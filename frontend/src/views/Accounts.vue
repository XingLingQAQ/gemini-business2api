<template>
  <div class="relative space-y-8">
    <section class="ui-panel space-y-5">
      <ToolbarShell stack-on-mobile start-class="flex-1" end-class="xl:justify-end">
        <template #start>
          <div class="flex flex-wrap items-center gap-2.5">
          <Input
            :model-value="searchQuery"
            type="text"
            placeholder="搜索账号 ID"
            block
            root-class="min-w-[11rem] flex-1 md:w-80 md:flex-none"
            @update:model-value="searchQuery = $event.trim()"
          />
          <FilterSelect
            v-model="statusFilter"
            :options="statusOptions"
            placeholder="状态筛选"
            aria-label="账号状态筛选"
          />
          <Button
            size="sm"
            variant="outline"
            root-class="shrink-0 whitespace-nowrap"
            :disabled="isLoading"
            @click="refreshAccounts"
          >
            刷新列表
          </Button>
          <Button
            size="sm"
            variant="primary"
            root-class="shrink-0 whitespace-nowrap"
            @click="openImportModal"
          >
            导入账户
          </Button>
          <Button
            size="sm"
            variant="outline"
            root-class="shrink-0 whitespace-nowrap"
            @click="openExportModal"
          >
            导出账户
          </Button>
          <Button
            size="sm"
            variant="outline"
            root-class="shrink-0 whitespace-nowrap"
            @click="openConfigPanel"
          >
            账户配置
          </Button>
          </div>
        </template>

        <template #end>
          <div class="flex flex-wrap items-center justify-end gap-2.5">
          <Button
            size="sm"
            variant="outline"
            root-class="shrink-0 whitespace-nowrap"
            :disabled="!selectedCount || isOperating"
            @click="handleBulkEnable"
          >
            批量启用
          </Button>
          <Button
            size="sm"
            variant="outline"
            root-class="shrink-0 whitespace-nowrap"
            :disabled="!selectedCount || isOperating"
            @click="handleBulkDisable"
          >
            批量禁用
          </Button>
          <Button
            size="sm"
            variant="danger"
            root-class="shrink-0 whitespace-nowrap"
            :disabled="!selectedCount || isOperating"
            @click="handleBulkDelete"
          >
            批量删除
          </Button>
          </div>
        </template>
      </ToolbarShell>

      <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <Checkbox :model-value="allSelected" @update:model-value="toggleSelectAll">
            全选当前结果
          </Checkbox>
          <span class="rounded-full border border-border bg-muted/30 px-3 py-1.5">
            账号总数 {{ filteredAccounts.length }}
          </span>
          <span class="rounded-full border border-border bg-muted/30 px-3 py-1.5">
            已选 {{ selectedCount }}
          </span>
          <span
            v-if="batchProgress"
            class="rounded-full border border-border bg-muted/30 px-3 py-1.5"
          >
            处理中 {{ batchProgress.current }}/{{ batchProgress.total }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <button
            class="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
            :class="viewMode === 'table'
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground'"
            title="列表视图"
            aria-label="列表视图"
            @click="viewMode = 'table'"
          >
            <svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round">
              <path d="M4 5.5h12" />
              <path d="M4 10h12" />
              <path d="M4 14.5h12" />
            </svg>
          </button>
          <button
            class="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
            :class="viewMode === 'card'
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground'"
            title="卡片视图"
            aria-label="卡片视图"
            @click="viewMode = 'card'"
          >
            <svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3.5" y="3.5" width="5.5" height="5.5" rx="1" />
              <rect x="11" y="3.5" width="5.5" height="5.5" rx="1" />
              <rect x="3.5" y="11" width="5.5" height="5.5" rx="1" />
              <rect x="11" y="11" width="5.5" height="5.5" rx="1" />
            </svg>
          </button>
        </div>
      </div>

      <div
        v-if="false && isLoading && !filteredAccounts.length"
        class="rounded-2xl border border-border bg-background px-4 py-8 text-center text-sm text-muted-foreground"
      >
        正在加载账号...
      </div>

      <div
        v-if="isLoading && !filteredAccounts.length"
        class="rounded-2xl border border-border bg-background px-4 py-8 text-center text-sm text-muted-foreground"
      >
        正在加载账号...
      </div>

      <div
        v-else-if="viewMode === 'card'"
        class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3"
      >
        <div
          v-if="!filteredAccounts.length && !isLoading"
          class="col-span-full"
        >
          <EmptyState
            plain
            title="暂无账号数据"
            description="可以先导入账号配置，再进行启用、禁用和导出操作。"
          />
        </div>

        <div
          v-for="account in paginatedAccounts"
          :key="account.id"
          class="ui-card cursor-pointer transition-colors"
          :class="[rowClass(account), selectedIds.has(account.id) ? 'ring-2 ring-primary/20' : '']"
          @click="toggleSelect(account.id)"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs text-muted-foreground">账号 ID</p>
              <p class="mt-1 font-mono text-xs text-foreground">{{ account.id }}</p>
            </div>
            <Checkbox
              :model-value="selectedIds.has(account.id)"
              @update:model-value="toggleSelect(account.id, $event)"
              @click.stop
            />
          </div>

          <div class="mt-4 grid grid-cols-2 gap-3 text-xs text-muted-foreground">
            <div>
              <p>状态</p>
              <p class="mt-1 flex flex-wrap items-center gap-1.5 text-sm font-semibold text-foreground">
                <span
                  class="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-xs"
                  :class="statusClass(account)"
                >
                  {{ statusLabel(account) }}
                </span>
                <span
                  v-if="account.trial_days_remaining != null"
                  class="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs font-medium"
                  :class="trialBadgeClass(account.trial_days_remaining)"
                >
                  {{ account.trial_days_remaining }} 天
                </span>
              </p>
            </div>
            <div>
              <p>剩余时间</p>
              <p class="mt-1 text-sm font-semibold" :class="remainingClass(account)">
                {{ displayRemaining(account.remaining_display) }}
              </p>
              <p v-if="account.expires_at" class="mt-1 text-[11px]">
                {{ account.expires_at }}
              </p>
            </div>
            <div>
              <p>配额</p>
              <div class="mt-1">
                <QuotaBadge v-if="account.quota_status" :quota-status="account.quota_status" />
                <span v-else class="text-xs text-muted-foreground">-</span>
              </div>
            </div>
            <div>
              <p>失败数</p>
              <p class="mt-1 text-sm font-semibold text-foreground">{{ account.failure_count }}</p>
            </div>
            <div>
              <p>成功数</p>
              <p class="mt-1 text-sm font-semibold text-foreground">{{ account.conversation_count }}</p>
            </div>
          </div>

          <div class="mt-4 flex flex-wrap items-center gap-2">
            <Button size="xs" variant="outline" @click.stop="openEdit(account.id)">编辑</Button>
            <Button
              v-if="shouldShowEnable(account)"
              size="xs"
              variant="outline"
              @click.stop="handleEnable(account.id)"
            >
              启用
            </Button>
            <Button
              v-else
              size="xs"
              variant="outline"
              @click.stop="handleDisable(account.id)"
            >
              禁用
            </Button>
            <Button size="xs" variant="danger" @click.stop="handleDelete(account.id)">删除</Button>
          </div>
        </div>

        <div
          v-if="false && !filteredAccounts.length && !isLoading"
          class="col-span-full rounded-2xl border border-border bg-background p-4 text-center text-xs text-muted-foreground"
        >
          暂无账号数据，请检查后台配置。
        </div>
      </div>

      <div v-else class="scrollbar-slim overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <tr>
              <th class="py-3 pr-4">
                <Checkbox :model-value="allSelected" @update:model-value="toggleSelectAll" />
              </th>
              <th class="py-3 pr-6">账号 ID</th>
              <th class="py-3 pr-6">状态</th>
              <th class="py-3 pr-6">剩余/过期</th>
              <th class="py-3 pr-6">配额</th>
              <th class="py-3 pr-6">失败数</th>
              <th class="py-3 pr-6">成功数</th>
              <th class="py-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody class="text-sm text-foreground">
            <tr v-if="false && !filteredAccounts.length && !isLoading">
              <td colspan="8" class="py-8 text-center text-muted-foreground">
                暂无账号数据，请检查后台配置。
              </td>
            </tr>
            <tr v-if="!filteredAccounts.length && !isLoading">
              <td colspan="8" class="py-8">
                <EmptyState
                  plain
                  title="暂无账号数据"
                  description="可以先导入账号配置，再进行启用、禁用和导出操作。"
                />
              </td>
            </tr>
            <tr
              v-for="account in paginatedAccounts"
              :key="account.id"
              class="border-t border-border"
              :class="[rowClass(account), selectedIds.has(account.id) ? 'bg-primary/5' : '']"
              @click="toggleSelect(account.id)"
            >
              <td class="py-4 pr-4" @click.stop>
                <Checkbox
                  :model-value="selectedIds.has(account.id)"
                  @update:model-value="toggleSelect(account.id, $event)"
                />
              </td>
              <td class="py-4 pr-6 font-mono text-xs text-foreground">
                {{ account.id }}
              </td>
              <td class="py-4 pr-6">
                <div class="flex flex-wrap items-center gap-1.5">
                  <span
                    class="inline-flex items-center rounded-full border border-border px-3 py-1 text-xs"
                    :class="statusClass(account)"
                  >
                    {{ statusLabel(account) }}
                  </span>
                  <span
                    v-if="account.trial_days_remaining != null"
                    class="inline-flex items-center rounded-full border border-border px-2 py-1 text-xs font-medium"
                    :class="trialBadgeClass(account.trial_days_remaining)"
                  >
                    {{ account.trial_days_remaining }} 天
                  </span>
                </div>
              </td>
              <td class="py-4 pr-6">
                <div class="text-sm font-semibold" :class="remainingClass(account)">
                  {{ displayRemaining(account.remaining_display) }}
                </div>
                <span v-if="account.expires_at" class="block text-[11px] text-muted-foreground">
                  {{ account.expires_at }}
                </span>
              </td>
              <td class="py-4 pr-6">
                <QuotaBadge v-if="account.quota_status" :quota-status="account.quota_status" />
                <span v-else class="text-xs text-muted-foreground">-</span>
              </td>
              <td class="py-4 pr-6 text-xs text-muted-foreground">
                {{ account.failure_count }}
              </td>
              <td class="py-4 pr-6 text-xs text-muted-foreground">
                {{ account.conversation_count }}
              </td>
              <td class="py-4 text-right">
                <div class="flex flex-wrap items-center justify-end gap-2">
                  <Button size="xs" variant="outline" @click.stop="openEdit(account.id)">编辑</Button>
                  <Button
                    v-if="shouldShowEnable(account)"
                    size="xs"
                    variant="outline"
                    @click.stop="handleEnable(account.id)"
                  >
                    启用
                  </Button>
                  <Button
                    v-else
                    size="xs"
                    variant="outline"
                    @click.stop="handleDisable(account.id)"
                  >
                    禁用
                  </Button>
                  <Button size="xs" variant="danger" @click.stop="handleDelete(account.id)">删除</Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex flex-col gap-3 border-t border-border/60 pt-4 md:flex-row md:items-center md:justify-between">
        <div class="text-xs text-muted-foreground">
          当前展示 {{ paginatedAccounts.length }} / {{ filteredAccounts.length }} 条
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-muted-foreground">每页</span>
          <div class="w-[110px] shrink-0">
            <SelectMenu v-model="pageSize" :options="pageSizeOptions" />
          </div>
          <Button size="sm" variant="outline" :disabled="currentPage === 1" @click="currentPage--">
            上一页
          </Button>
          <span class="text-sm text-muted-foreground">{{ currentPage }} / {{ totalPages }}</span>
          <Button size="sm" variant="outline" :disabled="currentPage === totalPages" @click="currentPage++">
            下一页
          </Button>
        </div>
      </div>
    </section>
    <input
      ref="importFileInput"
      type="file"
      accept=".json,.txt,text/plain,application/json"
      class="hidden"
      @change="handleImportFile"
    />

    <ModalShell
      :open="isImportOpen"
      size-class="max-w-2xl"
      body-class="p-0"
      panel-class="overflow-hidden"
      :show-close="false"
      @close="closeImportModal"
    >
      <div class="flex max-h-[90vh] flex-col overflow-hidden">
          <div class="flex items-center justify-between border-b border-border/60 px-6 py-4">
            <div>
              <p class="text-sm font-medium text-foreground">导入账户</p>
              <p class="mt-1 text-xs text-muted-foreground">
                支持 JSON 配置文件，或粘贴 `duckmail----邮箱----密码` 这类文本格式。
              </p>
            </div>
            <Button size="xs" variant="outline" root-class="min-w-14 justify-center" @click="closeImportModal">
              关闭
            </Button>
          </div>

          <div class="scrollbar-slim flex-1 space-y-4 overflow-y-auto px-6 py-5">
            <div class="flex flex-wrap items-center gap-3">
              <Button size="sm" variant="outline" @click="triggerImportFile">
                选择文件
              </Button>
              <span class="text-xs text-muted-foreground">
                {{ importFileName || '未选择文件，可直接在下方粘贴内容' }}
              </span>
            </div>

            <textarea
              v-model="importText"
              rows="14"
              class="ui-textarea-sm min-h-[18rem] font-mono"
              placeholder="粘贴 JSON 数组，或一行一个的账号导入文本"
            ></textarea>

            <div
              v-if="importError"
              class="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {{ importError }}
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 border-t border-border/60 px-6 py-4">
            <Button size="sm" variant="outline" @click="closeImportModal">取消</Button>
            <Button size="sm" variant="primary" :disabled="isImporting" @click="handleImportSubmit">
              {{ isImporting ? '导入中...' : '确认导入' }}
            </Button>
          </div>
      </div>
    </ModalShell>

    <ModalShell
      :open="isExportOpen"
      size-class="max-w-lg"
      body-class="p-0"
      panel-class="overflow-hidden"
      :show-close="false"
      @close="closeExportModal"
    >
      <div class="overflow-hidden">
          <div class="flex items-center justify-between border-b border-border/60 px-6 py-4">
            <div>
              <p class="text-sm font-medium text-foreground">导出账户</p>
              <p class="mt-1 text-xs text-muted-foreground">可导出全部配置，或仅导出当前已选账户。</p>
            </div>
            <Button size="xs" variant="outline" root-class="min-w-14 justify-center" @click="closeExportModal">
              关闭
            </Button>
          </div>

          <div class="space-y-4 px-6 py-5">
            <div>
              <label class="block text-xs text-muted-foreground">导出范围</label>
              <div class="mt-2">
                <SelectMenu v-model="exportScope" :options="exportScopeOptions" class="w-full" />
              </div>
            </div>
            <div>
              <label class="block text-xs text-muted-foreground">导出格式</label>
              <div class="mt-2">
                <SelectMenu v-model="exportFormat" :options="exportFormatOptions" class="w-full" />
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 border-t border-border/60 px-6 py-4">
            <Button size="sm" variant="outline" @click="closeExportModal">取消</Button>
            <Button size="sm" variant="primary" @click="runExport">开始导出</Button>
          </div>
      </div>
    </ModalShell>

    <ModalShell
      :open="isConfigOpen"
      size-class="max-w-4xl"
      body-class="p-0"
      panel-class="overflow-hidden"
      :show-close="false"
      @close="closeConfigPanel"
    >
      <div class="flex max-h-[92vh] flex-col overflow-hidden">
          <div class="flex items-center justify-between border-b border-border/60 px-6 py-4">
            <div>
              <p class="text-sm font-medium text-foreground">账户配置</p>
              <p class="mt-1 text-xs text-muted-foreground">支持直接编辑完整 JSON。保存前请先切换为明文。</p>
            </div>
            <div class="flex items-center gap-2">
              <Button size="xs" variant="outline" @click="toggleConfigMask">
                {{ configMasked ? '显示明文' : '隐藏敏感值' }}
              </Button>
              <Button size="xs" variant="outline" root-class="min-w-14 justify-center" @click="closeConfigPanel">
                关闭
              </Button>
            </div>
          </div>

          <div class="scrollbar-slim flex-1 space-y-4 overflow-y-auto px-6 py-5">
            <textarea
              v-model="configJson"
              rows="20"
              class="ui-textarea-sm min-h-[26rem] font-mono"
            ></textarea>

            <div
              v-if="configError"
              class="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {{ configError }}
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 border-t border-border/60 px-6 py-4">
            <Button size="sm" variant="outline" @click="closeConfigPanel">取消</Button>
            <Button size="sm" variant="primary" :disabled="isOperating" @click="saveConfigPanel">
              保存配置
            </Button>
          </div>
      </div>
    </ModalShell>

    <ModalShell
      :open="isEditOpen"
      size-class="max-w-2xl"
      body-class="p-0"
      panel-class="overflow-hidden"
      :show-close="false"
      @close="closeEdit"
    >
      <div class="overflow-hidden">
          <div class="flex items-center justify-between border-b border-border/60 px-6 py-4">
            <div>
              <p class="text-sm font-medium text-foreground">编辑账户</p>
              <p class="mt-1 text-xs text-muted-foreground">修改当前账户的 Cookie 与配置字段。</p>
            </div>
            <Button size="xs" variant="outline" root-class="min-w-14 justify-center" @click="closeEdit">
              关闭
            </Button>
          </div>

          <div class="space-y-4 px-6 py-5">
            <FieldGrid :columns="2">
              <FormField label="账号 ID">
                账号 ID
                <Input v-model="editForm.id" type="text" block />
              </FormField>
              <FormField label="过期时间">
                过期时间
                <Input v-model="editForm.expires_at" type="text" block />
              </FormField>
            </FieldGrid>

            <FormField label="secure_c_ses">
              <Input v-model="editForm.secure_c_ses" type="text" block root-class="font-mono" />
            </FormField>

            <FieldGrid :columns="2">
              <FormField label="csesidx">
                csesidx
                <Input v-model="editForm.csesidx" type="text" block />
              </FormField>
              <FormField label="config_id">
                config_id
                <Input v-model="editForm.config_id" type="text" block />
              </FormField>
            </FieldGrid>

            <FormField label="host_c_oses">
              <Input v-model="editForm.host_c_oses" type="text" block />
            </FormField>

            <div
              v-if="editError"
              class="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {{ editError }}
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 border-t border-border/60 px-6 py-4">
            <Button size="sm" variant="outline" @click="closeEdit">取消</Button>
            <Button size="sm" variant="primary" :disabled="isOperating" @click="saveEdit">保存</Button>
          </div>
      </div>
    </ModalShell>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Button,
  Checkbox,
  EmptyState,
  FieldGrid,
  FilterSelect,
  FormField,
  Input,
  ModalShell,
  SelectMenu,
  ToolbarShell,
} from 'nanocat-ui'
import QuotaBadge from '@/components/QuotaBadge.vue'
import { accountsApi } from '@/api'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import { useToast } from '@/composables/useToast'
import { useAccountsStore } from '@/stores/accounts'
import type { AccountConfigItem, AdminAccount } from '@/types/api'

