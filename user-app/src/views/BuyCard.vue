<template>
  <div class="faka-page">
    <!-- Standalone top bar -->
    <div class="faka-nav">
      <span class="faka-logo">拾光 · 发卡平台</span>
      <span style="font-size:13px;color:var(--text-secondary)">安全 · 自动发货</span>
    </div>
    <div class="page-container rw-lg mx-auto" style="padding-top:32px">
    <div style="text-align:center;margin-bottom:32px">
      <h2 style="font-size:28px;margin-bottom:8px">VIP 会员卡密</h2>
      <p style="color:var(--text-secondary)">选择套餐，完成支付后卡密将自动发送至您的邮箱</p>
    </div>

    <!-- Step: Plan selection -->
    <el-row :gutter="16" v-if="!devDone">
      <el-col :xs="24" :sm="12" :md="8" :lg="8" v-for="p in plans" :key="p.days" style="margin-bottom:16px">
        <div class="plan-card" :class="{ selected: selected === p.days }" @click="selected = p.days">
          <div class="plan-badge" v-if="p.badge">{{ p.badge }}</div>
          <div class="plan-days">{{ p.days }} 天</div>
          <div class="plan-desc">{{ p.desc }}</div>
          <div class="plan-price">
            <span class="plan-currency">¥</span>{{ p.price }}
          </div>
          <div class="plan-per-day">约 ¥{{ (p.price / p.days).toFixed(2) }}/天</div>
        </div>
      </el-col>
    </el-row>

    <!-- Step: Payment method & email -->
    <div v-if="!devDone" class="glass-card" style="max-width:520px;margin:0 auto">
      <div style="margin-bottom:16px">
        <div style="font-weight:600;margin-bottom:8px;font-size:15px">接收邮箱</div>
        <el-input v-model="email" placeholder="卡密将发送到此邮箱" size="large" />
      </div>
      <div style="margin-bottom:16px">
        <div style="font-weight:600;margin-bottom:8px;font-size:15px">支付方式</div>
        <div class="pay-methods">
          <div class="pay-method" :class="{ active: method === 'alipay' }" @click="method = 'alipay'">
            <span style="font-size:24px">💙</span>
            <span>支付宝</span>
          </div>
          <div class="pay-method" :class="{ active: method === 'wechat' }" @click="method = 'wechat'">
            <span style="font-size:24px">💚</span>
            <span>微信支付</span>
          </div>
        </div>
      </div>
      <div class="order-summary">
        <span>套餐：{{ selected }}天VIP</span>
        <span style="font-size:22px;font-weight:700;color:var(--danger)">¥{{ currentPlan?.price }}</span>
      </div>
      <el-button type="primary" size="large" @click="startPay" :loading="paying"
        style="width:100%;height:48px;font-size:16px;margin-top:12px" :disabled="!email">
        立即支付 ¥{{ currentPlan?.price }}
      </el-button>
    </div>

    <!-- Dev mode done / Success -->
    <div v-if="devDone" class="glass-card" style="max-width:520px;margin:0 auto;text-align:center;padding:40px">
      <div style="font-size:48px;margin-bottom:12px">✅</div>
      <h3 style="color:var(--success)">购买成功！</h3>
      <p style="margin:12px 0">卡密已发送至 <b>{{ email }}</b></p>
      <div class="glass-card" style="background:var(--card-bg);padding:16px;margin:12px 0">
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">您的卡密</div>
        <div style="font-size:20px;font-weight:700;letter-spacing:2px;font-family:monospace">{{ devCode }}</div>
      </div>
      <el-button type="primary" @click="$router.push('/vip')">去兑换VIP</el-button>
      <el-button @click="resetPay">购买其他套餐</el-button>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createPaymentOrder, alipayPay, devPay } from '../api'

const plans = [
  { days: 7, price: 9.9, desc: '体验套餐', badge: '试用' },
  { days: 30, price: 29.9, desc: '月度套餐', badge: '热门' },
  { days: 90, price: 69.9, desc: '季度套餐，省 ¥19.8' },
  { days: 180, price: 119.9, desc: '半年套餐，省 ¥58.9' },
  { days: 360, price: 199.9, desc: '年度套餐，省 ¥158.9', badge: '最值' },
]

const selected = ref(30)
const email = ref('')
const method = ref('alipay')
const paying = ref(false)
const devDone = ref(false)
const devCode = ref('')

const currentPlan = computed(() => plans.find(p => p.days === selected.value))

async function startPay() {
  if (!email.value) { ElMessage.warning('请输入邮箱'); return }
  paying.value = true
  try {
    const { data: ord } = await createPaymentOrder({ days: selected.value, email: email.value, method: method.value })

    if (method.value === 'alipay') {
      try {
        const { data: r } = await alipayPay({ order_id: ord.order_id })
        // Redirect current page to Alipay payment
        window.location.href = r.pay_url
      } catch (e) {
        if (e.response?.status === 400) {
          ElMessage.info(e.response?.data?.detail || '支付渠道未配置，使用模拟支付')
          const { data: r } = await devPay({ order_id: ord.order_id })
          devDone.value = true
          devCode.value = r.card_code
        } else { throw e }
      }
    } else {
      ElMessage.info('微信支付开发中，使用模拟支付')
      const { data: r } = await devPay({ order_id: ord.order_id })
      devDone.value = true
      devCode.value = r.card_code
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '支付失败')
  } finally {
    paying.value = false
  }
}

function resetPay() {
  devDone.value = false
  devCode.value = ''
}
</script>

<style scoped>
.faka-page { min-height: 100vh; background: var(--bg); }
.faka-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--card-border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.faka-logo {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.plan-card {
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  border: 2px solid var(--card-border);
  border-radius: var(--radius-lg);
  padding: 24px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.plan-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.plan-card.selected { border-color: var(--accent); box-shadow: 0 0 24px rgba(10, 132, 255, 0.2); }
.plan-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  color: #fff;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
}
.plan-days { font-size: 26px; font-weight: 700; }
.plan-desc { font-size: 13px; color: var(--text-secondary); }
.plan-price .plan-currency { font-size: 18px; font-weight: 600; margin-right: 2px; }
.plan-price { font-size: 36px; font-weight: 700; color: var(--text); }
.plan-per-day { font-size: 12px; color: var(--text-tertiary); }

.pay-methods { display: flex; gap: 12px; }
.pay-method {
  flex: 1;
  padding: 14px;
  border: 2px solid var(--card-border);
  border-radius: var(--radius-sm);
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.pay-method:hover { border-color: var(--accent); }
.pay-method.active { border-color: var(--accent); background: var(--accent-light); }

.order-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--card-border);
  font-size: 15px;
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
