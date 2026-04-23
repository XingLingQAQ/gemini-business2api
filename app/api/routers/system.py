from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from app.services import get_dashboard_stats_payload


@dataclass(frozen=True)
class SystemRouteDeps:
    admin_key: Callable[[], str]
    get_multi_account_mgr: Callable[[], Any]
    get_update_status: Callable[[], Any]
    logger: logging.Logger
    login_user: Callable[[Request], None]
    logout_user: Callable[[Request], None]
    require_login: Callable[..., Callable]
    stats_db: Any


def register_system_routes(app: FastAPI, deps: SystemRouteDeps) -> None:
    @app.get("/")
    async def serve_frontend_index():
        index_path = os.path.join("static", "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(404, "Not Found")

    @app.get("/logo.svg")
    async def serve_logo():
        logo_path = os.path.join("static", "logo.svg")
        if os.path.exists(logo_path):
            return FileResponse(logo_path)
        raise HTTPException(404, "Not Found")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.post("/login")
    async def admin_login_post(request: Request, admin_key: str = Form(...)):
        if admin_key == deps.admin_key():
            deps.login_user(request)
            deps.logger.info("[AUTH] Admin login success")
            return {"success": True}

        deps.logger.warning("[AUTH] Login failed - invalid key")
        raise HTTPException(401, "Invalid key")

    @app.post("/logout")
    @deps.require_login(redirect_to_login=False)
    async def admin_logout(request: Request):
        deps.logout_user(request)
        deps.logger.info("[AUTH] Admin logout")
        return {"success": True}

    @app.get("/admin/version-check")
    @deps.require_login()
    async def admin_version_check(request: Request):
        return deps.get_update_status()

    @app.get("/admin/stats-legacy")
    @deps.require_login()
    async def admin_stats(request: Request, time_range: str = "24h"):
        return await get_dashboard_stats_payload(
            deps.get_multi_account_mgr(),
            deps.stats_db,
            time_range,
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