const accountsStore = useAccountsStore()
const { accounts, isLoading, isOperating, batchProgress } = storeToRefs(accountsStore)
const toast = useToast()
const confirmDialog = useConfirmDialog()

const searchQuery = ref('')
const statusFilter = ref('all')
const selectedIds = ref<Set<string>>(new Set())
const viewMode = ref<'table' | 'card'>(
  (localStorage.getItem('accounts_view_mode') as 'table' | 'card') || 'table',
)
const currentPage = ref(1)
const pageSize = ref(50)

const isImportOpen = ref(false)
const importText = ref('')
const importError = ref('')
const isImporting = ref(false)
const importFileInput = ref<HTMLInputElement | null>(null)
const importFileName = ref('')

const isExportOpen = ref(false)
const exportScope = ref<'all' | 'selected'>('all')
const exportFormat = ref<'json' | 'txt'>('json')

const isConfigOpen = ref(false)
const configError = ref('')
const configJson = ref('')
const configMasked = ref(false)
const configData = ref<AccountConfigItem[]>([])

const isEditOpen = ref(false)
const editError = ref('')
const editIndex = ref<number | null>(null)
const configAccounts = ref<AccountConfigItem[]>([])
const editForm = ref({
  id: '',
  secure_c_ses: '',
  csesidx: '',
  config_id: '',
  host_c_oses: '',
  expires_at: '',
})

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '正常', value: '正常' },
  { label: '即将过期', value: '即将过期' },
  { label: '已过期', value: '已过期' },
  { label: '手动禁用', value: '手动禁用' },
  { label: '403 禁用', value: '403 禁用' },
  { label: '429 限流', value: '429 限流' },
]

