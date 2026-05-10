<template>
  <div class="reports-page">
    <h2>举报处理</h2>
    <el-table :data="items" style="width:100%">
      <el-table-column label="举报人" width="100">
        <template #default="{ row }">{{ row.reporter?.username }}</template>
      </el-table-column>
      <el-table-column prop="targetType" label="对象类型" width="80" />
      <el-table-column prop="targetId" label="对象ID" width="200" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column prop="status" label="状态" width="80" />
      <el-table-column label="操作" width="150" v-if="filter === 'pending'">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="handle(row, 'handle')">处理</el-button>
          <el-button size="small" type="info" @click="handle(row, 'dismiss')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';

const filter = ref('pending');
const items = ref<any[]>([]);

onMounted(async () => {
  try {
    const res = await client.get('/admin/reports', { params: { status: filter.value } });
    items.value = res.data.items || [];
  } catch {}
});

async function handle(row: any, action: string) {
  try {
    await client.post(`/admin/reports/${row.id}/handle`, { action });
    ElMessage.success('已处理');
    row.status = action === 'dismiss' ? 'dismissed' : 'handled';
  } catch {}
}
</script>
