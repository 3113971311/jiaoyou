<template>
  <div class="faka-page">
    <div class="faka-nav">
      <span class="faka-logo">拾光 · 发卡平台</span>
      <span style="font-size:clamp(11px,1vw,14px);color:var(--text-secondary)">安全 · 自动发货</span>
    </div>

    <div class="faka-content">
      <div style="text-align:center;margin-bottom:clamp(16px,2.5vw,32px)">
        <h2 style="font-size:clamp(22px,2.5vw,30px);margin-bottom:8px">VIP 会员卡密</h2>
        <p style="color:var(--text-secondary);font-size:clamp(13px,1.1vw,15px)">选择套餐，完成支付后卡密将自动发送至您的邮箱</p>
      </div>

      <!-- Success -->
      <div v-if="devDone" class="success-card glass-card">
        <div style="font-size:clamp(36px,4vw,52px);margin-bottom:12px">✅</div>
        <h3 style="color:var(--success);font-size:clamp(16px,1.5vw,20px)">购买成功！</h3>
        <p style="margin:12px 0;font-size:clamp(13px,1.1vw,15px)">卡密已发送至 <b>{{ email }}</b></p>
        <div class="glass-card" style="background:var(--card-bg);padding:clamp(12px,1.5vw,20px);margin:12px 0">
          <div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">您的卡密</div>
          <div style="font-size:clamp(16px,1.5vw,22px);font-weight:700;letter-spacing:2px;font-family:monospace">{{ devCode }}</div>
        </div>
        <el-button type="primary" @click="$router.push('/vip')">去兑换VIP</el-button>
        <el-button @click="resetPay">购买其他套餐</el-button>
      </div>

      <!-- Main: left-right layout -->
      <div v-if="!devDone" class="faka-layout">
        <!-- Left: Plan cards -->
        <div class="faka-left">
          <h4 style="margin-bottom:clamp(8px,1vw,14px);font-size:clamp(14px,1.2vw,16px)">选择套餐</h4>
          <div class="plan-list">
            <div v-for="p in plans" :key="p.days" class="plan-card" :class="{ selected: selected === p.days }" @click="selected = p.days">
              <div class="plan-badge" v-if="p.badge">{{ p.badge }}</div>
              <div class="plan-info">
                <div class="plan-days">{{ p.days }} 天</div>
                <div class="plan-desc">{{ p.desc }}</div>
              </div>
              <div class="plan-price-col">
                <div class="plan-price"><span class="plan-currency">¥</span>{{ p.price }}</div>
                <div class="plan-per-day">约 ¥{{ (p.price / p.days).toFixed(2) }}/天</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Payment -->
        <div class="faka-right">
          <h4 style="margin-bottom:clamp(8px,1vw,14px);font-size:clamp(14px,1.2vw,16px)">支付信息</h4>
          <div class="glass-card">
            <div class="form-row">
              <label class="form-label">接收邮箱</label>
              <el-input v-model="email" placeholder="卡密将发送到此邮箱" size="large" />
            </div>
            <div class="form-row">
              <label class="form-label">支付方式</label>
              <div class="pay-methods">
                <div class="pay-method active">
                  <span class="pay-icon">💙</span>
                  <span>支付宝</span>
                </div>
              </div>
            </div>
            <div class="order-summary">
              <span>套餐：{{ selected }}天VIP</span>
              <span class="order-price">¥{{ currentPlan?.price }}</span>
            </div>
            <el-button type="primary" size="large" @click="startPay" :loading="paying"
              class="pay-btn" :disabled="!email">
              立即支付 ¥{{ currentPlan?.price }}
            </el-button>
          </div>
        </div>
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
const paying = ref(false)
const devDone = ref(false)
const devCode = ref('')

const currentPlan = computed(() => plans.find(p => p.days === selected.value))

async function startPay() {
  if (!email.value) { ElMessage.warning('请输入邮箱'); return }
  paying.value = true
  try {
    const { data: ord } = await createPaymentOrder({ days: selected.value, email: email.value, method: 'alipay' })
    try {
      const { data: r } = await alipayPay({ order_id: ord.order_id })
      window.location.href = r.pay_url
    } catch (e) {
      if (e.response?.status === 400) {
        ElMessage.info(e.response?.data?.detail || '支付渠道未配置，使用模拟支付')
        const { data: r } = await devPay({ order_id: ord.order_id })
        devDone.value = true; devCode.value = r.card_code
      } else { throw e }
    }
  } catch (e) { ElMessage.error(e.response?.data?.detail || '支付失败') }
  finally { paying.value = false }
}