const pageSizeOptions = [
  { label: '20 / 页', value: 20 },
  { label: '50 / 页', value: 50 },
  { label: '100 / 页', value: 100 },
]

const selectedCount = computed(() => selectedIds.value.size)
const exportScopeOptions = computed(() => [
  { label: '全部账户', value: 'all' },
  { label: `当前已选 (${selectedCount.value})`, value: 'selected' },
])

const exportFormatOptions = [
  { label: 'JSON', value: 'json' },
  { label: 'TXT', value: 'txt' },
]

const statusLabel = (account: AdminAccount) => {
  if (account.cooldown_reason?.includes('429') && account.cooldown_seconds > 0) {
    return '429 限流'
  }
  if (account.disabled) {
    if (account.disabled_reason?.includes('403')) {
      return '403 禁用'
    }
    return '手动禁用'
  }
  if (account.status === '已过期') return '已过期'
  if (account.status === '即将过期') return '即将过期'
  return '正常'
}

const filteredAccounts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return accounts.value.filter((account) => {
    const matchesQuery = !query || account.id.toLowerCase().includes(query)
    const matchesStatus = statusFilter.value === 'all' || statusLabel(account) === statusFilter.value
    return matchesQuery && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredAccounts.value.length / pageSize.value)))
const paginatedAccounts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredAccounts.value.slice(start, start + pageSize.value)
})
const allSelected = computed(() =>
  filteredAccounts.value.length > 0 &&
  filteredAccounts.value.every((account) => selectedIds.value.has(account.id)),
)

