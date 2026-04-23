<template>
  <div class="space-y-8">
    <section v-if="isLoading && !localSettings" class="ui-panel text-sm text-muted-foreground">
      正在加载设置...
    </section>

    <section v-else class="ui-panel">
      <PanelPageHeader
        title="配置面板"
        description="保留原来的邮箱与注册配置方式，刷新服务需要的参数也继续在这里统一维护。"
      >
        <template #actions>
          <Button
            size="xs"
            variant="primary"
            root-class="min-w-14 justify-center"
            :disabled="isSaving || !localSettings"
            @click="handleSave"
          >
            {{ isSaving ? '保存中...' : '保存设置' }}
          </Button>
        </template>
      </PanelPageHeader>

      <div
        v-if="errorMessage"
        class="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
      >
        {{ errorMessage }}
      </div>

      <div v-if="localSettings" class="mt-6 space-y-8">
        <div class="grid gap-4 lg:grid-cols-3">
          <div class="space-y-4">
            <div class="ui-card">
              <CardSectionHeader title="基础" />
              <div class="mt-4 space-y-3">
                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <label class="block">API 密钥</label>
                  <HelpTip text="支持多个密钥，用逗号分隔。例如：key1,key2,key3" />
                </div>
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
                  placeholder="自动检测或手动填写"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>聊天代理</span>
                  <HelpTip text="用于 JWT、会话和消息请求；留空表示直连。" />
                </div>
                <Input
                  v-model="localSettings.basic.proxy_for_chat"
                  type="text"
                  block
                  placeholder="http://127.0.0.1:7890"
                />
              </div>
            </div>

            <div class="ui-card">
              <CardSectionHeader title="重试" />
              <div class="mt-4 grid grid-cols-2 gap-3">
                <label class="col-span-2 text-xs text-muted-foreground">账户切换次数</label>
                <Input
                  v-model="maxAccountSwitchTriesInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">对话冷却（小时）</label>
                <Input
                  v-model="textCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">绘图冷却（小时）</label>
                <Input
                  v-model="imagesCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">视频冷却（小时）</label>
                <Input
                  v-model="videosCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">会话缓存秒数</label>
                <Input
                  v-model="sessionCacheTtlInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="ui-card">
              <CardSectionHeader
                title="邮箱与注册"
                help-text="这里继续保留原来的邮箱下拉和按服务商分段配置，便于独立刷新服务直接复用。"
              />

              <div class="mt-4 space-y-3">
                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>账户操作代理</span>
                  <HelpTip text="用于注册、登录、刷新流程；临时邮箱开启代理时也会走这个地址。" />
                </div>
                <Input
                  v-model="localSettings.refresh_settings.proxy_for_auth"
                  type="text"
                  block
                  placeholder="http://127.0.0.1:7890"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>浏览器模式</span>
                  <HelpTip text="normal 为正常窗口；silent 为静默窗口；headless 为无头。" />
                </div>
                <SelectMenu
                  v-model="localSettings.refresh_settings.browser_mode"
                  :options="browserModeOptions"
                  class="w-full"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>临时邮箱服务</span>
                  <HelpTip text="恢复为下拉选择，不同服务商展示各自配置项。" />
                </div>
                <SelectMenu
                  v-model="localSettings.refresh_settings.temp_mail_provider"
                  :options="tempMailProviderOptions"
                  class="w-full"
                />

                <Checkbox v-model="localSettings.refresh_settings.mail_proxy_enabled">
                  启用邮箱代理（使用账户操作代理）
                </Checkbox>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'duckmail'">
                  <Checkbox v-model="localSettings.refresh_settings.duckmail.verify_ssl">
                    DuckMail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">DuckMail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.duckmail.base_url"
                    type="text"
                    block
                    placeholder="https://api.duckmail.sbs"
                  />

                  <label class="block text-xs text-muted-foreground">DuckMail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.duckmail.api_key"
                    type="text"
                    block
                    placeholder="dk_xxx"
                  />

                  <label class="block text-xs text-muted-foreground">DuckMail 域名（推荐）</label>
                  <Input
                    v-model="localSettings.refresh_settings.register_domain"
                    type="text"
                    block
                    placeholder="留空则自动选择"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'moemail'">
                  <label class="block text-xs text-muted-foreground">Moemail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.base_url"
                    type="text"
                    block
                    placeholder="https://moemail.nanohajimi.mom"
                  />

                  <label class="block text-xs text-muted-foreground">Moemail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.api_key"
                    type="text"
                    block
                    placeholder="X-API-Key"
                  />

                  <label class="block text-xs text-muted-foreground">Moemail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'freemail'">
                  <Checkbox v-model="localSettings.refresh_settings.freemail.verify_ssl">
                    Freemail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">Freemail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.base_url"
                    type="text"
                    block
                    placeholder="http://your-freemail-server.com"
                  />

                  <label class="block text-xs text-muted-foreground">Freemail JWT Token</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.jwt_token"
                    type="text"
                    block
                    placeholder="eyJ..."
                  />

                  <label class="block text-xs text-muted-foreground">Freemail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'gptmail'">
                  <Checkbox v-model="localSettings.refresh_settings.gptmail.verify_ssl">
                    GPTMail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">GPTMail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.base_url"
                    type="text"
                    block
                    placeholder="https://mail.chatgpt.org.uk"
                  />

                  <label class="block text-xs text-muted-foreground">GPTMail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.api_key"
                    type="text"
                    block
                    placeholder="X-API-Key"
                  />

                  <label class="block text-xs text-muted-foreground">GPTMail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'cfmail'">
                  <Checkbox v-model="localSettings.refresh_settings.cfmail.verify_ssl">
                    Cloudflare Mail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">Cloudflare Mail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.base_url"
                    type="text"
                    block
                    placeholder="https://your-cfmail-instance.example.com"
                  />

                  <label class="block text-xs text-muted-foreground">访问密码（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.api_key"
                    type="text"
                    block
                    placeholder="留空则不使用密码"
                  />

                  <label class="block text-xs text-muted-foreground">邮箱域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <label class="block text-xs text-muted-foreground">默认注册数量</label>
                <Input
                  v-model="registerDefaultCountInput"
                  type="number"
                  block
                />
              </div>
            </div>

            <div class="ui-card">
              <CardSectionHeader title="刷新调度" />
              <div class="mt-4 space-y-3">
                <Checkbox v-model="localSettings.refresh_settings.auto_register_enabled">
                  启用自动补量
                </Checkbox>

                <Checkbox v-model="localSettings.refresh_settings.delete_expired_accounts">
                  自动删除过期账号
                </Checkbox>

                <label class="block text-xs text-muted-foreground">最低账号数量</label>
                <Input
                  v-model="minAccountCountInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">刷新窗口（小时）</label>
                <Input
                  v-model="refreshWindowHoursInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">账号列表重载间隔（秒）</label>
                <Input
                  v-model="autoRefreshAccountsSecondsInput"
                  type="number"
                  block
                />

                <Checkbox v-model="localSettings.refresh_settings.scheduled_refresh_enabled">
                  启用定时刷新
                </Checkbox>

                <label class="block text-xs text-muted-foreground">定时轮询间隔（分钟）</label>
                <Input
                  v-model="scheduledRefreshIntervalMinutesInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">定时表达式</label>
                <Input
                  v-model="localSettings.refresh_settings.scheduled_refresh_cron"
                  type="text"
                  block
                  placeholder="08:00,20:00 或 */120"
                />

                <label class="block text-xs text-muted-foreground">验证码重发次数</label>
                <Input
                  v-model="verificationCodeResendCountInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">单批刷新数量</label>
                <Input
                  v-model="refreshBatchSizeInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">批次间隔（分钟）</label>
                <Input
                  v-model="refreshBatchIntervalMinutesInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">刷新冷却（小时）</label>
                <Input
                  v-model="refreshCooldownHoursInput"
                  type="number"
                  block
                />
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="ui-card">
              <CardSectionHeader
                title="图像生成"
                help-text="不建议默认开启图像生成，若要稳定出图更推荐专门的图像模型。"
              />
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
                  placeholder="选择模型"
                  placement="up"
                  multiple
                  class="w-full"
                />
              </div>
            </div>

            <div class="ui-card">
              <CardSectionHeader title="视频生成" />
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

            <div class="ui-card">
              <CardSectionHeader
                title="每日配额"
                help-text="达到上限后会自动切换账号。0 表示不限制该类型。"
              />
              <div class="mt-4 space-y-3">
                <Checkbox v-model="localSettings.quota_limits.enabled">
                  启用主动配额计数
                </Checkbox>

                <label class="block text-xs text-muted-foreground">对话每日上限</label>
                <Input
                  v-model="quotaTextDailyLimitInput"
                  type="number"
                  block
                  placeholder="120"
                />

                <label class="block text-xs text-muted-foreground">绘图每日上限</label>
                <Input
                  v-model="quotaImagesDailyLimitInput"
                  type="number"
                  block
                  placeholder="2"
                />

                <label class="block text-xs text-muted-foreground">视频每日上限</label>
                <Input
                  v-model="quotaVideosDailyLimitInput"
                  type="number"
                  block
                  placeholder="1"
                />
              </div>
            </div>

            <div class="ui-card">
              <CardSectionHeader title="公开展示" />
              <div class="mt-4 space-y-3">
                <label class="block text-xs text-muted-foreground">Logo 地址</label>
                <Input
                  v-model="localSettings.public_display.logo_url"
                  type="text"
                  block
                  placeholder="logo 地址"
                />

                <label class="block text-xs text-muted-foreground">聊天入口</label>
                <Input
                  v-model="localSettings.public_display.chat_url"
                  type="text"
                  block
                  placeholder="聊天入口地址"
                />

                <label class="block text-xs text-muted-foreground">会话有效时长（小时）</label>
                <Input
                  v-model="sessionExpireHoursInput"
                  type="number"
                  block
                />
              </div>
            </div>

            <div class="ui-card">
              <CardSectionHeader title="说明" />
              <div class="mt-4 space-y-3 text-sm text-muted-foreground">
                <p>设置页已经恢复成旧版交互思路：邮箱提供商下拉选择，按服务商分别填写。</p>
                <p>保存时以前端这份统一 settings 契约为准，刷新相关配置统一收口到 `refresh_settings`。</p>
                <p>后端会在运行时映射到 `basic / retry` 供主服务读取，但数据库只保存 canonical 配置，避免旧值反向覆盖。</p>
                <p>没有重新加回当前后端未支持的 `browser_engine` 和 `samplemail` 专属字段，避免再次出现保存错乱。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Button, Checkbox, HelpTip, Input, SelectMenu } from 'nanocat-ui'
import CardSectionHeader from '@/components/ui/CardSectionHeader.vue'
import PanelPageHeader from '@/components/ui/PanelPageHeader.vue'
import { useSettingsPage } from './settings/useSettingsPage'

const {
  browserModeOptions,
  tempMailProviderOptions,
  imageOutputOptions,
  videoOutputOptions,
  imageModelOptions,
  isLoading,
  localSettings,
  isSaving,
  errorMessage,
  maxAccountSwitchTriesInput,
  textCooldownHoursInput,
  imagesCooldownHoursInput,
  videosCooldownHoursInput,
  sessionCacheTtlInput,
  registerDefaultCountInput,
  refreshWindowHoursInput,
  autoRefreshAccountsSecondsInput,
  scheduledRefreshIntervalMinutesInput,
  verificationCodeResendCountInput,
  refreshBatchSizeInput,
  refreshBatchIntervalMinutesInput,
  refreshCooldownHoursInput,
  minAccountCountInput,
  quotaTextDailyLimitInput,
  quotaImagesDailyLimitInput,
  quotaVideosDailyLimitInput,
  sessionExpireHoursInput,
  handleSave,
} = useSettingsPage()
</script>
