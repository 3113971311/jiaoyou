<template>
  <div class="faka-page">
    <div class="faka-nav">
      <span class="faka-logo">拾光 · 卡密购买</span>
      <span class="nav-subtitle">手动付款后提交订单号核验</span>
    </div>

    <div class="faka-content">
      <div class="page-title">
        <h2>VIP 会员卡密</h2>
        <p>套餐价格来自后台数据库。完成支付宝付款后，提交订单号即可自动核验并发卡到邮箱。</p>
      </div>

      <div v-if="loading" class="glass-card loading-card">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在加载套餐</span>
      </div>

      <el-empty v-else-if="!plans.length" description="暂无可购买套餐" />

      <div v-else class="faka-layout">
        <section class="faka-left">
          <div class="section-head">
            <h4>选择套餐</h4>
            <span>以管理后台当前启用价格为准</span>
          </div>
          <div class="plan-list">
            <button
              v-for="plan in plans"
              :key="plan.id"
              type="button"
              class="plan-card"
              :class="{ selected: selected === plan.days, locked: !!order && order.status !== 'paid' }"
              :disabled="!!order && order.status !== 'paid'"
              @click="selected = plan.days">
              <div class="plan-main">
                <div class="plan-title-row">
                  <div class="plan-days">{{ plan.title || `${plan.days} 天 VIP` }}</div>
                  <el-tag v-if="plan.badge" size="small" effect="dark">{{ plan.badge }}</el-tag>
                  <el-tag v-if="plan.is_first_discount" size="small" type="warning">首充 {{ Number(plan.first_discount_rate).toFixed(1) }} 折</el-tag>
                  <el-tag v-else-if="Number(plan.first_discount_rate) > 0" size="small" type="info">首充已使用</el-tag>
                </div>
                <div class="plan-desc">{{ plan.description || `${plan.days} 天会员权益，支持自动发卡` }}</div>
              </div>
              <div class="plan-price-col">
                <div
                  v-if="plan.is_first_discount && Number(plan.original_price || 0) > Number(plan.price || 0)"
                  class="plan-original-price"
                >
                  原价 ¥{{ money(plan.original_price) }}
                </div>
                <div class="plan-price">¥{{ money(plan.price) }}</div>
                <div class="plan-per-day">日均 ¥{{ perDay(plan) }}</div>
              </div>
            </button>
          </div>
        </section>

        <section class="faka-right">
          <div class="section-head">
            <h4>{{ isCompleted ? '发卡结果' : order ? '订单核验' : '创建订单' }}</h4>
            <span>{{ statusText }}</span>
          </div>

          <div v-if="isCompleted" class="glass-card success-card fade-in-up">
            <div class="success-mark">✓</div>
            <h3>核验通过</h3>
            <p>卡密已发送至 <b>{{ order?.email || email }}</b></p>
            <div class="code-card">
              <div class="code-label">卡密</div>
              <div class="code-text">{{ order?.card_code }}</div>
            </div>
            <div class="result-meta">
              <span>订单号：{{ order?.id }}</span>
              <span>金额：¥{{ money(order?.amount) }}</span>
            </div>
            <div class="result-actions">
              <el-button type="primary" size="large" @click="$router.push('/vip')">前往兑换 VIP</el-button>
              <el-button size="large" @click="resetFlow">继续购买</el-button>
            </div>
          </div>

          <div v-else class="glass-card pay-card fade-in-up">
            <template v-if="!order">
              <div class="form-row">
                <label class="form-label">接收邮箱</label>
                <el-input v-model="email" placeholder="核验成功后卡密会发送到这个邮箱" size="large" />
              </div>

              <div class="summary-card">
                <div class="summary-line">
                  <span>套餐</span>
                  <b>{{ currentPlan?.title || `${selected} 天 VIP` }}</b>
                </div>
                <div class="summary-line">
                  <span>金额</span>
                  <div class="summary-price-block">
                    <b class="accent">¥{{ money(currentPlan?.price) }}</b>
                    <div
                      v-if="currentPlan?.is_first_discount && Number(currentPlan?.original_price || 0) > Number(currentPlan?.price || 0)"
                      class="summary-origin-price"
                    >
                      原价 ¥{{ money(currentPlan?.original_price) }}
                    </div>
                  </div>
                </div>
                <div v-if="currentPlan?.is_first_discount" class="summary-line">
                  <span>首充优惠</span>
                  <b class="discount-text">已为当前账号应用 {{ Number(currentPlan.first_discount_rate).toFixed(1) }} 折</b>
                </div>
                <div v-else-if="currentPlan && Number(currentPlan.first_discount_rate) > 0" class="summary-line">
                  <span>首充优惠</span>
                  <b class="used-discount-text">当前账号的该套餐首充已使用</b>
                </div>
                <div class="summary-line">
                  <span>发货方式</span>
                  <b>邮箱自动发卡</b>
                </div>
              </div>

              <el-alert
                v-if="currentPlan && !currentPlan.payment_qr_url"
                title="当前套餐暂未配置收款码，请联系管理员先在套餐设置中上传对应二维码"
                type="warning"
                :closable="false"
                show-icon
                class="status-alert" />

              <div class="tip-block">
                <div class="tip-title">购买流程</div>
                <ol class="tip-list">
                  <li>先创建待核验订单。</li>
                  <li>按订单金额完成支付宝付款。</li>
                  <li>在支付宝账单详情复制订单号后提交核验。</li>
                </ol>
              </div>

              <el-button
                type="primary"
                size="large"
                class="pay-btn"
                :loading="creatingOrder"
                :disabled="!email || !currentPlan || !currentPlan.payment_qr_url"
                @click="createOrderFlow">
                生成待核验订单
              </el-button>
            </template>

            <template v-else>
              <div class="pending-header">
                <div>
                  <div class="pending-title">待核验订单</div>
                  <div class="pending-subtitle">请在支付宝完成付款后，再提交订单号</div>
                </div>
                <el-tag :type="statusType(order.status)" size="large">{{ statusLabel(order.status) }}</el-tag>
              </div>

              <div class="amount-panel">
                <div class="amount-label">需支付金额</div>
                <div class="amount-value">¥{{ money(order.amount) }}</div>
                <div v-if="order.is_first_discount" class="amount-hint">
                  {{ currentPlan?.title || `${order.days} 天 VIP` }} · 首充 {{ Number(order.discount_rate || 0).toFixed(1) }} 折
                </div>
                <div v-else class="amount-hint">{{ currentPlan?.title || `${order.days} 天 VIP` }}</div>
                <div v-if="order.is_first_discount" class="amount-discount-note">
                  原价 ¥{{ money(order.original_amount || order.amount) }}，本次首充优惠后实付 ¥{{ money(order.amount) }}
                </div>
              </div>

              <div class="qr-payment-panel">
                <div class="qr-copy">
                  <div class="qr-copy-title">请扫码付款</div>
                  <div class="qr-copy-subtitle">请使用这个套餐对应的支付宝收款码付款，付款金额必须与订单金额完全一致。</div>
                </div>
                <div v-if="currentQrUrl" class="qr-payment-body">
                  <el-image :src="currentQrUrl" :preview-src-list="[currentQrUrl]" fit="contain" class="payment-qr-image" />
                </div>
                <el-alert
                  v-else
                  title="当前订单没有可用收款码，请联系管理员检查套餐配置"
                  type="error"
                  :closable="false"
                  show-icon />
              </div>

              <div class="order-grid">
                <div class="order-item">
                  <span>订单号</span>
                  <b>{{ order.id }}</b>
                </div>
                <div class="order-item">
                  <span>邮箱</span>
                  <b>{{ order.email }}</b>
                </div>
                <div class="order-item">
                  <span>套餐</span>
                  <b>{{ order.days }} 天 VIP</b>
                </div>
                <div class="order-item">
                  <span>状态</span>
                  <b>{{ order.verification_message || '等待核验' }}</b>
                </div>
              </div>

              <el-alert
                v-if="orderMessage"
                :title="orderMessage"
                :type="loginRequired ? 'error' : 'info'"
                :closable="false"
                show-icon
                class="status-alert" />

              <div class="tip-block pending-tips">
                <div class="tip-title">订单号说明</div>
                <ol class="tip-list">
                  <li>打开支付宝账单详情，复制业务订单号或支付宝交易号。</li>
                  <li>系统会每 3 秒轮询一次账单，最多等待 1 分钟。</li>
                  <li>匹配规则为“订单号 + 金额”同时命中才会发卡。</li>
                </ol>
              </div>

              <div class="form-row">
                <label class="form-label">支付宝订单号</label>
                <el-input
                  v-model="submittedOrderNo"
                  placeholder="粘贴支付宝业务订单号或交易号"
                  size="large"
                  :disabled="verifying" />
              </div>

              <div class="action-row">
                <el-button
                  type="primary"
                  size="large"
                  class="verify-btn"
                  :loading="verifying"
                  :disabled="!submittedOrderNo"
                  @click="verifyOrder">
                  提交订单号并核验
                </el-button>
                <el-button size="large" :icon="Refresh" @click="refreshOrder" :disabled="verifying">刷新订单</el-button>
                <el-button size="large" @click="resetFlow" :disabled="verifying">重新下单</el-button>
              </div>
            </template>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { createPaymentOrder, getPaymentOrder, submitPaymentOrderNo, vipPlans } from '../api'

