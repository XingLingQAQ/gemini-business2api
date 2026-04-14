<template>
  <div class="space-y-8">
    <section v-if="isLoading && !localSettings" class="ui-panel text-sm text-muted-foreground">
      正在加载设置...
    </section>

    <section v-else class="ui-panel">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="ui-section-title">系统设置</p>
          <p class="mt-1 text-xs text-muted-foreground">
            主分支只保留 2api 运行参数，注册机相关配置已从当前页面移除。
          </p>
        </div>
        <Button
          size="xs"
          variant="primary"
          root-class="min-w-14 justify-center"
          :disabled="isSaving || !localSettings"
          @click="handleSave"
        >
          保存设置
        </Button>
      </div>

      <div
        v-if="errorMessage"
        class="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
      >
        {{ errorMessage }}
      </div>

      <div v-if="localSettings" class="mt-6 grid gap-4 lg:grid-cols-3">
        <div class="space-y-4">
          <div class="ui-card">
            <p class="ui-section-kicker">基础</p>
            <div class="mt-4 space-y-3">
              <label class="block text-xs text-muted-foreground">API 密钥</label>
              <Input
                v-model="localSettings.basic.api_key"
                type="text"
                block
                placeholder="可选，多个密钥用逗号分隔"
              />

              <label class="block text-xs text-muted-foreground">基础地址</label>
              <Input
                v-model="localSettings.basic.base_url"
                type="text"
                block
                placeholder="留空自动检测"
              />

              <label class="block text-xs text-muted-foreground">聊天代理</label>
              <Input
                v-model="localSettings.basic.proxy_for_chat"
                type="text"
                block
                placeholder="http://127.0.0.1:7890"
              />

              <label class="block text-xs text-muted-foreground">图片链接有效期（小时）</label>
              <Input
                :model-value="imageExpireHoursInput"
                type="number"
                block
                @update:model-value="imageExpireHoursInput = $event"
              />
            </div>
          </div>

          <div class="ui-card">
            <p class="ui-section-kicker">重试与缓存</p>
            <div class="mt-4 grid grid-cols-1 gap-3">
              <label class="block text-xs text-muted-foreground">账号切换次数</label>
              <Input
                :model-value="maxAccountSwitchTriesInput"
                type="number"
                block
                @update:model-value="maxAccountSwitchTriesInput = $event"
              />

              <label class="block text-xs text-muted-foreground">对话冷却（小时）</label>
              <Input
                :model-value="textCooldownHoursInput"
                type="number"
                block
                @update:model-value="textCooldownHoursInput = $event"
              />

              <label class="block text-xs text-muted-foreground">绘图冷却（小时）</label>
              <Input
                :model-value="imagesCooldownHoursInput"
                type="number"
                block
                @update:model-value="imagesCooldownHoursInput = $event"
              />

              <label class="block text-xs text-muted-foreground">视频冷却（小时）</label>
              <Input
                :model-value="videosCooldownHoursInput"
                type="number"
                block
                @update:model-value="videosCooldownHoursInput = $event"
              />

              <label class="block text-xs text-muted-foreground">会话缓存 TTL（秒）</label>
              <Input
                :model-value="sessionCacheTtlInput"
                type="number"
                block
                @update:model-value="sessionCacheTtlInput = $event"
              />

              <label class="block text-xs text-muted-foreground">自动刷新账号列表（秒，0=关闭）</label>
              <Input
                :model-value="autoRefreshAccountsSecondsInput"
                type="number"
                block
                @update:model-value="autoRefreshAccountsSecondsInput = $event"
              />
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="ui-card">
            <p class="ui-section-kicker">图像能力</p>
            <div class="mt-4 space-y-3">
              <Checkbox v-model="localSettings.image_generation.enabled">
                启用图像生成
              </Checkbox>

              <label class="block text-xs text-muted-foreground">输出格式</label>
              <SelectMenu
                v-model="localSettings.image_generation.output_format"
                :options="imageOutputOptions"
                placement="up"
                class="w-full"
              />

              <label class="block text-xs text-muted-foreground">支持模型</label>
              <SelectMenu
                v-model="localSettings.image_generation.supported_models"
                :options="imageModelOptions"
                multiple
                placement="up"
                placeholder="选择模型"
                class="w-full"
              />
            </div>
          </div>

          <div class="ui-card">
            <p class="ui-section-kicker">视频输出</p>
            <div class="mt-4 space-y-3">
              <label class="block text-xs text-muted-foreground">输出格式</label>
              <SelectMenu
                v-model="localSettings.video_generation.output_format"
                :options="videoOutputOptions"
                placement="up"
                class="w-full"
              />
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="ui-card">
            <p class="ui-section-kicker">每日配额</p>
            <div class="mt-4 space-y-3">
              <Checkbox v-model="localSettings.quota_limits.enabled">
                启用每日配额统计
              </Checkbox>

              <label class="block text-xs text-muted-foreground">对话每日上限</label>
              <Input
                :model-value="quotaTextDailyLimitInput"
                type="number"
                block
                @update:model-value="quotaTextDailyLimitInput = $event"
              />

              <label class="block text-xs text-muted-foreground">绘图每日上限</label>
              <Input
                :model-value="quotaImagesDailyLimitInput"
                type="number"
                block
                @update:model-value="quotaImagesDailyLimitInput = $event"
              />

              <label class="block text-xs text-muted-foreground">视频每日上限</label>
              <Input
                :model-value="quotaVideosDailyLimitInput"
                type="number"
                block
                @update:model-value="quotaVideosDailyLimitInput = $event"
              />
            </div>
          </div>

          <div class="ui-card">
            <p class="ui-section-kicker">公开展示</p>
            <div class="mt-4 space-y-3">
              <label class="block text-xs text-muted-foreground">Logo 地址</label>
              <Input
                v-model="localSettings.public_display.logo_url"
                type="text"
                block
                placeholder="https://example.com/logo.svg"
              />

              <label class="block text-xs text-muted-foreground">聊天入口</label>
              <Input
                v-model="localSettings.public_display.chat_url"
                type="text"
                block
                placeholder="https://example.com/chat"
              />

              <label class="block text-xs text-muted-foreground">会话有效时长（小时）</label>
              <Input
                :model-value="sessionExpireHoursInput"
                type="number"
                block
                @update:model-value="sessionExpireHoursInput = $event"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Button, Checkbox, Input, SelectMenu } from 'nanocat-ui'