watch(viewMode, (value) => {
  localStorage.setItem('accounts_view_mode', value)
})

watch([searchQuery, statusFilter, pageSize], () => {
  currentPage.value = 1
})

watch(filteredAccounts, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

watch(accounts, (value) => {
  const validIds = new Set(value.map((account) => account.id))
  selectedIds.value = new Set(
    Array.from(selectedIds.value).filter((accountId) => validIds.has(accountId)),
  )
})

const refreshAccounts = async () => {
  await accountsStore.loadAccounts()
  selectedIds.value = new Set()
}

const statusClass = (account: AdminAccount) => {
  const status = statusLabel(account)
  if (status === '429 限流' || status === '即将过期') {
    return 'bg-amber-200 text-amber-900'
  }
  if (status === '已过期') {
    return 'bg-destructive/10 text-destructive'
  }
  if (status === '手动禁用') {
    return 'bg-muted text-muted-foreground'
  }
  if (status === '403 禁用') {
    return 'bg-rose-600 text-white'
  }
  return 'bg-emerald-500 text-white'
}

const shouldShowEnable = (account: AdminAccount) => {
  if (account.cooldown_reason?.includes('429') && account.cooldown_seconds > 0) {
    return true
  }
  return account.disabled
}

const displayRemaining = (value: string) => {
  if (value === '已过期') return '过期'
  if (value === '未设置') return '未设置'
  return value
}

const remainingClass = (account: AdminAccount) => {
  if (account.status === '已过期') return 'text-rose-600'
  if (account.status === '即将过期') return 'text-amber-700'
  if (account.status === '未设置') return 'text-muted-foreground'
  return 'text-emerald-600'
}

const trialBadgeClass = (days: number | null | undefined) => {
  if (days == null) return ''
  if (days > 7) return 'bg-emerald-500 text-white'
  if (days >= 3) return 'bg-amber-500 text-white'
  return 'bg-rose-500 text-white'
}

const rowClass = (account: AdminAccount) => {
  const status = statusLabel(account)
  if (status === '手动禁用' || status === '已过期' || status === '403 禁用') {
    return 'bg-muted/70'
  }
  return ''
}

const toggleSelect = (accountId: string, checked?: boolean) => {
  const next = new Set(selectedIds.value)
  const shouldSelect = typeof checked === 'boolean' ? checked : !next.has(accountId)
  if (shouldSelect) {
    next.add(accountId)
  } else {
    next.delete(accountId)
  }
  selectedIds.value = next
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedIds.value = new Set()
    return
  }
  selectedIds.value = new Set(filteredAccounts.value.map((account) => account.id))
}