const plans = ref([])
const selected = ref(null)
const email = ref('')
const loading = ref(false)
const creatingOrder = ref(false)
const verifying = ref(false)
const order = ref(null)
const submittedOrderNo = ref('')
const loginRequired = ref(false)

const currentPlan = computed(() => {
  if (!plans.value.length) return null
  const dayValue = order.value?.days ?? selected.value
  return plans.value.find(item => item.days === dayValue) || null
})

const isCompleted = computed(() => order.value?.status === 'paid' && !!order.value?.card_code)
const orderMessage = computed(() => order.value?.verification_message || '')
const currentQrUrl = computed(() => order.value?.payment_qr_url || currentPlan.value?.payment_qr_url || '')
const statusText = computed(() => {
  if (isCompleted.value) return '已自动发卡'
  if (order.value) return '等待提交订单号'
  return '先创建订单再付款'
})

function money(value) {
  return Number(value || 0).toFixed(2)
}

function perDay(plan) {
  if (!plan?.days) return '0.00'
  return (Number(plan.price || 0) / plan.days).toFixed(2)
}

function statusLabel(status) {
  const map = {
    pending: '待提交',
    verifying: '核验中',
    paid: '已完成',
  }
  return map[status] || status || '待处理'
}

function statusType(status) {
  const map = {
    pending: 'warning',
    verifying: 'primary',
    paid: 'success',
  }
  return map[status] || 'info'
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim())
}

