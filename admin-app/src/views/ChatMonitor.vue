<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">聊天监控</h2>
    <el-input v-model="search" placeholder="搜索用户名..." style="max-width:280px;margin-bottom:12px" @keyup.enter="load" />
    <el-table :data="chats" @row-click="openChat" highlight-current-row>
      <el-table-column label="用户1"><template #default="{row}">{{ row.user1_id }}</template></el-table-column>
      <el-table-column label="用户2"><template #default="{row}">{{ row.user2_id }}</template></el-table-column>
      <el-table-column label="最后活跃"><template #default="{row}">{{ row.last_message_at ? new Date(row.last_message_at).toLocaleString() : '-' }}</template></el-table-column>
    </el-table>
    <el-dialog v-model="showMsgs" title="消息记录" width="700px">
      <div v-for="m in messages" :key="m.id" style="padding:8px 0;border-bottom:1px solid var(--card-border)">
        <strong>{{ m.sender_id }}:</strong>
        <span v-if="m.content_type==='text'">{{ m.content }}</span>
        <el-image v-else-if="m.image_url" :src="m.image_url" style="width:clamp(80px,15vw,120px);height:clamp(80px,15vw,120px);border-radius:8px" fit="cover" />
        <small style="color:var(--text-secondary);margin-left:12px">{{ new Date(m.created_at).toLocaleString() }}</small>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { adminChats, adminChatMsgs } from '../api'
const search = ref('')
const chats = ref([])
const messages = ref([])
const showMsgs = ref(false)
load()
async function load() { try { const r=await adminChats(); chats.value=r.data||[] } catch {} }
async function openChat(row) { try { const r=await adminChatMsgs(row.id); messages.value=r.data||[]; showMsgs.value=true } catch {} }
</script>
