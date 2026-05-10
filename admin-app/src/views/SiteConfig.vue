<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">系统配置</h2>
    <el-table :data="configs">
      <el-table-column prop="config_key" label="KEY" width="180" />
      <el-table-column prop="value_type" label="类型" width="60" />
      <el-table-column prop="description" label="说明" width="140" />
      <el-table-column label="值"><template #default="{row}">{{ row.config_value?.slice(0,80) }}{{ row.config_value?.length>80?'...':'' }}</template></el-table-column>
      <el-table-column label="操作" width="80"><template #default="{row}"><el-button size="small" @click="edit(row)">编辑</el-button></template></el-table-column>
    </el-table>
    <el-dialog v-model="showEdit" :title="'编辑 '+editing?.config_key" width="600px">
      <el-select v-if="editing?.config_key==='smtp_port'" v-model="editVal" style="width:100%">
        <el-option label="465 (SSL)" value="465" />
        <el-option label="587 (STARTTLS)" value="587" />
      </el-select>
      <el-input v-else-if="editing?.value_type==='text'" v-model="editVal" type="textarea" :rows="4" />
      <el-input v-else-if="editing?.value_type==='html'" v-model="editVal" type="textarea" :rows="12" />
      <el-input v-else v-model="editVal" type="textarea" :rows="8" placeholder="JSON格式" />
      <template #footer><el-button @click="showEdit=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminSiteConfigs, adminUpdateConfig } from '../api'
const configs = ref([])
const showEdit = ref(false)
const editing = ref(null)
const editVal = ref('')
load()
async function load() { try { const r=await adminSiteConfigs(); configs.value=r.data||[] } catch {} }
function edit(row) { editing.value=row; editVal.value=row.config_value; showEdit.value=true }
async function save() { try { await adminUpdateConfig(editing.value.config_key,{value:editVal.value,type:editing.value.value_type}); ElMessage.success('已保存'); showEdit.value=false; load() } catch {} }
</script>
