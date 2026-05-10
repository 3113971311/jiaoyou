<template>
  <div class="review-page">
    <h2>图片审核</h2>
    <el-tabs v-model="filter">
      <el-tab-pane label="待审" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="已拒绝" name="rejected" />
    </el-tabs>
    <div style="margin-bottom:12px">
      <template v-if="filter === 'pending'">
        <el-button type="primary" @click="batchReview('approve')" :disabled="!selected.length">批量通过 ({{ selected.length }})</el-button>
        <el-button type="danger" @click="batchReview('reject')" :disabled="!selected.length">批量拒绝</el-button>
      </template>
      <template v-if="filter === 'rejected'">
        <el-button type="danger" @click="batchDelete" :disabled="!selected.length">批量删除 ({{ selected.length }})</el-button>
      </template>
    </div>
    <el-table :data="items" @selection-change="onSelect" style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column label="缩略图" width="100">
        <template #default="{ row }">
          <el-image :src="imageUrl(row.thumbnailUrl || row.imageUrl)" style="width:60px;height:60px" fit="cover" :preview-src-list="[imageUrl(row.imageUrl)]" />
        </template>
      </el-table-column>
      <el-table-column prop="imageType" label="类型" width="80" />
      <el-table-column label="提交者" width="120">
        <template #default="{ row }">{{ row.submitter?.nickname || row.submitter?.username }}</template>
      </el-table-column>
      <el-table-column prop="submittedAt" label="提交时间" width="160">
        <template #default="{ row }">{{ new Date(row.submittedAt).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <template v-if="filter === 'pending'">
            <el-button size="small" type="success" @click="approve(row)">通过</el-button>
            <el-button size="small" type="danger" @click="reject(row)">拒绝</el-button>
          </template>
          <template v-if="filter === 'rejected'">
            <el-button size="small" type="danger" @click="removeOne(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev, pager, next" @current-change="load" style="margin-top:16px;justify-content:center" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';

const filter = ref('pending');
const items = ref<any[]>([]);
const selected = ref<any[]>([]);

function imageUrl(p: string) { const t = localStorage.getItem('adminToken') || ''; return `/api/admin/image-preview?path=${encodeURIComponent(p)}&token=${t}`; }
const page = ref(1);
const total = ref(0);

onMounted(() => load());
watch(filter, () => { page.value = 1; load(); });

async function load() {
  try {
    const res = await client.get('/admin/review-queue', { params: { status: filter.value, page: page.value } });
    items.value = res.data.items || [];
    total.value = res.data.total;
  } catch {}
}

function onSelect(rows: any[]) { selected.value = rows; }

async function approve(row: any) {
  try {
    await client.post(`/admin/review-queue/${row.id}/approve`);
    ElMessage.success('已通过');
    load();
  } catch {}
}

async function reject(row: any) {
  try {
    const comment = prompt('拒绝原因（可选）：');
    await client.post(`/admin/review-queue/${row.id}/reject`, { comment });
    ElMessage.success('已拒绝');
    load();
  } catch {}
}

async function batchReview(action: string) {
  try {
    await client.post('/admin/review-queue/batch', { ids: selected.value.map((i) => i.id), action });
    ElMessage.success('批量操作完成');
    selected.value = [];
    load();
  } catch {}
}

async function batchDelete() {
  try {
    await client.post('/admin/review-queue/batch-delete', { ids: selected.value.map((i) => i.id) });
    ElMessage.success(`已删除 ${selected.value.length} 条`);
    selected.value = [];
    load();
  } catch {}
}

async function removeOne(row: any) {
  try {
    await client.post('/admin/review-queue/batch-delete', { ids: [row.id] });
    ElMessage.success('已删除');
    load();
  } catch {}
}
</script>
