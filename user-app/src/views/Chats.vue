<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <el-button @click="$router.push('/')" circle><el-icon><Back /></el-icon></el-button>
      <h2 style="margin:0">消息</h2>
    </div>
    <div v-if="!list.length" class="glass-card" style="text-align:center"><el-empty description="暂无会话" /></div>
    <div v-for="c in list" :key="c.id" class="glass-card" style="margin-bottom:8px;cursor:pointer;display:flex;align-items:center;gap:12px" @click="$router.push('/chat/'+c.id)">
      <el-avatar :size="48" :src="userImageUrl(c.other_user?.avatar_url)" />
      <div style="flex:1">
        <div style="font-weight:600">{{ c.other_user?.nickname||c.other_user?.username }}</div>
        <div style="font-size:13px;color:var(--text-secondary);margin-top:2px">{{ c.last_message?.content?.slice(0,50) || '暂无消息' }}</div>
      </div>
      <div style="font-size:12px;color:var(--text-secondary)">{{ c.last_message_at ? new Date(c.last_message_at).toLocaleDateString() : '' }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Back } from '@element-plus/icons-vue'
import { getConversations, userImageUrl } from '../api'
const list = ref([])
onMounted(async ()=>{ try { const r=await getConversations(); list.value=r.data.list||[] } catch {} })
</script>
