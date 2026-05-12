<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <el-button @click="$router.push('/')" circle><el-icon><Back /></el-icon></el-button>
      <h2 style="margin:0;flex:1">通知</h2><el-button link type="primary" @click="readAll">全部已读</el-button>
    </div>
    <div v-if="!items.length" class="glass-card" style="text-align:center;padding:40px"><el-empty description="暂无通知" /></div>
    <div v-for="n in items" :key="n.id" class="glass-card" style="margin-bottom:8px;cursor:pointer;opacity:0.6" :class="{unread:!n.is_read}" @click="readOne(n)">
      <div style="font-weight:600;font-size:14px">{{ n.title }}<el-badge v-if="!n.is_read" is-dot style="margin-left:6px" /></div>
      <div style="font-size:13px;color:var(--text-secondary);margin-top:4px">{{ n.content }}</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">{{ new Date(n.created_at).toLocaleString() }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Back } from '@element-plus/icons-vue'
import { getNotifications, markRead, markAllRead } from '../api'
const items = ref([])
onMounted(async ()=>{ try { const r=await getNotifications(); items.value=r.data.items||[] } catch {} })
async function readOne(n) { if(!n.is_read) { await markRead(n.id); n.is_read=true } }
async function readAll() { await markAllRead(); items.value.forEach(n=>n.is_read=true) }
</script>
<style scoped>.unread { opacity:1; background:var(--accent-light) }</style>
