<template>
  <div class="vip-page">
    <van-nav-bar title="VIP 会员" fixed placeholder left-arrow @click-left="$router.back()" />
    <div class="vip-content">
      <div class="vip-status" v-if="auth.isVip">
        <van-icon name="vip-card" size="40" color="#ff6b6b" />
        <h3>VIP 会员</h3>
        <p>到期时间：{{ new Date(auth.user?.vipExpiresAt).toLocaleString() }}</p>
        <p>剩余 {{ daysRemaining }} 天</p>
      </div>
      <div class="vip-status" v-else>
        <h3>开通 VIP 解锁全部功能</h3>
        <p>每日匹配5次 · 动态3条 · 聊天发图 · 更多特权</p>
      </div>

      <div class="buy-link" @click="$router.push('/buy-card')">
        <van-icon name="shop-o" /> 购买VIP卡密 → 支持各种套餐，卡密发送到邮箱
      </div>

      <van-cell-group inset title="卡密充值">
        <van-field v-model="cardCode" label="卡密" placeholder="输入16位卡密，格式 XXXX-XXXX-XXXX-XXXX" maxlength="19" />
        <div class="redeem-btn"><van-button block type="primary" @click="redeem" :loading="redeeming">立即兑换</van-button></div>
      </van-cell-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { showSuccessToast, showFailToast } from 'vant';
import { useAuthStore } from '../stores/auth';
import client from '../api/client';

const auth = useAuthStore();
const cardCode = ref('');
const redeeming = ref(false);

const daysRemaining = computed(() => {
  if (!auth.user?.vipExpiresAt) return 0;
  const diff = new Date(auth.user.vipExpiresAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (24 * 60 * 60 * 1000)));
});

async function redeem() {
  if (!cardCode.value.trim()) return;
  redeeming.value = true;
  try {
    const res = await client.post('/cards/redeem', { code: cardCode.value.trim() });
    showSuccessToast(`兑换成功！获得 ${res.data.days} 天 VIP`);
    cardCode.value = '';
    await auth.fetchMe();
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '兑换失败');
  } finally { redeeming.value = false; }
}
</script>

<style scoped>
.vip-page { background: #f7f8fa; min-height: 100vh; }
.vip-content { padding: 20px 0; }
.vip-status { text-align: center; padding: 30px 20px; background: #fff; margin-bottom: 16px; }
.vip-status h3 { color: #ff6b6b; }
.buy-link { margin: 16px; padding: 14px; background: linear-gradient(135deg, #ff6b6b, #ff8e53); color: #fff; border-radius: 10px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 14px; cursor: pointer; }
.redeem-btn { padding: 16px; }
</style>
