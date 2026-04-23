from __future__ import annotations

from typing import Any


def _summarize_account_states(multi_account_mgr: Any) -> dict[str, int]:
    active_accounts = 0
    failed_accounts = 0
    rate_limited_accounts = 0
    idle_accounts = 0

    for account_manager in multi_account_mgr.accounts.values():
        account_config = account_manager.config
        cooldown_seconds, _cooldown_reason = account_manager.get_cooldown_info()

        is_expired = account_config.is_expired()
        is_manual_disabled = account_config.disabled
        is_rate_limited = cooldown_seconds > 0
        is_failed = is_expired
        is_active = (not is_failed) and (not is_manual_disabled) and (not is_rate_limited)

        if is_rate_limited:
            rate_limited_accounts += 1
        elif is_failed:
            failed_accounts += 1
        elif is_active:
            active_accounts += 1
        else:
            idle_accounts += 1

    return {
        "total_accounts": len(multi_account_mgr.accounts),
        "active_accounts": active_accounts,
        "failed_accounts": failed_accounts,
        "rate_limited_accounts": rate_limited_accounts,
        "idle_accounts": idle_accounts,
    }


async def get_dashboard_stats_payload(
    multi_account_mgr: Any,
    stats_db: Any,
    time_range: str,
) -> dict[str, Any]:
    summary = _summarize_account_states(multi_account_mgr)
    trend_data = await stats_db.get_stats_by_time_range(time_range)
    success_count, failed_count = await stats_db.get_total_counts()

    return {
        **summary,
        "success_count": success_count,
        "failed_count": failed_count,
        "trend": trend_data,
    }
