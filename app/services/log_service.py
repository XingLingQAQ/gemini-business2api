from __future__ import annotations

import logging
from typing import Any


def get_admin_logs_payload(
    log_buffer: Any,
    limit: int = 300,
    level: str | None = None,
    search: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    logs = list(log_buffer)

    stats_by_level: dict[str, int] = {}
    error_logs = []
    chat_count = 0
    for log in logs:
        level_name = log.get("level", "INFO")
        stats_by_level[level_name] = stats_by_level.get(level_name, 0) + 1
        if level_name in ["ERROR", "CRITICAL"]:
            error_logs.append(log)
        if "收到请求" in log.get("message", ""):
            chat_count += 1

    normalized_level = level.upper() if level else None
    if normalized_level:
        logs = [log for log in logs if log["level"] == normalized_level]
    if search:
        logs = [log for log in logs if search.lower() in log["message"].lower()]
    if start_time:
        logs = [log for log in logs if log["time"] >= start_time]
    if end_time:
        logs = [log for log in logs if log["time"] <= end_time]

    normalized_limit = min(limit, log_buffer.maxlen)
    filtered_logs = logs[-normalized_limit:]

    return {
        "total": len(filtered_logs),
        "limit": normalized_limit,
        "filters": {
            "level": normalized_level,
            "search": search,
            "start_time": start_time,
            "end_time": end_time,
        },
        "logs": filtered_logs,
        "stats": {
            "memory": {
                "total": len(log_buffer),
                "by_level": stats_by_level,
                "capacity": log_buffer.maxlen,
            },
            "errors": {"count": len(error_logs), "recent": error_logs[-10:]},
            "chat_count": chat_count,
        },
    }


def clear_admin_logs(log_buffer: Any, logger: logging.Logger) -> dict[str, Any]:
    cleared_count = len(log_buffer)
    log_buffer.clear()
    logger.info("[LOG] Memory logs cleared")
    return {
        "status": "success",
        "message": "已清空内存日志",
        "cleared_count": cleared_count,
    }