async function loadPlans() {
  loading.value = true
  try {
    const { data } = await vipPlans()
    plans.value = data.items || []
    if (!selected.value) selected.value = plans.value[0]?.days ?? null
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '套餐加载失败')
  } finally {
    loading.value = false
  }
}

async function createOrderFlow() {
  if (!currentPlan.value) {
    ElMessage.warning('请先选择套餐')
    return
  }
  if (!currentPlan.value.payment_qr_url) {
    ElMessage.warning('当前套餐暂未配置收款码')
    return
  }
  if (!isValidEmail(email.value)) {
    ElMessage.warning('请输入正确的邮箱地址')
    return
  }

  creatingOrder.value = true
  try {
    const { data } = await createPaymentOrder({
      days: selected.value,
      email: email.value.trim(),
      method: 'alipay',
    })
    const detail = await getPaymentOrder(data.order_id)
    order.value = {
      ...detail.data,
      email: email.value.trim(),
    }
    loginRequired.value = false
    submittedOrderNo.value = order.value.submitted_order_no || ''
    ElMessage.success('订单已创建，请完成支付宝付款后提交订单号')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建订单失败')
  } finally {
    creatingOrder.value = false
  }
}

async function refreshOrder() {
  if (!order.value?.id) return
  try {
    const { data } = await getPaymentOrder(order.value.id)
    order.value = {
      ...data,
      email: order.value.email || email.value.trim(),
    }
    submittedOrderNo.value = data.submitted_order_no || submittedOrderNo.value
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '订单刷新失败')
  }
}