import { useToast } from '@/composables/useToast'
import { useSettingsStore } from '@/stores/settings'
import type { Settings } from '@/types/api'

const settingsStore = useSettingsStore()
const { settings, isLoading } = storeToRefs(settingsStore)
const toast = useToast()

const localSettings = ref<Settings | null>(null)
const isSaving = ref(false)
const errorMessage = ref('')

const DEFAULT_COOLDOWN_HOURS = {
  text: 2,
  images: 4,
  videos: 4,
} as const

const imageOutputOptions = [
  { label: 'Base64 编码', value: 'base64' },
  { label: 'URL 链接', value: 'url' },
]

const videoOutputOptions = [
  { label: 'HTML 视频标签', value: 'html' },
  { label: 'URL 链接', value: 'url' },
  { label: 'Markdown 格式', value: 'markdown' },
]

const clampInteger = (
  value: number,
  min: number,
  max: number = Number.MAX_SAFE_INTEGER,
) => Math.max(min, Math.min(max, Math.round(value)))

const toCooldownHours = (seconds: number | undefined, fallbackHours: number) => {
  if (!seconds) return fallbackHours
  return Math.max(1, Math.round(seconds / 3600))
}

const createNumberInputBinding = (
  getter: () => number | undefined,
  setter: (value: number) => void,
  normalize: (value: number) => number = (value) => value,
) => computed({
  get: () => {
    const value = getter()
    return Number.isFinite(value) ? String(value) : ''
  },
  set: (raw: string | number) => {
    const parsed = typeof raw === 'number' ? raw : Number(String(raw).trim())
    if (Number.isFinite(parsed)) {
      setter(normalize(parsed))
    }
  },
})

