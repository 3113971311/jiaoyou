<template>
  <div class="sw-page">
    <h2>敏感词管理</h2>
    <div style="margin-bottom:12px;display:flex;gap:8px">
      <el-input v-model="newWord.word" placeholder="输入敏感词" style="width:200px" />
      <el-select v-model="newWord.level" style="width:100px">
        <el-option label="替换" value="replace" />
        <el-option label="阻止" value="block" />
      </el-select>
      <el-button type="primary" @click="add">添加</el-button>
    </div>
    <el-table :data="words" style="width:100%">
      <el-table-column prop="word" label="敏感词" />
      <el-table-column prop="level" label="等级" width="80">
        <template #default="{ row }"><el-tag :type="row.level === 'block' ? 'danger' : 'warning'">{{ row.level }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }"><el-button size="small" type="danger" @click="remove(row)">删除</el-button></template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';

const words = ref<any[]>([]);
const newWord = reactive({ word: '', level: 'replace' });

onMounted(load);

async function load() {
  try {
    const res = await client.get('/admin/sensitive-words');
    words.value = res.data || [];
  } catch {}
}

async function add() {
  if (!newWord.word) return;
  try {
    await client.post('/admin/sensitive-words', { word: newWord.word, level: newWord.level });
    ElMessage.success('已添加');
    newWord.word = '';
    load();
  } catch {}
}

async function remove(row: any) {
  try {
    await client.delete(`/admin/sensitive-words/${row.id}`);
    ElMessage.success('已删除');
    load();
  } catch {}
}
</script>
