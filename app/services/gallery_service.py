from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Callable


def _validate_gallery_filename(filename: str) -> str:
    safe_name = os.path.basename(filename)
    if safe_name != filename or ".." in filename:
        raise ValueError("非法文件名")
    return safe_name


async def get_gallery_payload(
    scan_media_files: Callable[[], list[dict[str, Any]]],
    expire_hours: int,
) -> dict[str, Any]:
    files = await asyncio.to_thread(scan_media_files)
    total_size = sum(file_info["size"] for file_info in files)
    return {
        "files": files,
        "total": len(files),
        "total_size": total_size,
        "expire_hours": expire_hours,
    }


def delete_gallery_file_payload(
    filename: str,
    image_dir: str,
    video_dir: str,
    logger: logging.Logger,
) -> dict[str, Any]:
    safe_name = _validate_gallery_filename(filename)

    for directory in (image_dir, video_dir):
        filepath = os.path.join(directory, safe_name)
        if os.path.isfile(filepath):
            os.remove(filepath)
            logger.info("[GALLERY] Deleted file: %s", safe_name)
            return {"success": True, "message": f"Deleted {safe_name}"}

    raise FileNotFoundError(safe_name)


def cleanup_expired_gallery_payload(
    expire_hours: int,
    image_dir: str,
    video_dir: str,
    logger: logging.Logger,
) -> dict[str, Any]:
    if expire_hours < 0:
        return {
            "success": True,
            "deleted": 0,
            "deleted_images": 0,
            "deleted_videos": 0,
            "message": "当前设置为永不删除",
        }

    now = time.time()
    deleted_images = 0
    deleted_videos = 0
    video_exts = (".mp4", ".webm", ".mov")

    for directory, is_video_dir in ((image_dir, False), (video_dir, True)):
        if not os.path.isdir(directory):
            continue

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                age_hours = (now - os.path.getmtime(filepath)) / 3600
                if age_hours > expire_hours:
                    os.remove(filepath)
                    ext = os.path.splitext(filename)[1].lower()
                    if is_video_dir or ext in video_exts:
                        deleted_videos += 1
                    else:
                        deleted_images += 1
            except Exception:
                continue

    deleted_count = deleted_images + deleted_videos
    if deleted_count > 0:
        logger.info(
            "[GALLERY] Cleaned %s expired media files (images: %s, videos: %s)",
            deleted_count,
            deleted_images,
            deleted_videos,
        )

    return {
        "success": True,
        "deleted": deleted_count,
        "deleted_images": deleted_images,
        "deleted_videos": deleted_videos,
        "message": (
            f"已清理 {deleted_count} 个过期文件"
            if deleted_count > 0
            else "没有过期文件需要清理"
        ),
    }
