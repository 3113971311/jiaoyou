<template>
  <div class="page-container" style="max-width:600px;margin:0 auto">
    <el-page-header @back="$router.back()" title="返回"><template #content>我的粉丝</template></el-page-header>
    <div v-if="!list.length" style="margin-top:40px"><el-empty description="暂无粉丝" /></div>
    <div v-for="u in list" :key="u.id" class="glass-card" style="margin-top:8px;display:flex;align-items:center;gap:12px;cursor:pointer" @click="$router.push('/profile/'+u.id)">
      <el-avatar :size="48" :src="u.avatar_url" />
      <div><div style="font-weight:600">{{ u.nickname||u.username }}</div><div style="font-size:13px;color:var(--text-secondary)">{{ u.gender==='male'?'男':u.gender==='female'?'女':'' }}</div></div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { getFollowers } from '../api'
const list = ref([])
onMounted(async ()=>{ try { const r=await getFollowers(); list.value=r.data.list||[] } catch {} })
</script>