function resetPay() { devDone.value = false; devCode.value = '' }
</script>

<style scoped>
.faka-page { min-height: 100vh; background: var(--bg); }
.faka-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
.faka-content {
  width: min(100%, 1200px);
  margin: 0 auto;
  padding: clamp(16px, 3vw, 40px) clamp(12px, 4vw, 48px);
}

.faka-layout {
  display: flex;
  gap: clamp(16px, 2.5vw, 32px);
  align-items: flex-start;
}
.faka-left { flex: 1; min-width: 0; }
.faka-right { width: min(100%, clamp(300px, 35vw, 400px)); flex-shrink: 0; }

.plan-list { display: flex; flex-direction: column; gap: clamp(8px, 1vw, 14px); }
.plan-card {
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  border: 2px solid var(--card-border);
  border-radius: var(--radius-md);
  padding: clamp(14px, 1.5vw, 22px) clamp(16px, 1.8vw, 24px);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  gap: clamp(12px, 1.5vw, 24px);
}
.plan-card:hover { border-color: var(--accent); }
.plan-card.selected { border-color: var(--accent); box-shadow: 0 0 24px rgba(10, 132, 255, 0.2); }
.plan-badge {
  position: absolute;
  top: clamp(6px, 0.8vw, 10px);
  right: clamp(8px, 1vw, 14px);
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  color: #fff;
  font-size: clamp(9px, 0.8vw, 11px);
  padding: 2px clamp(6px, 0.8vw, 10px);
  border-radius: 8px;
  font-weight: 600;
}
.plan-info { flex: 1; min-width: 0; }
.plan-days { font-size: clamp(16px, 1.5vw, 22px); font-weight: 700; }
.plan-desc { font-size: clamp(11px, 0.9vw, 13px); color: var(--text-secondary); margin-top: 2px; }
.plan-price-col { text-align: right; flex-shrink: 0; }
.plan-price .plan-currency { font-size: clamp(14px, 1.2vw, 18px); font-weight: 600; margin-right: 2px; }
.plan-price { font-size: clamp(22px, 2vw, 30px); font-weight: 700; color: var(--text); }
.plan-per-day { font-size: clamp(10px, 0.8vw, 12px); color: var(--text-tertiary); }

.form-row { margin-bottom: clamp(12px, 1.5vw, 20px); }
.form-label { display: block; font-weight: 600; margin-bottom: clamp(4px, 0.6vw, 10px); font-size: clamp(13px, 1.1vw, 15px); }

.pay-methods { display: flex; gap: clamp(6px, 1vw, 12px); }
.pay-method {
  flex: 1;
  padding: clamp(10px, 1vw, 16px);
  border: 2px solid var(--card-border);
  border-radius: var(--radius-sm);
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(2px, 0.4vw, 6px);
  font-size: clamp(12px, 1vw, 14px);
  font-weight: 500;
  transition: all 0.2s;
}
.pay-method:hover { border-color: var(--accent); }
.pay-method.active { border-color: var(--accent); background: var(--accent-light); }
.pay-icon { font-size: clamp(18px, 1.8vw, 26px); }

.order-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(10px, 1vw, 14px) 0;
  border-top: 1px solid var(--card-border);
  font-size: clamp(13px, 1.1vw, 15px);
}
.order-price { font-size: clamp(18px, 1.8vw, 24px); font-weight: 700; color: var(--danger); }

.pay-btn {
  width: 100%;
  height: clamp(40px, 4vw, 52px);
  font-size: clamp(14px, 1.2vw, 17px);
  margin-top: clamp(8px, 1vw, 14px);
}
.success-card { max-width: min(100%, 520px); margin: 0 auto; text-align: center; }

@media (max-width: 768px) {
  .faka-layout { flex-direction: column; }
  .faka-right { width: 100%; }
}
</style>
