from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, Request

from app.services import (
    get_public_display_payload,
    get_public_logs_payload,
    get_public_stats_payload,
)


@dataclass(frozen=True)
class PublicRouteDeps:
    get_config: Callable[[], Any]
    get_global_stats: Callable[[], dict[str, Any]]
    get_sanitized_logs: Callable[[int], list[dict[str, Any]]]
    get_version_info: Callable[[], Any]
    logger: logging.Logger
    save_stats: Callable[[dict[str, Any]], Awaitable[None]]
    stats_lock: Any
    uptime_tracker: Any


def register_public_routes(app: FastAPI, deps: PublicRouteDeps) -> None:
    @app.get("/public/version")
    async def public_version():
        return deps.get_version_info()

    @app.get("/public/uptime")
    async def get_public_uptime(days: int = 90):
        if days < 1 or days > 90:
            days = 90
        return await deps.uptime_tracker.get_uptime_summary(days)

    @app.get("/public/stats")
    async def get_public_stats():
        async with deps.stats_lock:
            return get_public_stats_payload(deps.get_global_stats())

    @app.get("/public/display")
    async def get_public_display():
        return get_public_display_payload(deps.get_config().public_display)

    @app.get("/public/log")
    async def get_public_logs(request: Request, limit: int = 100):
        try:
            async with deps.stats_lock:
                return await get_public_logs_payload(
                    request,
                    deps.get_global_stats(),
                    deps.get_sanitized_logs,
                    deps.save_stats,
                    limit=limit,
                )
        except Exception as exc:
            deps.logger.error(f"[LOG] Failed to load public logs: {exc}")
            return {"total": 0, "logs": [], "error": str(exc)}
