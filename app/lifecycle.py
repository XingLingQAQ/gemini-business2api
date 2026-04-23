from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, Request


@dataclass(frozen=True)
class LifecycleDeps:
    account_store: Any
    cleanup_expired_gallery: Callable[[int, str, str, logging.Logger], dict[str, Any]]
    data_dir: str
    get_config: Callable[[], Any]
    get_multi_account_mgr: Callable[[], Any]
    image_dir: str
    load_stats: Callable[[], Awaitable[dict[str, Any]]]
    logger: logging.Logger
    set_global_stats: Callable[[dict[str, Any]], None]
    stats_db: Any
    storage: Any
    uptime_tracker: Any
    video_dir: str


def register_lifecycle_hooks(app: FastAPI, deps: LifecycleDeps) -> None:
    @app.middleware("http")
    async def track_uptime_middleware(request: Request, call_next):
        path = request.url.path
        if _should_skip_uptime_tracking(path):
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            latency_ms = int((time.time() - start_time) * 1000)
            success = response.status_code < 400
            deps.uptime_tracker.record_request(
                "api_service",
                success,
                latency_ms,
                response.status_code,
            )
            return response
        except Exception:
            deps.uptime_tracker.record_request("api_service", False)
            raise

    @app.on_event("startup")
    async def startup_event():
        global_stats = await deps.load_stats()
        _ensure_stats_defaults(global_stats)
        deps.set_global_stats(global_stats)

        deps.uptime_tracker.configure_storage(os.path.join(deps.data_dir, "uptime.json"))
        deps.uptime_tracker.load_heartbeats()

        multi_account_mgr = deps.get_multi_account_mgr()
        for account_id, account_mgr in multi_account_mgr.accounts.items():
            account_mgr.conversation_count = global_stats["account_conversations"].get(account_id, 0)
            account_mgr.failure_count = global_stats["account_failures"].get(account_id, 0)

        deps.logger.info("[SYSTEM] Restored account conversation and failure counters")
        deps.logger.info(
            "[SYSTEM] Loaded stats: %s requests, %s visitors",
            global_stats["total_requests"],
            global_stats["total_visitors"],
        )

        asyncio.create_task(multi_account_mgr.start_background_cleanup())
        deps.logger.info("[SYSTEM] Started background cache cleanup task")

        asyncio.create_task(_cleanup_database_task(deps.stats_db, deps.logger))
        deps.logger.info("[SYSTEM] Started database cleanup task")

        if deps.storage.is_database_enabled():
            asyncio.create_task(
                _save_cooldown_states_task(
                    deps.account_store,
                    deps.get_multi_account_mgr,
                    deps.logger,
                )
            )
            deps.logger.info("[SYSTEM] Started cooldown persistence task")

        asyncio.create_task(
            _cleanup_expired_media_task(
                deps.cleanup_expired_gallery,
                deps.get_config,
                deps.image_dir,
                deps.video_dir,
                deps.logger,
            )
        )
        expire_hours = deps.get_config().basic.image_expire_hours
        if expire_hours < 0:
            deps.logger.info("[SYSTEM] Media expiration cleanup disabled")
        else:
            deps.logger.info(
                "[SYSTEM] Started media expiration cleanup task (expire_hours=%s)",
                expire_hours,
            )

    @app.on_event("shutdown")
    async def shutdown_event():
        if not deps.storage.is_database_enabled():
            return

        multi_account_mgr = deps.get_multi_account_mgr()
        try:
            success_count = await deps.account_store.save_all_cooldown_states(multi_account_mgr)
            deps.logger.info(
                "[SYSTEM] Saved cooldown states for %s/%s accounts on shutdown",
                success_count,
                len(multi_account_mgr.accounts),
            )
        except Exception as exc:
            deps.logger.error(
                "[SYSTEM] Failed to save cooldown states during shutdown: %s",
                exc,
            )


def _should_skip_uptime_tracking(path: str) -> bool:
    return (
        path.startswith("/images/")
        or path.startswith("/public/")
        or path.startswith("/favicon")
        or path.endswith("/v1/chat/completions")
    )


def _ensure_stats_defaults(global_stats: dict[str, Any]) -> None:
    global_stats.setdefault("total_visitors", 0)
    global_stats.setdefault("total_requests", 0)
    global_stats.setdefault("request_timestamps", [])
    global_stats.setdefault("model_request_timestamps", {})
    global_stats.setdefault("failure_timestamps", [])
    global_stats.setdefault("rate_limit_timestamps", [])
    global_stats.setdefault("recent_conversations", [])
    global_stats.setdefault("success_count", 0)
    global_stats.setdefault("failed_count", 0)
    global_stats.setdefault("visitor_ips", {})
    global_stats.setdefault("account_conversations", {})
    global_stats.setdefault("account_failures", {})


async def _save_cooldown_states_task(
    account_store: Any,
    get_multi_account_mgr: Callable[[], Any],
    logger: logging.Logger,
) -> None:
    while True:
        try:
            await asyncio.sleep(300)
            multi_account_mgr = get_multi_account_mgr()
            for attempt in range(3):
                try:
                    success_count = await account_store.save_all_cooldown_states(multi_account_mgr)
                    logger.debug(
                        "[COOLDOWN] Saved cooldown states for %s/%s accounts",
                        success_count,
                        len(multi_account_mgr.accounts),
                    )
                    break
                except Exception as retry_err:
                    error_message = str(retry_err)
                    is_busy_connection = (
                        "another operation" in error_message
                        or "ConnectionDoesNotExist" in error_message
                        or "connection was closed" in error_message
                    )
                    if is_busy_connection and attempt < 2:
                        logger.warning(
                            "[COOLDOWN] Database connection busy, retry %s/3",
                            attempt + 1,
                        )
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    raise
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("[COOLDOWN] Periodic save failed: %s", exc)


async def _cleanup_database_task(stats_db: Any, logger: logging.Logger) -> None:
    while True:
        try:
            await asyncio.sleep(24 * 3600)
            deleted_count = await stats_db.cleanup_old_data(days=30)
            logger.info(
                "[DATABASE] Cleaned %s expired rows (retention: 30 days)",
                deleted_count,
            )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("[DATABASE] Cleanup failed: %s", exc)


async def _cleanup_expired_media_task(
    cleanup_expired_gallery: Callable[[int, str, str, logging.Logger], dict[str, Any]],
    get_config: Callable[[], Any],
    image_dir: str,
    video_dir: str,
    logger: logging.Logger,
) -> None:
    while True:
        try:
            await asyncio.sleep(30 * 60)

            expire_hours = get_config().basic.image_expire_hours
            if expire_hours < 0:
                continue

            cleanup_expired_gallery(
                expire_hours,
                image_dir,
                video_dir,
                logger,
            )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("[GALLERY] Expired media cleanup failed: %s", exc)
