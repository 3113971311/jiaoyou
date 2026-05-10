<template>
  <div class="config-page">
    <h2>系统配置</h2>
    <el-table :data="configs" style="width:100%">
      <el-table-column prop="configKey" label="KEY" width="180" />
      <el-table-column prop="valueType" label="类型" width="60" />
      <el-table-column prop="description" label="说明" width="120" />
      <el-table-column label="值">
        <template #default="{ row }">{{ row.configValue?.slice(0, 60) }}{{ row.configValue?.length > 60 ? '...' : '' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }"><el-button size="small" @click="edit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showEdit" :title="'编辑 ' + editing?.configKey">
      <el-input v-if="editing?.valueType === 'text'" v-model="editValue" type="textarea" :rows="4" />
      <el-input v-else-if="editing?.valueType === 'html'" v-model="editValue" type="textarea" :rows="12" />
      <el-input v-else v-model="editValue" type="textarea" :rows="8" placeholder="JSON 格式" />
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';

const configs = ref<any[]>([]);
const showEdit = ref(false);
const editing = ref<any>(null);
const editValue = ref('');

onMounted(load);

async function load() {
  try {
    const res = await client.get('/admin/site-configs');
    configs.value = res.data || [];
  } catch {}
}

function edit(row: any) {
  editing.value = row;
  editValue.value = row.configValue;
  showEdit.value = true;
}

async function save() {
  try {
    await client.put(`/admin/site-configs/${editing.value.configKey}`, {
      value: editValue.value,
      type: editing.value.valueType,
    });
    ElMessage.success('已保存');
    showEdit.value = false;
    load();
  } catch {}
}
</script>