const getConfigId = (account: AccountConfigItem, index: number) =>
  account.id || account.mail_address || `account_${index + 1}`

const loadConfigList = async () => {
  const response = await accountsApi.getConfig()
  return response.accounts.map((account, index) => ({
    ...account,
    id: getConfigId(account, index),
  }))
}

const applyEditTarget = (list: AccountConfigItem[], accountId: string) => {
  const targetIndex = list.findIndex((account) => account.id === accountId)
  if (targetIndex === -1) {
    editError.value = '未找到对应账号配置。'
    return
  }

  const target = list[targetIndex]
  editForm.value = {
    id: target.id,
    secure_c_ses: target.secure_c_ses,
    csesidx: target.csesidx,
    config_id: target.config_id,
    host_c_oses: target.host_c_oses || '',
    expires_at: target.expires_at || '',
  }
  configAccounts.value = list
  editIndex.value = targetIndex
  isEditOpen.value = true
}

const openEdit = async (accountId: string) => {
  editError.value = ''
  try {
    const list = await loadConfigList()
    applyEditTarget(list, accountId)
  } catch (error: any) {
    editError.value = error.message || '加载账号配置失败'
  }
}

const closeEdit = () => {
  isEditOpen.value = false
  editError.value = ''
  editIndex.value = null
}

const saveEdit = async () => {
  if (editIndex.value === null) return

  const next = [...configAccounts.value]
  next[editIndex.value] = {
    ...next[editIndex.value],
    id: editForm.value.id.trim(),
    secure_c_ses: editForm.value.secure_c_ses.trim(),
    csesidx: editForm.value.csesidx.trim(),
    config_id: editForm.value.config_id.trim(),
    host_c_oses: editForm.value.host_c_oses.trim() || undefined,
    expires_at: editForm.value.expires_at.trim() || undefined,
  }

  try {
    await accountsStore.updateConfig(next)
    toast.success('账号编辑成功')
    selectedIds.value = new Set([editForm.value.id.trim()])
    closeEdit()
  } catch (error: any) {
    editError.value = error.message || '保存失败'
    toast.error(error.message || '保存失败')
  }
}

