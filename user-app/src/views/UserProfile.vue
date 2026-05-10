<template>
  <div class="page-container" style="max-width:500px;margin:0 auto">
    <el-page-header @back="$router.back()" title="返回" />
    <div class="glass-card" style="text-align:center;margin-top:16px" v-if="user">
      <el-avatar :size="80" :src="user.avatar_url" />
      <h3 style="margin-top:12px">{{ user.nickname||user.username }}</h3>
      <p v-if="user.location" style="color:var(--text-secondary);font-size:13px"><el-icon><Location /></el-icon> {{ user.location }}</p>
      <p style="color:var(--text-secondary);font-size:13px">{{ user.bio||'暂无简介' }}</p>
      <div style="display:flex;gap:8px;justify-content:center;margin-top:12px">
        <el-button :type="fs.i_follow?'default':'primary'" size="small" @click="toggleFollow">{{ fs.i_follow?'取消关注':'关注' }}</el-button>
        <el-button size="small" @click="startChat">发消息</el-button>
        <el-button size="small" type="danger" @click="block">拉黑</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUser, follow, unfollow, followStatus, blockUser, createConversation } from '../api'
const route = useRoute()
const router = useRouter()
const user = ref(null)
const fs = ref({ i_follow:false, they_follow:false, mutual:false })
const uid = route.params.id
onMounted(async ()=>{
  try { const [u,s] = await Promise.all([getUser(uid),followStatus(uid)]); user.value=u.data; fs.value=s.data } catch {}
})
async function toggleFollow() {
  try { if(fs.value.i_follow) { await unfollow(uid); fs.value.i_follow=false } else { await follow(uid); fs.value.i_follow=true } } catch {}
}
async function startChat() { try { const r=await createConversation({target_user_id:uid}); router.push('/chat/'+r.data.id) } catch(e) { ElMessage.error(e.response?.data?.detail||'操作失败') } }
async function block() { try { await blockUser(uid); ElMessage.success('已拉黑'); router.back() } catch {} }
</script>
