<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">举报处理</h2>
    <el-table :data="items">
      <el-table-column prop="reporter_id" label="举报人ID" width="200" />
      <el-table-column prop="target_type" label="类型" width="80" />
      <el-table-column prop="target_id" label="对象ID" width="200" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='pending'?'warning':row.status==='handled'?'success':'info'" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="140" v-if="filter==='pending'">
        <template #default="{row}"><el-button size="small" type="success" @click="handle(row,'handle')">处理</el-button><el-button size="small" type="info" @click="handle(row,'dismiss')">驳回</el-button></template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminReports, adminHandleReport } from '../api'
const filter = ref('pending')
const items = ref([])
load()
async function load() { try { const r=await adminReports({status:filter.value}); items.value=r.data.items||[] } catch {} }
async function handle(row, action) { try { await adminHandleReport(row.id,{action}); ElMessage.success('已处理'); load() } catch {} }
</script>