const openConfigPanel = async () => {
  configError.value = ''
  try {
    const response = await accountsApi.getConfig()
    configData.value = Array.isArray(response.accounts) ? response.accounts : []
    configJson.value = JSON.stringify(maskConfig(configData.value), null, 2)
    configMasked.value = true
    isConfigOpen.value = true
  } catch (error: any) {
    configError.value = error.message || '加载账号配置失败'
  }
}

const closeConfigPanel = () => {
  isConfigOpen.value = false
  configError.value = ''
  configMasked.value = false
}

const getConfigFromEditor = () => {
  const parsed = JSON.parse(configJson.value)
  if (!Array.isArray(parsed)) {
    throw new Error('配置格式必须是数组。')
  }
  return parsed as AccountConfigItem[]
}

const maskValue = (value: unknown) => {
  if (typeof value !== 'string') return value
  if (!value) return value
  if (value.length <= 6) return `${value.slice(0, 2)}****`
  return `${value.slice(0, 3)}****`
}

const maskConfig = (list: AccountConfigItem[]) => {
  const fields = new Set([
    'secure_c_ses',
    'csesidx',
    'config_id',
    'host_c_oses',
    'mail_password',
    'mail_refresh_token',
    'mail_client_id',
    'mail_api_key',
    'mail_jwt_token',
  ])

  return list.map((item) => {
    const next = { ...item } as Record<string, unknown>
    fields.forEach((field) => {
      if (next[field]) {
        next[field] = maskValue(next[field])
      }
    })
    return next as AccountConfigItem
  })
}

const toggleConfigMask = () => {
  configError.value = ''
  if (!configMasked.value) {
    try {
      configData.value = getConfigFromEditor()
    } catch (error: any) {
      configError.value = error.message || 'JSON 格式错误'
      return
    }
    configJson.value = JSON.stringify(maskConfig(configData.value), null, 2)
    configMasked.value = true
    return
  }

  configJson.value = JSON.stringify(configData.value, null, 2)
  configMasked.value = false
}

const saveConfigPanel = async () => {
  configError.value = ''
  if (configMasked.value) {
    configError.value = '请先切换为明文，再保存配置。'
    return
  }

  try {
    const parsed = getConfigFromEditor()
    await accountsStore.updateConfig(parsed)
    toast.success('配置保存成功')
    closeConfigPanel()
  } catch (error: any) {
    configError.value = error.message || '保存失败'
    toast.error(error.message || '保存失败')
  }
}

const openImportModal = () => {
  isImportOpen.value = true
  importText.value = ''
  importError.value = ''
  importFileName.value = ''
}

const closeImportModal = () => {
  isImportOpen.value = false
  importText.value = ''
  importError.value = ''
  importFileName.value = ''
}

const IMPORT_EXPIRES_AT = '1970-01-01 00:00:00'

const parseImportLines = (raw: string) => {
  const items: AccountConfigItem[] = []
  const errors: string[] = []
  const lines = raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)

  lines.forEach((line, index) => {
    const parts = line.split('----').map((part) => part.trim())
    const lineNo = index + 1

    if (!parts.length) return

    if (parts[0].toLowerCase() === 'duckmail') {
      if (parts.length < 3 || !parts[1] || !parts[2]) {
        errors.push(`第 ${lineNo} 行格式错误（duckmail）`)
        return
      }
      const email = parts[1]
      const password = parts.slice(2).join('----')
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'duckmail',
        mail_address: email,
        mail_password: password,
      })
      return
    }

    if (parts[0].toLowerCase() === 'moemail') {
      if (parts.length < 3 || !parts[1] || !parts[2]) {
        errors.push(`第 ${lineNo} 行格式错误（moemail）`)
        return
      }
      const email = parts[1]
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'moemail',
        mail_address: email,
        mail_password: parts[2],
      })
      return
    }

    if (parts[0].toLowerCase() === 'freemail') {
      if (parts.length < 2 || !parts[1]) {
        errors.push(`第 ${lineNo} 行格式错误（freemail）`)
        return
      }
      const email = parts[1]
      if (parts.length >= 6) {
        items.push({
          id: email,
          secure_c_ses: '',
          csesidx: '',
          config_id: '',
          expires_at: IMPORT_EXPIRES_AT,
          mail_provider: 'freemail',
          mail_address: email,
          mail_password: '',
          mail_base_url: parts[2] || undefined,
          mail_jwt_token: parts[3] || undefined,
          mail_verify_ssl: parts[4] === 'true' || parts[4] === '1',
          mail_domain: parts[5] || undefined,
        })
        return
      }
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'freemail',
        mail_address: email,
        mail_password: '',
      })
      return
    }

    if (parts[0].toLowerCase() === 'gptmail') {
      if (parts.length < 2 || !parts[1]) {
        errors.push(`第 ${lineNo} 行格式错误（gptmail）`)
        return
      }
      const email = parts[1]
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'gptmail',
        mail_address: email,
        mail_password: '',
      })
      return
    }

    if (parts[0].toLowerCase() === 'cfmail') {
      if (parts.length < 2 || !parts[1]) {
        errors.push(`第 ${lineNo} 行格式错误（cfmail）`)
        return
      }
      const email = parts[1]
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'cfmail',
        mail_address: email,
        mail_password: parts[2] || '',
      })
      return
    }

    if (parts.length >= 4 && parts[0] && parts[2] && parts[3]) {
      const email = parts[0]
      const password = parts[1] || ''
      const clientId = parts[2]
      const refreshToken = parts.slice(3).join('----')
      items.push({
        id: email,
        secure_c_ses: '',
        csesidx: '',
        config_id: '',
        expires_at: IMPORT_EXPIRES_AT,
        mail_provider: 'microsoft',
        mail_address: email,
        mail_password: password,
        mail_client_id: clientId,
        mail_refresh_token: refreshToken,
        mail_tenant: 'consumers',
      })
      return
    }

    errors.push(`第 ${lineNo} 行格式错误`)
  })

  return { items, errors }
}