const createCooldownHoursBinding = (
  key: 'text_rate_limit_cooldown_seconds' | 'images_rate_limit_cooldown_seconds' | 'videos_rate_limit_cooldown_seconds',
  fallbackHours: number,
  maxHours = 24,
) => createNumberInputBinding(
  () => toCooldownHours(localSettings.value?.retry?.[key], fallbackHours),
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry[key] = value * 3600
    }
  },
  (value) => clampInteger(value, 1, maxHours),
)

const maxAccountSwitchTriesInput = createNumberInputBinding(
  () => localSettings.value?.retry?.max_account_switch_tries,
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry.max_account_switch_tries = value
    }
  },
  (value) => clampInteger(value, 1, 20),
)

const imageExpireHoursInput = createNumberInputBinding(
  () => localSettings.value?.basic?.image_expire_hours,
  (value) => {
    if (localSettings.value?.basic) {
      localSettings.value.basic.image_expire_hours = value
    }
  },
  (value) => clampInteger(value, 1, 720),
)

const textCooldownHoursInput = createCooldownHoursBinding(
  'text_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.text,
)

const imagesCooldownHoursInput = createCooldownHoursBinding(
  'images_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.images,
)

const videosCooldownHoursInput = createCooldownHoursBinding(
  'videos_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.videos,
)

const sessionCacheTtlInput = createNumberInputBinding(
  () => localSettings.value?.retry?.session_cache_ttl_seconds,
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry.session_cache_ttl_seconds = value
    }
  },
  (value) => clampInteger(value, 0, 86400),
)

const autoRefreshAccountsSecondsInput = createNumberInputBinding(
  () => localSettings.value?.retry?.auto_refresh_accounts_seconds,
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry.auto_refresh_accounts_seconds = value
    }
  },
  (value) => clampInteger(value, 0, 3600),
)

const quotaTextDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.text_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.text_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const quotaImagesDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.images_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.images_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const quotaVideosDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.videos_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.videos_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const sessionExpireHoursInput = createNumberInputBinding(
  () => localSettings.value?.session?.expire_hours,
  (value) => {
    if (localSettings.value?.session) {
      localSettings.value.session.expire_hours = value
    }
  },
  (value) => clampInteger(value, 1, 720),
)

const imageModelOptions = computed(() => {
  const options = [
    { label: 'Gemini Auto', value: 'gemini-auto' },
    { label: 'Gemini 2.5 Flash', value: 'gemini-2.5-flash' },
    { label: 'Gemini 2.5 Pro', value: 'gemini-2.5-pro' },
    { label: 'Gemini 3 Flash Preview', value: 'gemini-3-flash-preview' },
    { label: 'Gemini 3 Pro Preview', value: 'gemini-3-pro-preview' },
    { label: 'Gemini 3.1 Pro Preview', value: 'gemini-3.1-pro-preview' },
  ]

  const selected = localSettings.value?.image_generation.supported_models || []
  for (const value of selected) {
    if (!options.some((option) => option.value === value)) {
      options.push({ label: value, value })
    }
  }

  return options
})

