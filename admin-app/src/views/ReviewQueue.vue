<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">图片审核</h2>
    <el-tabs v-model="filter" @tab-change="onFilterChange">
      <el-tab-pane label="待审" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="已拒绝" name="rejected" />
    </el-tabs>
    <div style="margin-bottom:12px;display:flex;gap:8px">
      <template v-if="filter==='pending'">
        <el-button type="success" @click="batchApprove" :disabled="!selected.length">批量通过 ({{ selected.length }})</el-button>
        <el-button type="danger" @click="batchReject" :disabled="!selected.length">批量拒绝 ({{ selected.length }})</el-button>
      </template>
      <template v-if="filter==='rejected'">
        <el-button type="danger" @click="batchDelete" :disabled="!selected.length">批量删除 ({{ selected.length }})</el-button>
      </template>
    </div>
    <el-table :data="items" @selection-change="onSelect">
      <el-table-column type="selection" min-width="35" />
      <el-table-column label="缩略图" min-width="80">
        <template #default="{row}"><el-image :src="imgUrl(row.thumbnail_url||row.image_url)" style="width:clamp(40px,8vw,60px);height:clamp(40px,8vw,60px);border-radius:8px" fit="cover" :preview-src-list="[imgUrl(row.image_url)]" /></template>
      </el-table-column>
      <el-table-column prop="image_type" label="类型" min-width="60" />
      <el-table-column label="提交时间" min-width="130"><template #default="{row}">{{ new Date(row.submitted_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="操作" min-width="140">
        <template #default="{row}">
          <template v-if="filter==='pending'">
            <el-button size="small" type="success" @click="approve(row)">通过</el-button>
            <el-button size="small" type="danger" @click="reject(row)">拒绝</el-button>
          </template>
          <template v-if="filter==='rejected'">
            <el-button size="small" type="danger" @click="removeOne(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next" @current-change="load" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminReviewQueue, adminApprove, adminReject, adminBatchReview, adminBatchDelete, adminImageUrl } from '../api'

const filter = ref('pending')
const items = ref([])
const selected = ref([])
const page = ref(1)
const total = ref(0)

load()
function imgUrl(p) { return adminImageUrl(p) }
async function load() {
  try { const r = await adminReviewQueue({ status: filter.value, page: page.value }); items.value = r.data.items||[]; total.value = r.data.total||0 } catch {}
}
function onFilterChange() { page.value=1; load() }
function onSelect(rows) { selected.value = rows }
async function approve(row) { try { await adminApprove(row.id); ElMessage.success('已通过'); load() } catch {} }
async function reject(row) { try { await adminReject(row.id, {}); ElMessage.success('已拒绝'); load() } catch {} }
async function removeOne(row) { try { await adminBatchDelete({ ids: [row.id] }); ElMessage.success('已删除'); load() } catch {} }
async function batchApprove() { try { await adminBatchReview({ ids: selected.value.map(i=>i.id), action:'approve' }); ElMessage.success('批量通过'); selected.value=[]; load() } catch {} }
async function batchReject() { try { await adminBatchReview({ ids: selected.value.map(i=>i.id), action:'reject' }); ElMessage.success('批量拒绝'); selected.value=[]; load() } catch {} }
async function batchDelete() { try { await adminBatchDelete({ ids: selected.value.map(i=>i.id) }); ElMessage.success('已删除'); selected.value=[]; load() } catch {} }
</script>