async function verifyOrder() {
  if (!order.value?.id) return
  if (!submittedOrderNo.value.trim()) {
    ElMessage.warning('请输入支付宝订单号')
    return
  }

  verifying.value = true
  loginRequired.value = false
  try {
    const { data } = await submitPaymentOrderNo(order.value.id, { order_no: submittedOrderNo.value.trim() })
    if (data.matched) {
      order.value = {
        ...order.value,
        card_code: data.card_code || order.value?.card_code,
        status: 'paid',
        verification_message: data.message || '支付成功，卡密已发送至邮箱',
      }
      try {
        await refreshOrder()
      } catch {
        /* keep optimistic success state */
      }
      ElMessage.success(data.message || '核验通过')
      return
    }

    loginRequired.value = !!data.login_required
    order.value = {
      ...order.value,
      status: 'pending',
      submitted_order_no: submittedOrderNo.value.trim(),
      verification_message: data.message || '未找到订单',
    }
    ElMessage.warning(order.value.verification_message)
  } catch (e) {
    const message = e.response?.data?.detail || '核验失败'
    order.value = {
      ...order.value,
      status: 'pending',
      submitted_order_no: submittedOrderNo.value.trim(),
      verification_message: message,
    }
    ElMessage.error(message)
  } finally {
    verifying.value = false
  }
}

function resetFlow() {
  order.value = null
  submittedOrderNo.value = ''
  loginRequired.value = false
}

loadPlans()
</script>

