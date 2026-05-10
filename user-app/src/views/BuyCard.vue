<template>
  <div class="page-container" style="max-width:500px;margin:0 auto">
    <h2 style="text-align:center;margin-bottom:20px">购买VIP卡密</h2>
    <el-row :gutter="12">
      <el-col :span="24" v-for="p in plans" :key="p.days" style="margin-bottom:12px">
        <div class="glass-card" :style="{border:selected===p.days?'2px solid var(--accent)':'',cursor:'pointer'}" @click="selected=p.days">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div><div style="font-size:20px;font-weight:700">{{ p.days }}天VIP</div><div style="color:var(--text-secondary);font-size:13px">{{ p.desc }}</div></div>
            <div style="font-size:24px;font-weight:700;color:#ff3b30">¥{{ p.price }}</div>
          </div>
        </div>
      </el-col>
    </el-row>
    <el-input v-model="email" placeholder="卡密将发送到此邮箱" style="margin:12px 0" />
    <el-button type="primary" size="large" @click="buy" :loading="buying" :disabled="!selected||!email" style="width:100%">立即购买</el-button>
    <div style="margin-top:16px;font-size:13px;color:var(--text-secondary)"><p>说明：选择套餐→填写邮箱→购买→卡密发送到邮箱→在VIP页兑换</p></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { buyCard } from '../api'
const plans = [{days:7,price:9.9,desc:'体验套餐'},{days:30,price:29.9,desc:'月度套餐'},{days:90,price:69.9,desc:'季度套餐'},{days:180,price:119.9,desc:'半年套餐'},{days:360,price:199.9,desc:'年度套餐'}]
const selected = ref(30)
const email = ref('')
const buying = ref(false)
async function buy() { buying.value=true; try { await buyCard({days:selected.value,email:email.value}); ElMessage.success('购买成功！卡密已发送至邮箱'); email.value='' } catch(e) { ElMessage.error(e.response?.data?.detail||'购买失败') } finally { buying.value=false } }
</script>
