<template>
  <div class="page-container rw-md mx-auto">
    <h2 style="text-align:center;margin-bottom:20px">VIP 会员</h2>
    <div class="glass-card" style="text-align:center;margin-bottom:16px">
      <h3 v-if="auth.isVip" style="color:var(--success)">VIP 已开通</h3><h3 v-else style="color:var(--text-secondary)">未开通VIP</h3>
      <p v-if="auth.isVip" style="font-size:14px;color:var(--text-secondary)">到期：{{ new Date(auth.user.vip_expires_at).toLocaleDateString() }}（剩余{{remaining}}天）</p>
      <p v-else style="font-size:14px;color:var(--text-secondary)">开通VIP解锁所有功能</p>
    </div>
    <div class="glass-card">
      <h4>卡密兑换</h4>
      <div style="display:flex;gap:8px;margin-top:8px"><el-input v-model="cardCode" placeholder="输入卡密 XXXX-XXXX-XXXX-XXXX" maxlength="19" /><el-button type="primary" @click="redeem" :loading="redeeming">兑换</el-button></div>
    </div>
    <div style="text-align:center;margin-top:16px"><el-button type="warning" @click="$router.push('/buy-card')">购买VIP卡密 →</el-button></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { redeemCard } from '../api'
const auth = useAuthStore()
const cardCode = ref('')
const redeeming = ref(false)
const remaining = computed(()=>{ if(!auth.user?.vip_expires_at) return 0; return Math.max(0,Math.ceil((new Date(auth.user.vip_expires_at)-new Date())/(24*60*60*1000))) })
async function redeem() { if(!cardCode.value) return; redeeming.value=true; try { const r=await redeemCard({code:cardCode.value}); ElMessage.success(`兑换成功！+${r.data.days}天VIP`); cardCode.value=''; await auth.fetchMe() } catch(e) { ElMessage.error(e.response?.data?.detail||'兑换失败') } finally { redeeming.value=false } }
</script>
