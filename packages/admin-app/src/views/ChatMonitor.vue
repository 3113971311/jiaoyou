<template>
  <div class="cm-page">
    <h2>聊天监控</h2>
    <el-input v-model="search" placeholder="搜索用户名..." style="width:240px;margin-bottom:12px" @keyup.enter="loadChats" />
    <el-table :data="chats" style="width:100%" @row-click="openChat">
      <el-table-column label="用户1">
        <template #default="{ row }">{{ row.user1?.nickname || row.user1?.username }}</template>
      </el-table-column>
      <el-table-column label="用户2">
        <template #default="{ row }">{{ row.user2?.nickname || row.user2?.username }}</template>
      </el-table-column>
      <el-table-column prop="_count.messages" label="消息数" width="80" />
      <el-table-column label="最后活跃">
        <template #default="{ row }">{{ row.lastMessageAt ? new Date(row.lastMessageAt).toLocaleString() : '-' }}</template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showMsgs" title="消息记录" width="700px">
      <div v-for="m in messages" :key="m.id" class="msg-row">
        <strong>{{ m.sender?.nickname || m.sender?.username }}:</strong>
        <span v-if="m.contentType === 'text'">{{ m.content }}</span>
        <el-image v-else :src="m.imageUrl" style="width:120px;height:120px" fit="cover" />
        <small>{{ new Date(m.createdAt).toLocaleString() }}</small>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import client from '../api/client';

const search = ref('');
const chats = ref<any[]>([]);
const messages = ref<any[]>([]);
const showMsgs = ref(false);

async function loadChats() {
  try {
    const res = await client.get('/admin/chats', { params: { search: search.value } });
    chats.value = res.data || [];
  } catch {}
}

async function openChat(row: any) {
  try {
    const res = await client.get(`/admin/chats/${row.id}/messages`);
    messages.value = res.data || [];
    showMsgs.value = true;
  } catch {}
}
</script>
<style scoped>
.msg-row { padding: 8px 0; border-bottom: 1px solid #eee; }
.msg-row small { color: #999; margin-left: 12px; }
</style>
