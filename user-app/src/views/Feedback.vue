<template>
  <div class="page-container rw-md mx-auto">
    <h2 style="margin-bottom:16px">问题反馈</h2>
    <div class="glass-card">
      <el-input v-model="form.title" placeholder="标题" style="margin-bottom:12px" />
      <el-input v-model="form.content" type="textarea" :rows="5" placeholder="详细描述你的问题" style="margin-bottom:12px" />
      <el-input v-model="form.contact" placeholder="联系方式（QQ/邮箱，选填）" style="margin-bottom:16px" />
      <el-button type="primary" @click="submit" :loading="sending" style="width:100%">提交反馈</el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { submitFeedback } from '../api'
const form = reactive({ title:'',content:'',contact:'' })
const sending = ref(false)
async function submit() { sending.value=true; try { await submitFeedback(form); ElMessage.success('反馈已提交'); form.title=''; form.content=''; form.contact='' } catch(e) { ElMessage.error(e.response?.data?.detail||'提交失败') } finally { sending.value=false } }
</script>
