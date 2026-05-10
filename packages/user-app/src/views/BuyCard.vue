<template>
  <div class="page">
    <van-nav-bar title="购买VIP卡密" left-arrow fixed placeholder @click-left="$router.back()" />
    <div class="content">
      <h3 style="text-align:center;margin:16px 0">选择VIP套餐</h3>
      <van-grid :column-num="2" gutter="12">
        <van-grid-item v-for="plan in plans" :key="plan.days" :class="{ selected: selectedPlan === plan.days }" @click="selectedPlan = plan.days">
          <div class="plan-card" :style="{ borderColor: selectedPlan === plan.days ? '#1989fa' : '#eee' }">
            <div class="plan-days">{{ plan.days }}天</div>
            <div class="plan-price">¥{{ plan.price }}</div>
            <div class="plan-desc">{{ plan.desc }}</div>
          </div>
        </van-grid-item>
      </van-grid>

      <van-cell-group inset style="margin-top:20px">
        <van-field v-model="email" label="接收邮箱" placeholder="卡密将发送到此邮箱" :rules="[{ required: true, pattern: /^\S+@\S+$/ }]" />
      </van-cell-group>

      <div style="padding:20px 16px">
        <van-button block type="primary" size="large" @click="buyCard" :loading="buying" :disabled="!selectedPlan || !email">
          立即购买 - ¥{{ selectedPlan ? plans.find(p => p.days === selectedPlan)?.price : '--' }}
        </van-button>
      </div>

      <div class="tips">
        <p>购买说明：</p>
        <ul>
          <li>选择VIP套餐并填写接收邮箱</li>
          <li>卡密将在支付成功后发送到你的邮箱</li>
          <li>收到卡密后在「VIP会员」页面兑换即可</li>
          <li>如有问题请联系站长</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { showSuccessToast, showFailToast } from 'vant';
import client from '../api/client';

const plans = [
  { days: 7, price: 9.9, desc: '体验套餐' },
  { days: 30, price: 29.9, desc: '月度套餐' },
  { days: 90, price: 69.9, desc: '季度套餐' },
  { days: 180, price: 119.9, desc: '半年套餐' },
  { days: 360, price: 199.9, desc: '年度套餐' },
];

const selectedPlan = ref(30);
const email = ref('');
const buying = ref(false);

async function buyCard() {
  if (!selectedPlan.value || !email.value) return;
  buying.value = true;
  try {
    const res = await client.post('/cards/buy', { days: selectedPlan.value, email: email.value });
    showSuccessToast(`购买成功！卡密已发送至 ${email.value}`);
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '购买失败');
  } finally { buying.value = false; }
}
</script>

<style scoped>
.page { background: #f7f8fa; min-height: 100vh; }
.content { padding-bottom: 30px; }
.plan-card { border: 2px solid #eee; border-radius: 12px; padding: 20px 10px; text-align: center; transition: all 0.2s; }
.plan-days { font-size: 24px; font-weight: bold; color: #1989fa; }
.plan-price { font-size: 20px; color: #ff6b6b; margin: 6px 0; }
.plan-desc { font-size: 12px; color: #999; }
.selected .plan-card { border-color: #1989fa; background: #f0f7ff; }
.tips { padding: 20px; font-size: 13px; color: #999; }
.tips ul { padding-left: 20px; }
.tips li { margin: 4px 0; }
</style>
