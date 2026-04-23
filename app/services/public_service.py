from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Awaitable, Callable


def get_public_stats_payload(
    global_stats: dict[str, Any],
    current_time: float | None = None,
) -> dict[str, Any]:
    now = current_time if current_time is not None else time.time()
    recent_requests = [
        ts for ts in global_stats["request_timestamps"]
        if now - ts < 3600
    ]
    recent_minute = [ts for ts in recent_requests if now - ts < 60]
    requests_per_minute = len(recent_minute)

    if requests_per_minute < 10:
        load_status = "low"
        load_color = "#10b981"
    elif requests_per_minute < 30:
        load_status = "medium"
        load_color = "#f59e0b"
    else:
        load_status = "high"
        load_color = "#ef4444"

    return {
        "total_visitors": global_stats["total_visitors"],
        "total_requests": global_stats["total_requests"],
        "requests_per_minute": requests_per_minute,
        "load_status": load_status,
        "load_color": load_color,
    }


def get_public_display_payload(public_display: Any) -> dict[str, Any]:
    return {
        "logo_url": public_display.logo_url,
        "chat_url": public_display.chat_url,
    }


async def get_public_logs_payload(
    request: Any,
    global_stats: dict[str, Any],
    get_sanitized_logs: Callable[[int], list[dict[str, Any]]],
    save_stats: Callable[[dict[str, Any]], Awaitable[None]],
    limit: int = 100,
) -> dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    if "visitor_ips" not in global_stats:
        global_stats["visitor_ips"] = {}
    global_stats["visitor_ips"] = {
        ip: timestamp
        for ip, timestamp in global_stats["visitor_ips"].items()
        if current_time - timestamp <= 86400
    }
    if client_ip not in global_stats["visitor_ips"]:
        global_stats["visitor_ips"][client_ip] = current_time
        global_stats["total_visitors"] = global_stats.get("total_visitors", 0) + 1

    global_stats.setdefault("recent_conversations", [])
    await save_stats(global_stats)
    stored_logs = list(global_stats.get("recent_conversations", []))

    sanitized_logs = get_sanitized_logs(limit=min(limit, 1000))
    log_map = {log.get("request_id"): log for log in sanitized_logs}
    for log in stored_logs:
        request_id = log.get("request_id")
        if request_id and request_id not in log_map:
            log_map[request_id] = log

    def get_log_ts(item: dict[str, Any]) -> float:
        if "start_ts" in item:
            return float(item["start_ts"])
        try:
            start_time = item.get("start_time", "")
            return datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()
        except Exception:
            return 0.0

    merged_logs = sorted(log_map.values(), key=get_log_ts, reverse=True)[: min(limit, 1000)]
    output_logs = []
    for log in merged_logs:
        if "start_ts" in log:
            log = dict(log)
            log.pop("start_ts", None)
        output_logs.append(log)

    return {"total": len(output_logs), "logs": output_logs}
