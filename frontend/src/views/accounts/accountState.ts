import type { AccountStateCode, AdminAccount } from '@/types/api'

export type AccountStatusFilter = 'all' | AccountStateCode

type AccountStateMeta = {
  code: AccountStateCode
  label: string
  badgeClass: string
  rowClass: string
  canEnable: boolean
  canDisable: boolean
}

const ACCOUNT_STATE_META: Record<AccountStateCode, AccountStateMeta> = {
  active: {
    code: 'active',
    label: '正常',
    badgeClass: 'bg-emerald-500 text-white',
    rowClass: '',
    canEnable: false,
    canDisable: true,
  },
  manual_disabled: {
    code: 'manual_disabled',
    label: '手动禁用',
    badgeClass: 'bg-muted text-muted-foreground',
    rowClass: 'bg-muted/70',
    canEnable: true,
    canDisable: false,
  },
  access_restricted: {
    code: 'access_restricted',
    label: '403 禁用',
    badgeClass: 'bg-rose-600 text-white',
    rowClass: 'bg-muted/70',
    canEnable: true,
    canDisable: false,
  },
  expired: {
    code: 'expired',
    label: '已过期',
    badgeClass: 'bg-destructive/10 text-destructive',
    rowClass: 'bg-muted/70',
    canEnable: false,
    canDisable: false,
  },
  expiring_soon: {
    code: 'expiring_soon',
    label: '即将过期',
    badgeClass: 'bg-amber-200 text-amber-900',
    rowClass: '',
    canEnable: false,
    canDisable: true,
  },
  rate_limited: {
    code: 'rate_limited',
    label: '429 限流',
    badgeClass: 'bg-amber-200 text-amber-900',
    rowClass: '',
    canEnable: true,
    canDisable: true,
  },
  quota_limited: {
    code: 'quota_limited',
    label: '额度受限',
    badgeClass: 'bg-amber-200 text-amber-900',
    rowClass: '',
    canEnable: false,
    canDisable: true,
  },
  unavailable: {
    code: 'unavailable',
    label: '不可用',
    badgeClass: 'bg-muted text-muted-foreground',
    rowClass: 'bg-muted/70',
    canEnable: true,
    canDisable: true,
  },
  unknown: {
    code: 'unknown',
    label: '未知',
    badgeClass: 'bg-muted text-muted-foreground',
    rowClass: 'bg-muted/70',
    canEnable: false,
    canDisable: true,
  },
}

const includesStateText = (value: string | null | undefined, patterns: string[]) => {
  const normalized = String(value || '').trim().toLowerCase()
  return patterns.some((pattern) => normalized.includes(pattern))
}

const getFallbackStateCode = (account: AdminAccount): AccountStateCode => {
  if (account.cooldown_seconds > 0) {
    return 'rate_limited'
  }
  if (account.disabled) {
    if (includesStateText(account.disabled_reason, ['403', 'access restricted'])) {
      return 'access_restricted'
    }
    return 'manual_disabled'
  }
  if ((account.quota_status?.limited_count ?? 0) > 0) {
    return 'quota_limited'
  }
  if (
    typeof account.remaining_hours === 'number'
    && account.remaining_hours > 0
    && account.remaining_hours < 3
  ) {
    return 'expiring_soon'
  }
  if (includesStateText(account.status, ['expired', '已过期'])) return 'expired'
  if (includesStateText(account.status, ['expiring soon', '即将过期'])) return 'expiring_soon'
  if (account.is_available === false) return 'unavailable'
  return 'active'
}

export const resolveAccountStateCode = (account: AdminAccount): AccountStateCode =>
  account.state?.code ?? getFallbackStateCode(account)

export const getAccountStateMeta = (account: AdminAccount): AccountStateMeta => {
  const code = resolveAccountStateCode(account)
  const fallback = ACCOUNT_STATE_META[code] ?? ACCOUNT_STATE_META.unknown

  return {
    ...fallback,
    canEnable: account.state?.can_enable ?? fallback.canEnable,
    canDisable: account.state?.can_disable ?? fallback.canDisable,
  }
}

export const accountStatusOptions = [
  { label: '全部状态', value: 'all' },
  { label: ACCOUNT_STATE_META.active.label, value: 'active' },
  { label: ACCOUNT_STATE_META.expiring_soon.label, value: 'expiring_soon' },
  { label: ACCOUNT_STATE_META.expired.label, value: 'expired' },
  { label: ACCOUNT_STATE_META.manual_disabled.label, value: 'manual_disabled' },
  { label: ACCOUNT_STATE_META.access_restricted.label, value: 'access_restricted' },
  { label: ACCOUNT_STATE_META.rate_limited.label, value: 'rate_limited' },
  { label: ACCOUNT_STATE_META.quota_limited.label, value: 'quota_limited' },
] satisfies Array<{ label: string; value: AccountStatusFilter }>