watch(settings, (value) => {
  if (!value) return

  const next = JSON.parse(JSON.stringify(value)) as Settings
  next.basic = next.basic || {}
  next.basic.api_key = typeof next.basic.api_key === 'string' ? next.basic.api_key : ''
  next.basic.base_url = typeof next.basic.base_url === 'string' ? next.basic.base_url : ''
  next.basic.proxy_for_chat = typeof next.basic.proxy_for_chat === 'string' ? next.basic.proxy_for_chat : ''
  next.basic.image_expire_hours = Number.isFinite(next.basic.image_expire_hours)
    ? next.basic.image_expire_hours
    : 24

  next.retry = next.retry || {
    max_account_switch_tries: 3,
    text_rate_limit_cooldown_seconds: 7200,
    images_rate_limit_cooldown_seconds: 14400,
    videos_rate_limit_cooldown_seconds: 14400,
    session_cache_ttl_seconds: 0,
    auto_refresh_accounts_seconds: 60,
  }
  next.retry.max_account_switch_tries = Number.isFinite(next.retry.max_account_switch_tries)
    ? next.retry.max_account_switch_tries
    : 3
  next.retry.text_rate_limit_cooldown_seconds = Number.isFinite(next.retry.text_rate_limit_cooldown_seconds)
    ? next.retry.text_rate_limit_cooldown_seconds
    : 7200
  next.retry.images_rate_limit_cooldown_seconds = Number.isFinite(next.retry.images_rate_limit_cooldown_seconds)
    ? next.retry.images_rate_limit_cooldown_seconds
    : 14400
  next.retry.videos_rate_limit_cooldown_seconds = Number.isFinite(next.retry.videos_rate_limit_cooldown_seconds)
    ? next.retry.videos_rate_limit_cooldown_seconds
    : 14400
  next.retry.session_cache_ttl_seconds = Number.isFinite(next.retry.session_cache_ttl_seconds)
    ? next.retry.session_cache_ttl_seconds
    : 0
  next.retry.auto_refresh_accounts_seconds = Number.isFinite(next.retry.auto_refresh_accounts_seconds)
    ? next.retry.auto_refresh_accounts_seconds
    : 60

  next.image_generation = next.image_generation || {
    enabled: false,
    supported_models: [],
    output_format: 'base64',
  }
  next.image_generation.enabled = next.image_generation.enabled ?? false
  next.image_generation.supported_models = Array.isArray(next.image_generation.supported_models)
    ? next.image_generation.supported_models
    : []
  next.image_generation.output_format =
    next.image_generation.output_format === 'url' ? 'url' : 'base64'

  next.video_generation = next.video_generation || { output_format: 'html' }
  next.video_generation.output_format = next.video_generation.output_format === 'url'
    ? 'url'
    : next.video_generation.output_format === 'markdown'
      ? 'markdown'
      : 'html'

  next.quota_limits = next.quota_limits || {
    enabled: true,
    text_daily_limit: 120,
    images_daily_limit: 2,
    videos_daily_limit: 1,
  }
  next.quota_limits.enabled = next.quota_limits.enabled ?? true
  next.quota_limits.text_daily_limit = Number.isFinite(next.quota_limits.text_daily_limit)
    ? next.quota_limits.text_daily_limit
    : 120
  next.quota_limits.images_daily_limit = Number.isFinite(next.quota_limits.images_daily_limit)
    ? next.quota_limits.images_daily_limit
    : 2
  next.quota_limits.videos_daily_limit = Number.isFinite(next.quota_limits.videos_daily_limit)
    ? next.quota_limits.videos_daily_limit
    : 1

  next.public_display = next.public_display || {}
  next.public_display.logo_url = typeof next.public_display.logo_url === 'string'
    ? next.public_display.logo_url
    : ''
  next.public_display.chat_url = typeof next.public_display.chat_url === 'string'
    ? next.public_display.chat_url
    : ''

  next.session = next.session || { expire_hours: 24 }
  next.session.expire_hours = Number.isFinite(next.session.expire_hours)
    ? next.session.expire_hours
    : 24

  localSettings.value = next
}, { immediate: true })

onMounted(async () => {
  if (!settings.value) {
    await settingsStore.loadSettings()
  }
})

const handleSave = async () => {
  if (!localSettings.value) return

  errorMessage.value = ''
  isSaving.value = true

  try {
    await settingsStore.updateSettings(localSettings.value)
    toast.success('设置保存成功')
  } catch (error: any) {
    errorMessage.value = error.message || '保存失败'
    toast.error(error.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}
</script>
