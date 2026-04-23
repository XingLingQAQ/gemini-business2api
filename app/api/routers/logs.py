from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request

from app.services import clear_admin_logs, get_admin_logs_payload


@dataclass(frozen=True)
class LogRouteDeps:
    get_log_buffer: Callable[[], Any]
    log_lock: Any
    logger: logging.Logger
    require_login: Callable[..., Callable]


def register_log_routes(app: FastAPI, deps: LogRouteDeps) -> None:
    @app.get("/admin/log")
    @deps.require_login()
    async def admin_get_logs(
        request: Request,
        limit: int = 300,
        level: str | None = None,
        search: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ):
        log_buffer = deps.get_log_buffer()
        with deps.log_lock:
            return get_admin_logs_payload(
                log_buffer,
                limit=limit,
                level=level,
                search=search,
                start_time=start_time,
                end_time=end_time,
            )

    @app.delete("/admin/log")
    @deps.require_login()
    async def admin_clear_logs(request: Request, confirm: str | None = None):
        if confirm != "yes":
            raise HTTPException(400, "需要 confirm=yes 参数确认清空操作")

        log_buffer = deps.get_log_buffer()
        with deps.log_lock:
            return clear_admin_logs(log_buffer, deps.logger)
