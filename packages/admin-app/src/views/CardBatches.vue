<template>
  <div class="card-page">
    <h2>发卡管理</h2>
    <el-button type="primary" @click="showGen = true" style="margin-bottom:16px">生成卡密</el-button>

    <el-table :data="batches" style="width:100%">
      <el-table-column prop="batchName" label="批次名称" />
      <el-table-column prop="denominationDays" label="面值(天)" width="80" />
      <el-table-column prop="expireDays" label="有效期(天)" width="90" />
      <el-table-column prop="quantity" label="数量" width="60" />
      <el-table-column label="已用/未用/过期" width="150">
        <template #default="{ row }">{{ row.used }} / {{ row.unused }} / {{ row.expired }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="info" @click="showDetail(row)">详情</el-button>
          <el-button size="small" @click="exportBatch(row)">导出</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 批次详情弹窗 -->
    <el-dialog v-model="showDetailDialog" :title="detailBatch?.batchName" width="800px">
      <div style="margin-bottom:12px;display:flex;gap:8px">
        <el-select v-model="detailFilter" @change="loadDetail" style="width:100px">
          <el-option label="全部" value="" />
          <el-option label="未使用" value="unused" />
          <el-option label="已使用" value="used" />
          <el-option label="已过期" value="expired" />
        </el-select>
        <el-button @click="copyAllVisible">一键复制当前页</el-button>
      </div>
      <el-table :data="detailItems" max-height="400">
        <el-table-column prop="cardCode" label="卡密" width="220">
          <template #default="{ row }">
            <code>{{ row.cardCode }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="denominationDays" label="面值" width="60" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'unused' ? 'success' : row.status === 'used' ? 'info' : 'warning'" size="small">
              {{ row.status === 'unused' ? '未用' : row.status === 'used' ? '已用' : '过期' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="过期时间" width="160">
          <template #default="{ row }">{{ new Date(row.expiresAt).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="copyOne(row.cardCode)">复制</el-button>
            <el-button size="small" type="danger" @click="deleteCard(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="detailPage" :total="detailTotal" :page-size="30" layout="prev,pager,next" @current-change="loadDetail" style="margin-top:12px;justify-content:center" />
    </el-dialog>

    <!-- 生成弹窗 -->
    <el-dialog v-model="showGen" title="生成卡密批次">
      <el-form :model="gen">
        <el-form-item label="批次名称"><el-input v-model="gen.batchName" /></el-form-item>
        <el-form-item label="面值天数（给用户加多少天VIP）"><el-input-number v-model="gen.denominationDays" :min="1" /></el-form-item>
        <el-form-item label="销毁天数">
          <el-radio-group v-model="gen.expireDays">
            <el-radio-button :value="3">3天</el-radio-button>
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
            <el-radio-button :value="90">90天</el-radio-button>
            <el-radio-button :value="180">180天</el-radio-button>
            <el-radio-button :value="360">360天</el-radio-button>
          </el-radio-group>
          <el-input-number v-model="gen.expireDays" :min="1" placeholder="自定义" style="margin-left:8px" />
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="gen.quantity" :min="1" :max="10000" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="gen.note" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGen = false">取消</el-button>
        <el-button type="primary" @click="doGenerate" :loading="genLoading">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';

const batches = ref<any[]>([]);
const showGen = ref(false);
const genLoading = ref(false);
const gen = reactive({ batchName: '', denominationDays: 30, expireDays: 7, quantity: 10, note: '' });

// 详情弹窗
const showDetailDialog = ref(false);
const detailBatch = ref<any>(null);
const detailItems = ref<any[]>([]);
const detailTotal = ref(0);
const detailPage = ref(1);
const detailFilter = ref('');

onMounted(loadBatches);

async function loadBatches() {
  const res = await client.get('/admin/cards/batches');
  batches.value = res.data.items || [];
}

async function doGenerate() {
  genLoading.value = true;
  try {
    const res = await client.post('/admin/cards/generate', gen);
    ElMessage.success(`生成成功！${res.data.quantity} 张卡密`);
    showGen.value = false;
    loadBatches();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || '生成失败');
  } finally { genLoading.value = false; }
}

async function showDetail(row: any) {
  detailBatch.value = row;
  detailPage.value = 1;
  detailFilter.value = '';
  showDetailDialog.value = true;
  await loadDetail();
}

async function loadDetail() {
  if (!detailBatch.value) return;
  const res = await client.get(`/admin/cards/batches/${detailBatch.value.id}`, {
    params: { page: detailPage.value, limit: 30, status: detailFilter.value || undefined },
  });
  detailItems.value = res.data.items || [];
  detailTotal.value = res.data.total;
}

function copyOne(code: string) {
  navigator.clipboard.writeText(code).then(() => ElMessage.success('已复制')).catch(() => ElMessage.info(code));
}

async function deleteCard(row: any) {
  try {
    await client.delete(`/admin/cards/${row.id}`);
    ElMessage.success('已删除');
    loadDetail();
    loadBatches();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || '删除失败');
  }
}

function copyAllVisible() {
  const codes = detailItems.value.map((c) => c.cardCode).join('\n');
  navigator.clipboard.writeText(codes).then(() => ElMessage.success(`已复制 ${detailItems.value.length} 张卡密`)).catch(() => ElMessage.info('复制失败，请手动选择'));
}

async function exportBatch(row: any) {
  const res = await client.get(`/admin/cards/batches/${row.id}/export`, { responseType: 'blob' });
  const url = URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `${row.batchName}.csv`;
  a.click();
  ElMessage.success('导出成功');
}
</script>