const triggerImportFile = () => {
  importFileInput.value?.click()
}

const handleImportFile = async (event: Event) => {
  const target = event.target as HTMLInputElement | null
  const file = target?.files?.[0]
  if (!file) return

  try {
    importText.value = await file.text()
    importFileName.value = file.name
    importError.value = ''
  } catch (error: any) {
    importError.value = error.message || '文件解析失败'
  } finally {
    if (target) {
      target.value = ''
    }
  }
}

const normalizeJsonImportList = (raw: string) => {
  const parsed = JSON.parse(raw)
  const list = Array.isArray(parsed) ? parsed : parsed?.accounts
  if (!Array.isArray(list)) {
    throw new Error('JSON 格式错误：需要数组或包含 accounts 字段')
  }

  return list.map((item, index) => {
    if (!item || typeof item !== 'object') {
      throw new Error(`第 ${index + 1} 条 JSON 记录不是对象`)
    }
    const record = item as Record<string, unknown>
    const id = String(record.id || record.mail_address || '').trim()
    if (!id) {
      throw new Error(`第 ${index + 1} 条 JSON 记录缺少 id`)
    }

    return {
      ...(record as AccountConfigItem),
      id,
      secure_c_ses: typeof record.secure_c_ses === 'string' ? record.secure_c_ses : '',
      csesidx: typeof record.csesidx === 'string' ? record.csesidx : '',
      config_id: typeof record.config_id === 'string' ? record.config_id : '',
    } as AccountConfigItem
  })
}

const mergeJsonImport = async (items: AccountConfigItem[]) => {
  const existing = await loadConfigList()
  const next = [...existing]
  const indexMap = new Map(next.map((account, index) => [account.id, index]))
  const importedIds: string[] = []

  items.forEach((item) => {
    const index = indexMap.get(item.id)
    if (index === undefined) {
      next.push(item)
    } else {
      next[index] = { ...next[index], ...item }
    }
    importedIds.push(item.id)
  })

  await accountsStore.updateConfig(next)
  selectedIds.value = new Set(importedIds)
  toast.success(`导入 ${importedIds.length} 条账号配置`)
}

const mergeTextImport = async (items: AccountConfigItem[]) => {
  const list = await loadConfigList()
  const next = [...list]
  const indexMap = new Map(next.map((account, index) => [account.id, index]))
  const importedIds: string[] = []

  items.forEach((item) => {
    const index = indexMap.get(item.id)
    if (index === undefined) {
      next.push(item)
      importedIds.push(item.id)
      return
    }

    const existing = next[index]
    const updated: AccountConfigItem = {
      ...existing,
      mail_provider: item.mail_provider,
      mail_address: item.mail_address,
    }

    if (item.mail_provider === 'microsoft') {
      updated.mail_client_id = item.mail_client_id
      updated.mail_refresh_token = item.mail_refresh_token
      updated.mail_tenant = item.mail_tenant
      updated.mail_password = item.mail_password
    } else {
      updated.mail_password = item.mail_password
      updated.mail_client_id = undefined
      updated.mail_refresh_token = undefined
      updated.mail_tenant = undefined
      updated.mail_base_url = item.mail_base_url
      updated.mail_jwt_token = item.mail_jwt_token
      updated.mail_verify_ssl = item.mail_verify_ssl
      updated.mail_domain = item.mail_domain
    }

    next[index] = updated
    importedIds.push(item.id)
  })

  await accountsStore.updateConfig(next)
  selectedIds.value = new Set(importedIds)
  toast.success(`成功导入 ${importedIds.length} 个账户`)
}

const handleImportSubmit = async () => {
  importError.value = ''
  const raw = importText.value.trim()
  if (!raw) {
    importError.value = '请输入导入内容'
    return
  }

  isImporting.value = true
  try {
    const looksLikeJson =
      importFileName.value.toLowerCase().endsWith('.json') ||
      raw.startsWith('[') ||
      raw.startsWith('{')

    if (looksLikeJson) {
      const items = normalizeJsonImportList(raw)
      await mergeJsonImport(items)
    } else {
      const { items, errors } = parseImportLines(raw)
      if (!items.length) {
        throw new Error(errors.length ? errors.join('，') : '未识别到有效账号')
      }
      if (errors.length) {
        throw new Error(errors.slice(0, 3).join('，'))
      }
      await mergeTextImport(items)
    }

    closeImportModal()
  } catch (error: any) {
    importError.value = error.message || '导入失败'
    toast.error(error.message || '导入失败')
  } finally {
    isImporting.value = false
  }
}

const openExportModal = () => {
  exportScope.value = selectedCount.value > 0 ? 'selected' : 'all'
  exportFormat.value = 'json'
  isExportOpen.value = true
}

