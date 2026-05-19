<template>
  <div class="bill-page">
    <div class="page-head">
      <div>
        <h2>支付宝账单</h2>
        <p>
          后台会优先使用已保存的支付宝账号密码自动登录。若支付宝触发验证码、短信验证或其他安全校验，
          会保留窗口给你手动补一步。登录成功后监测窗口保持最小化在线，页面每 5 分钟自动检查一次登录状态。
        </p>
      </div>
      <div class="head-actions">
        <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
        <el-button :icon="Position" @click="openLogin" :loading="openingLogin">自动登录支付宝</el-button>
        <el-button type="primary" :icon="Download" @click="syncBills" :loading="syncing">同步账单</el-button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="glass-card stat-card">
        <div class="stat-num">{{ total }}</div>
        <div class="stat-label">筛选结果总数</div>
      </div>
      <div class="glass-card stat-card">
        <div class="stat-num">{{ issuedCount }}</div>
        <div class="stat-label">当前页已发卡</div>
      </div>
      <div class="glass-card stat-card">
        <div class="stat-num">{{ voidCount }}</div>
        <div class="stat-label">当前页已作废</div>
      </div>
    </div>

    <div class="glass-card monitor-card" :class="{ offline: monitorIsOffline }">
      <div class="monitor-copy">
        <div class="monitor-head">
          <span class="monitor-title">支付宝登录状态</span>
          <el-tag :type="monitorStatusTagType" size="small">{{ monitorStatusLabel }}</el-tag>
        </div>
        <div class="monitor-text">{{ monitorStatusText }}</div>
        <div class="monitor-meta">
          <span>最近检查：{{ lastStatusCheckedText }}</span>
          <span v-if="monitorStatus.title">{{ monitorStatus.title }}</span>
          <span v-else-if="monitorStatus.pageUrl" class="mono">{{ monitorStatus.pageUrl }}</span>
        </div>
      </div>
      <div class="monitor-actions">
        <el-button size="small" @click="loadMonitorStatus()" :loading="statusLoading">检查状态</el-button>
        <el-button
          v-if="monitorIsOffline"
          size="small"
          type="warning"
          @click="openLogin"
          :loading="openingLogin">
          重新登录
        </el-button>
      </div>
    </div>

    <div class="glass-card table-shell">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索订单号、交易号、付款方、业务说明"
          clearable
          class="search-box"
          @keyup.enter="search"
          @clear="search">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="direction" class="direction-select" @change="search">
          <el-option label="只看收入" value="income" />
          <el-option label="只看支出" value="expense" />
          <el-option label="显示全部" value="all" />
        </el-select>
      </div>

      <div class="batch-bar">
        <div class="batch-meta">已选择 {{ selectedIds.length }} 条</div>
        <div class="batch-actions">
          <el-button size="small" @click="batchUpdateStatus('pending')" :disabled="!selectedIds.length || batchSaving">
            标记待发卡
          </el-button>
          <el-button size="small" type="success" @click="batchUpdateStatus('issued')" :disabled="!selectedIds.length || batchSaving">
            标记已发卡
          </el-button>
          <el-button size="small" type="danger" @click="batchUpdateStatus('void')" :disabled="!selectedIds.length || batchSaving">
            批量作废
          </el-button>
        </div>
      </div>

      <el-table :data="bills" row-key="id" v-loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="48" reserve-selection />
        <el-table-column label="入账时间" min-width="170">
          <template #default="{ row }">{{ formatDate(row.posted_at) }}</template>
        </el-table-column>
        <el-table-column label="方向" width="90">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'expense' ? 'warning' : 'success'" size="small">
              {{ row.direction === 'expense' ? '支出' : '收入' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span class="amount" :class="{ expense: row.direction === 'expense' }">
              {{ row.direction === 'expense' ? '-' : '+' }}¥{{ money(row.amount, row.amount_text) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="业务订单号" min-width="190">
          <template #default="{ row }">
            <div class="mono">{{ row.order_no || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="支付宝交易号" min-width="190">
          <template #default="{ row }">
            <div class="mono">{{ row.trade_no || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="付款方 / 说明" min-width="220">
          <template #default="{ row }">
            <div class="detail-main">{{ row.counterparty || '未知付款方' }}</div>
            <div class="detail-sub">{{ row.biz_description || row.payment_memo || '无业务说明' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="发卡状态" width="140">
          <template #default="{ row }">
            <el-tag :type="billStatusTagType(row.issue_status)" size="small">
              {{ billStatusLabel(row.issue_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="View" @click="openDetail(row)">详情</el-button>
            <el-dropdown @command="(command) => singleUpdateStatus(row, command)">
              <el-button size="small">状态</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pending">标记待发卡</el-dropdown-item>
                  <el-dropdown-item command="issued">标记已发卡</el-dropdown-item>
                  <el-dropdown-item command="void">标记作废</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="limit"
        background
        layout="prev, pager, next, jumper, ->, total"
        :total="total"
        @current-change="load" />
    </div>

    <el-drawer v-model="showDetail" title="账单详情" size="min(92vw, 760px)">
      <div v-loading="detailLoading" class="detail-panel">
        <template v-if="detail">
          <div class="detail-top">
            <div>
              <div class="detail-amount">¥{{ money(detail.amount, detail.amount_text) }}</div>
              <div class="detail-time">{{ formatDate(detail.posted_at) }}</div>
            </div>
            <el-tag :type="billStatusTagType(detail.issue_status)" size="large">
              {{ billStatusLabel(detail.issue_status) }}
            </el-tag>
          </div>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="账单方向">{{ detail.direction === 'expense' ? '支出' : '收入' }}</el-descriptions-item>
            <el-descriptions-item label="业务订单号">{{ detail.order_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="支付宝交易号">{{ detail.trade_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="付款方">{{ detail.counterparty || '-' }}</el-descriptions-item>
            <el-descriptions-item label="业务说明">{{ detail.biz_description || '-' }}</el-descriptions-item>
            <el-descriptions-item label="付款备注">{{ detail.payment_memo || '-' }}</el-descriptions-item>
            <el-descriptions-item label="备注">{{ detail.remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="账务类型">{{ detail.accounting_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发卡状态">{{ billStatusLabel(detail.issue_status) }}</el-descriptions-item>
            <el-descriptions-item label="关联订单">{{ detail.consumed_by_order_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detail.source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="采集时间">{{ formatDate(detail.captured_at) }}</el-descriptions-item>
          </el-descriptions>

          <div class="raw-block">
            <div class="raw-title">原始账单 JSON</div>
            <pre>{{ prettyRaw }}</pre>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Position, Refresh, Search, View } from '@element-plus/icons-vue'
import {
  adminAlipayBillDetail,
  adminAlipayBills,
  adminAlipayLogin,
  adminAlipayStatus,
  adminBatchAlipayBillStatus,
  adminSyncAlipayBills,
} from '../api'

const STATUS_POLL_MS = 5 * 60 * 1000

const bills = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const keyword = ref('')
const direction = ref('income')
const loading = ref(false)
const syncing = ref(false)
const openingLogin = ref(false)
const statusLoading = ref(false)
const batchSaving = ref(false)
const showDetail = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const selectedIds = ref([])
const monitorStatus = ref({
  ok: false,
  loggedIn: false,
  loginInProgress: false,
  pageUrl: '',
  title: '',
})
const lastStatusCheckedAt = ref('')

let statusTimer = null
let hasWarnedOffline = false

const issuedCount = computed(() => bills.value.filter((item) => item.issue_status === 'issued').length)
const voidCount = computed(() => bills.value.filter((item) => item.issue_status === 'void').length)
const prettyRaw = computed(() => JSON.stringify(detail.value?.raw || {}, null, 2))
const monitorIsOffline = computed(() => !monitorStatus.value.loggedIn && !monitorStatus.value.loginInProgress)
const monitorStatusLabel = computed(() => {
  if (monitorStatus.value.loggedIn) return '已登录'
  if (monitorStatus.value.loginInProgress) return '登录中'
  return '待重新登录'
})
const monitorStatusTagType = computed(() => {
  if (monitorStatus.value.loggedIn) return 'success'
  if (monitorStatus.value.loginInProgress) return 'warning'
  return 'danger'
})
const monitorStatusText = computed(() => {
  if (monitorStatus.value.loggedIn) {
    return '账单监测窗口在线，后台会继续复用当前登录态查询账单。'
  }
  if (monitorStatus.value.loginInProgress) {
    return '登录窗口已打开，先完成验证码或短信验证，登录成功后状态会自动恢复。'
  }
  return '当前没有可用登录态。账单同步和订单核验会提示重新登录。'
})
const lastStatusCheckedText = computed(() => {
  if (!lastStatusCheckedAt.value) return '尚未检查'
  return formatDate(lastStatusCheckedAt.value)
})

function money(amount, fallback) {
  const num = Number(amount)
  if (Number.isFinite(num)) return Math.abs(num).toFixed(2)
  if (fallback) return fallback
  return '0.00'
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function billStatusLabel(status) {
  const map = {
    pending: '待发卡',
    issued: '已发卡',
    void: '已作废',
  }
  return map[status] || '待发卡'
}

function billStatusTagType(status) {
  const map = {
    pending: 'info',
    issued: 'success',
    void: 'danger',
  }
  return map[status] || 'info'
}

async function load() {
  loading.value = true
  try {
    const { data } = await adminAlipayBills({
      page: page.value,
      limit: limit.value,
      query: keyword.value.trim(),
      direction: direction.value,
    })
    bills.value = data.items || []
    total.value = Number(data.total || 0)
    selectedIds.value = []
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '账单加载失败')
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function onSelectionChange(rows) {
  selectedIds.value = rows.map((item) => item.id)
}

async function loadMonitorStatus(silent = false) {
  if (!silent) statusLoading.value = true
  const previousLoggedIn = !!monitorStatus.value.loggedIn
  try {
    const { data } = await adminAlipayStatus()
    monitorStatus.value = {
      ok: !!data.ok,
      loggedIn: !!data.loggedIn,
      loginInProgress: !!data.loginInProgress,
      pageUrl: data.pageUrl || '',
      title: data.title || '',
    }
    lastStatusCheckedAt.value = new Date().toISOString()

    if (monitorStatus.value.loggedIn || monitorStatus.value.loginInProgress) {
      hasWarnedOffline = false
    } else if (previousLoggedIn && !hasWarnedOffline) {
      hasWarnedOffline = true
      ElMessage.warning('支付宝登录状态已失效，请重新登录')
    }
  } catch (e) {
    if (!silent) {
      ElMessage.error(e.response?.data?.detail || '支付宝状态检查失败')
    }
  } finally {
    statusLoading.value = false
  }
}

async function openLogin() {
  openingLogin.value = true
  try {
    const { data } = await adminAlipayLogin()
    ElMessage.success(data.message || '登录窗口已打开')
    await loadMonitorStatus(true)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '打开登录窗口失败')
  } finally {
    openingLogin.value = false
  }
}

async function syncBills() {
  syncing.value = true
  try {
    const { data } = await adminSyncAlipayBills()
    if (data.login_required) {
      ElMessage.warning('账单登录状态已失效，请先重新登录支付宝')
    } else {
      ElMessage.success(data.message || '账单同步完成')
    }
    await Promise.all([load(), loadMonitorStatus(true)])
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '账单同步失败')
  } finally {
    syncing.value = false
  }
}

async function batchUpdateStatus(status, ids = selectedIds.value) {
  if (!ids.length) {
    ElMessage.warning('请先选择账单')
    return
  }

  if (status === 'void') {
    try {
      await ElMessageBox.confirm(
        '作废后这批账单将不会再用于自动发卡匹配，确认继续？',
        '批量作废',
        {
          type: 'warning',
          confirmButtonText: '确认作废',
          cancelButtonText: '取消',
        },
      )
    } catch {
      return
    }
  }

  batchSaving.value = true
  try {
    const { data } = await adminBatchAlipayBillStatus({ ids, status })
    if (data.blocked_ids?.length) {
      ElMessage.warning(`已更新 ${data.updated} 条，${data.blocked_ids.length} 条因已关联订单未被修改`)
    } else {
      ElMessage.success(`已更新 ${data.updated} 条账单状态`)
    }
    if (
      detail.value &&
      ids.length === 1 &&
      ids[0] === detail.value.id &&
      (!data.blocked_ids || !data.blocked_ids.length)
    ) {
      detail.value.issue_status = status
    }
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '账单状态更新失败')
  } finally {
    batchSaving.value = false
  }
}

function singleUpdateStatus(row, status) {
  batchUpdateStatus(status, [row.id])
}

async function openDetail(row) {
  showDetail.value = true
  detailLoading.value = true
  detail.value = null
  try {
    const { data } = await adminAlipayBillDetail(row.id)
    detail.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '账单详情加载失败')
    showDetail.value = false
  } finally {
    detailLoading.value = false
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    loadMonitorStatus(true)
  }
}

onMounted(() => {
  load()
  loadMonitorStatus(true)
  statusTimer = window.setInterval(() => {
    loadMonitorStatus(true)
  }, STATUS_POLL_MS)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (statusTimer) {
    window.clearInterval(statusTimer)
    statusTimer = null
  }
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.bill-page {
  padding: 24px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.page-head h2 {
  margin: 0 0 6px;
}

.page-head p {
  margin: 0;
  color: var(--text-secondary);
  max-width: 820px;
  white-space: normal;
}

.head-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.monitor-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(46, 204, 113, 0.18);
}

.monitor-card.offline {
  border-color: rgba(245, 108, 108, 0.24);
}

.monitor-card + .table-shell {
  margin-top: 16px;
}

.monitor-copy {
  min-width: 0;
}

.monitor-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.monitor-title {
  font-size: 14px;
  font-weight: 700;
}

.monitor-text {
  font-size: 14px;
  line-height: 1.6;
}

.monitor-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.monitor-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.table-shell {
  padding: 14px;
  overflow: hidden;
}

.toolbar,
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toolbar {
  margin-bottom: 12px;
}

.batch-bar {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  margin-bottom: 14px;
}

.batch-meta {
  font-size: 13px;
  color: var(--text-secondary);
}

.batch-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.search-box {
  width: min(100%, 420px);
}

.direction-select {
  width: 140px;
}

.amount {
  font-weight: 800;
  color: var(--success);
}

.amount.expense {
  color: var(--warning);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  white-space: normal;
  word-break: break-all;
}

.detail-main {
  font-weight: 600;
}

.detail-sub {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  white-space: normal;
}

.detail-panel {
  min-height: 160px;
}

.detail-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-amount {
  font-size: 28px;
  font-weight: 800;
}

.detail-time {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 4px;
}

.raw-block {
  margin-top: 16px;
}

.raw-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
}

.raw-block pre {
  max-height: 320px;
  overflow: auto;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 960px) {
  .bill-page {
    padding: 16px;
  }

  .page-head,
  .toolbar,
  .batch-bar,
  .detail-top,
  .monitor-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .head-actions,
  .batch-actions,
  .monitor-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .search-box,
  .direction-select {
    width: 100%;
  }
}
</style>