<style scoped>
.faka-page { min-height: 100vh; background: var(--bg); }
.faka-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: clamp(8px, 1.2vw, 14px) clamp(16px, 4vw, 48px);
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--card-border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.faka-logo {
  font-size: clamp(16px, 1.5vw, 20px);
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-subtitle {
  font-size: clamp(11px, 1vw, 14px);
  color: var(--text-secondary);
  text-align: right;
}
.faka-content {
  width: min(100%, 1220px);
  margin: 0 auto;
  padding: clamp(18px, 3vw, 42px) clamp(14px, 4vw, 48px);
}
.page-title {
  text-align: center;
  margin-bottom: clamp(18px, 2.6vw, 34px);
}
.page-title h2 {
  font-size: clamp(24px, 2.5vw, 32px);
  margin-bottom: 8px;
}
.page-title p {
  color: var(--text-secondary);
  max-width: 760px;
  margin: 0 auto;
  white-space: normal;
}
.faka-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 420px);
  gap: clamp(16px, 2.5vw, 30px);
  align-items: start;
}
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.section-head h4 {
  font-size: 16px;
}
.section-head span {
  font-size: 12px;
  color: var(--text-secondary);
}
.plan-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.plan-card {
  width: 100%;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: left;
}
.plan-card:hover {
  border-color: rgba(10, 132, 255, 0.55);
  transform: translateY(-1px);
}
.plan-card.selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px rgba(10, 132, 255, 0.24), 0 14px 30px rgba(10, 132, 255, 0.08);
}
.plan-card.locked {
  opacity: 0.72;
  cursor: not-allowed;
}
.plan-main {
  min-width: 0;
  flex: 1;
}
.plan-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.plan-days {
  font-size: clamp(16px, 1.5vw, 20px);
  font-weight: 700;
}
.plan-desc {
  color: var(--text-secondary);
  font-size: 13px;
  white-space: normal;
}
.plan-price-col {
  text-align: right;
  flex-shrink: 0;
}
.plan-original-price {
  font-size: 12px;
  color: var(--text-tertiary);
  text-decoration: line-through;
  margin-bottom: 4px;
}
.plan-price {
  font-size: clamp(24px, 2vw, 30px);
  font-weight: 800;
}
.plan-per-day {
  font-size: 12px;
  color: var(--text-tertiary);
}
.pay-card {
  padding: 20px;
}
.form-row {
  margin-bottom: 18px;
}
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}
.summary-card {
  border: 1px solid var(--card-border);
  border-radius: 14px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  margin-bottom: 16px;
}
.summary-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
}
.summary-line + .summary-line {
  margin-top: 10px;
}
.summary-line span {
  color: var(--text-secondary);
}
.summary-price-block {
  text-align: right;
}
.summary-origin-price {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
  text-decoration: line-through;
}
.summary-line b,
.accent {
  color: var(--text);
}
.accent {
  font-weight: 800;
}
.discount-text {
  color: var(--warning);
}
.used-discount-text {
  color: var(--text-tertiary);
}
.tip-block {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 18px;
}
.tip-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
}
.tip-list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
}
.tip-list li {
  white-space: normal;
}
.tip-list li + li {
  margin-top: 6px;
}
.pay-btn,
.verify-btn {
  width: 100%;
  min-height: 46px;
}
.pending-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}
.pending-title {
  font-size: 18px;
  font-weight: 700;
}
.pending-subtitle {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 4px;
  white-space: normal;
}
.amount-panel {
  background: linear-gradient(180deg, rgba(10, 132, 255, 0.15), rgba(10, 132, 255, 0.04));
  border: 1px solid rgba(10, 132, 255, 0.24);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 16px;
}
.amount-label {
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: 4px;
}
.amount-value {
  font-size: clamp(30px, 2.5vw, 38px);
  line-height: 1.1;
  font-weight: 800;
}
.amount-hint {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}
.amount-discount-note {
  margin-top: 8px;
  font-size: 12px;
  color: var(--warning);
}
.qr-payment-panel {
  margin-bottom: 16px;
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.025);
}
.qr-copy-title {
  font-size: 16px;
  font-weight: 700;
}
.qr-copy-subtitle {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: normal;
}
.qr-payment-body {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}
.payment-qr-image {
  width: min(100%, 260px);
  aspect-ratio: 1 / 1;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--card-border);
  background: #fff;
}
.order-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.order-item {
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
}
.order-item span {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}
.order-item b {
  display: block;
  white-space: normal;
  word-break: break-all;
  font-size: 13px;
}
.status-alert {
  margin-bottom: 14px;
}
.pending-tips {
  margin-bottom: 16px;
}
.action-row {
  display: grid;
  grid-template-columns: 1fr 120px 120px;
  gap: 10px;
}
.success-card {
  text-align: center;
}
.success-mark {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  margin: 0 auto 14px;
  display: grid;
  place-items: center;
  font-size: 28px;
  font-weight: 800;
  background: rgba(48, 209, 88, 0.14);
  color: var(--success);
}
.success-card h3 {
  font-size: 22px;
  margin-bottom: 8px;
}
.success-card p {
  color: var(--text-secondary);
  margin-bottom: 16px;
  white-space: normal;
}
.code-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}
.code-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.code-text {
  font-size: clamp(18px, 2vw, 24px);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 1px;
  word-break: break-all;
}
.result-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 18px;
}
.result-meta span {
  white-space: normal;
}
.result-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
.loading-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: var(--text-secondary);
}

@media (max-width: 980px) {
  .faka-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .faka-nav,
  .section-head,
  .pending-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .plan-card,
  .order-grid,
  .action-row {
    grid-template-columns: 1fr;
  }
  .plan-card {
    display: block;
  }
  .plan-price-col {
    text-align: left;
    margin-top: 12px;
  }
  .action-row {
    display: flex;
    flex-direction: column;
  }
}
</style>