const closeExportModal = () => {
  isExportOpen.value = false
}

const downloadText = (content: string, filename: string, mime: string) => {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const exportConfig = async (format: 'json' | 'txt', scope: 'all' | 'selected') => {
  const response = await accountsApi.getConfig()
  let list = Array.isArray(response.accounts) ? response.accounts : []
  if (scope === 'selected') {
    if (!selectedIds.value.size) {
      throw new Error('当前没有选中的账户')
    }
    list = list.filter((item) => selectedIds.value.has(item.id))
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  if (format === 'json') {
    downloadText(
      JSON.stringify(list, null, 2),
      `accounts-${timestamp}.json`,
      'application/json',
    )
    toast.success('导出 JSON 成功')
    return
  }

  const lines = list.map((item) => {
    const provider = (item.mail_provider || '').toLowerCase()
    const email = item.mail_address || item.id || ''
    if (!email) return ''
    if (provider === 'moemail') {
      return `moemail----${email}----${item.mail_password || ''}`
    }
    if (provider === 'freemail') {
      return `freemail----${email}`
    }
    if (provider === 'gptmail') {
      return `gptmail----${email}`
    }
    if (provider === 'cfmail') {
      return `cfmail----${email}----${item.mail_password || ''}`
    }
    if (provider === 'duckmail') {
      return `duckmail----${email}----${item.mail_password || ''}`
    }
    if (provider === 'microsoft' || item.mail_client_id || item.mail_refresh_token) {
      return `${email}----${item.mail_password || ''}----${item.mail_client_id || ''}----${item.mail_refresh_token || ''}`
    }
    if (item.mail_password) {
      return `duckmail----${email}----${item.mail_password}`
    }
    return email
  }).filter(Boolean)

  downloadText(lines.join('\n'), `accounts-${timestamp}.txt`, 'text/plain')
  toast.success('导出 TXT 成功')
}

const runExport = async () => {
  try {
    await exportConfig(exportFormat.value, exportScope.value)
    closeExportModal()
  } catch (error: any) {
    toast.error(error.message || '导出失败')
  }
}

const formatOpErrors = (errors: string[]) => {
  if (!errors.length) return ''
  const sample = errors[0]
  return `失败 ${errors.length} 个${sample ? `，示例：${sample}` : ''}`
}

const handleOpResult = (
  result: { ok: boolean; errors: string[] },
  successMessage: string,
  failMessage: string,
) => {
  if (result.ok) {
    toast.success(successMessage)
    return true
  }
  const detail = formatOpErrors(result.errors)
  toast.error(detail ? `${failMessage}（${detail}）` : failMessage)
  return false
}

const handleBulkEnable = async () => {
  if (!selectedIds.value.size || isOperating.value) return
  try {
    const result = await accountsStore.bulkEnable(Array.from(selectedIds.value))
    if (handleOpResult(result, '批量启用成功', '批量启用失败')) {
      selectedIds.value = new Set()
    }
  } catch (error: any) {
    toast.error(error.message || '批量启用失败')
  }
}

const handleBulkDisable = async () => {
  if (!selectedIds.value.size || isOperating.value) return
  const confirmed = await confirmDialog.ask({
    title: '批量禁用',
    message: '确定要批量禁用选中的账号吗？',
  })
  if (!confirmed) return

  try {
    const result = await accountsStore.bulkDisable(Array.from(selectedIds.value))
    if (handleOpResult(result, '批量禁用成功', '批量禁用失败')) {
      selectedIds.value = new Set()
    }
  } catch (error: any) {
    toast.error(error.message || '批量禁用失败')
  }
}

const handleBulkDelete = async () => {
  if (!selectedIds.value.size || isOperating.value) return
  const confirmed = await confirmDialog.ask({
    title: '批量删除',
    message: '确定要批量删除选中的账号吗？',
    confirmText: '删除',
  })
  if (!confirmed) return

  try {
    const result = await accountsStore.bulkDelete(Array.from(selectedIds.value))
    if (handleOpResult(result, '批量删除成功', '批量删除失败')) {
      selectedIds.value = new Set()
    }
  } catch (error: any) {
    toast.error(error.message || '批量删除失败')
  }
}

const handleEnable = async (accountId: string) => {
  if (isOperating.value) return
  try {
    const result = await accountsStore.enableAccount(accountId)
    handleOpResult(result, '账号已启用', '启用失败')
  } catch (error: any) {
    toast.error(error.message || '启用失败')
  }
}

const handleDisable = async (accountId: string) => {
  if (isOperating.value) return
  const confirmed = await confirmDialog.ask({
    title: '禁用账号',
    message: '确定要禁用该账号吗？',
  })
  if (!confirmed) return

  try {
    const result = await accountsStore.disableAccount(accountId)
    handleOpResult(result, '账号已禁用', '禁用失败')
  } catch (error: any) {
    toast.error(error.message || '禁用失败')
  }
}

const handleDelete = async (accountId: string) => {
  if (isOperating.value) return
  const confirmed = await confirmDialog.ask({
    title: '删除账号',
    message: '确定要删除该账号吗？',
    confirmText: '删除',
  })
  if (!confirmed) return

  try {
    const result = await accountsStore.deleteAccount(accountId)
    handleOpResult(result, '账号已删除', '删除失败')
  } catch (error: any) {
    toast.error(error.message || '删除失败')
  }
}

onMounted(async () => {
  await refreshAccounts()
})
</script>
