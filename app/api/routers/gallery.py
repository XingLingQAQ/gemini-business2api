from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request

from app.services import (
    cleanup_expired_gallery_payload,
    delete_gallery_file_payload,
    get_gallery_payload,
)


@dataclass(frozen=True)
class GalleryRouteDeps:
    get_config: Callable[[], Any]
    image_dir: str
    logger: logging.Logger
    require_login: Callable[..., Callable]
    scan_media_files: Callable[[], list[dict[str, Any]]]
    video_dir: str


def register_gallery_routes(app: FastAPI, deps: GalleryRouteDeps) -> None:
    @app.get("/admin/gallery")
    @deps.require_login()
    async def admin_get_gallery(request: Request):
        return await get_gallery_payload(
            deps.scan_media_files,
            deps.get_config().basic.image_expire_hours,
        )

    @app.delete("/admin/gallery/{filename:path}")
    @deps.require_login()
    async def admin_delete_gallery_file(request: Request, filename: str):
        try:
            return delete_gallery_file_payload(
                filename,
                deps.image_dir,
                deps.video_dir,
                deps.logger,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(404, "文件不存在") from exc
        except Exception as exc:
            raise HTTPException(500, f"删除失败: {exc}") from exc

    @app.post("/admin/gallery/cleanup")
    @deps.require_login()
    async def admin_cleanup_expired(request: Request):
        return cleanup_expired_gallery_payload(
            deps.get_config().basic.image_expire_hours,
            deps.image_dir,
            deps.video_dir,
            deps.logger,
        )
