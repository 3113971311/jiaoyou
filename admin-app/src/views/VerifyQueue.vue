<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">实名审核</h2>
    <el-tabs v-model="filter" @tab-change="load">
      <el-tab-pane label="待审" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="已拒绝" name="rejected" />
    </el-tabs>
    <el-table :data="items" style="width:100%">
      <el-table-column label="用户" min-width="140">
        <template #default="{row}">
          <div style="display:flex;align-items:center;gap:8px">
            <el-avatar :src="row.avatar_url||''" :size="36" />
            <span>{{ row.nickname || row.username }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="real_name" label="姓名" min-width="80" />
      <el-table-column prop="id_card" label="身份证号" min-width="160" />
      <el-table-column label="手持照片" min-width="120">
        <template #default="{row}">
          <el-image v-if="row.id_photo" :src="verifyPhotoUrl(row.id_photo)" style="width:60px;height:60px;border-radius:8px" fit="cover" :preview-src-list="[verifyPhotoUrl(row.id_photo)]" />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="160">
        <template #default="{row}">
          <template v-if="filter==='pending'">
            <el-button size="small" type="success" @click="review(row, 'approve')">通过</el-button>
            <el-button size="small" type="danger" @click="rejectPrompt(row)">拒绝</el-button>
          </template>
          <template v-else>
            <el-button size="small" type="danger" @click="resetVerify(row)">删除记录</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next" @current-change="load" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const filter = ref('pending')
const items = ref([])
const page = ref(1)
const total = ref(0)

load()

function verifyPhotoUrl(p) {
  if (!p) return ''
  const t = localStorage.getItem('admin_token') || ''
  return `/api/verify/photo?path=${encodeURIComponent(p)}&token=${t}`
}

async function load() {
  try {
    const r = await api.get('/admin/verifications', { params: { status: filter.value, page: page.value } })
    items.value = r.data.items || []
    total.value = r.data.total || 0
  } catch {}
}

async function review(row, action) {
  try {
    await api.post(`/admin/verifications/${row.id}/review`, { action })
    ElMessage.success(action === 'approve' ? '已通过' : '已拒绝')
    load()
  } catch {}
}

async function rejectPrompt(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝认证', {
      confirmButtonText: '确认拒绝',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '填写拒绝原因...',
    })
    await api.post(`/admin/verifications/${row.id}/review`, { action: 'reject', comment: value || '' })
    ElMessage.success('已拒绝')
    load()
  } catch {}
}

async function resetVerify(row) {
  try {
    await ElMessageBox.confirm('确定删除该用户的实名认证记录？', '删除记录', { type: 'danger', confirmButtonText: '删除', cancelButtonText: '取消' })
    await api.post(`/admin/verifications/${row.id}/reset`)
    ElMessage.success('已删除')
    load()
  } catch {}
}
</script>
