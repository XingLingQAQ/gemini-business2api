from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from fastapi import FastAPI, Request

from app.services import get_dashboard_stats_payload


@dataclass(frozen=True)
class DashboardRouteDeps:
    get_multi_account_mgr: Callable[[], Any]
    require_login: Callable[..., Callable]
    stats_db: Any


def register_dashboard_routes(app: FastAPI, deps: DashboardRouteDeps) -> None:
    @app.get("/admin/stats")
    @deps.require_login()
    async def admin_stats(request: Request, time_range: str = "24h"):
        return await get_dashboard_stats_payload(
            deps.get_multi_account_mgr(),
            deps.stats_db,
            time_range,
        )
