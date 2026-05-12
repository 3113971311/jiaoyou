<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <el-button @click="$router.push('/')" circle><el-icon><ArrowLeft /></el-icon></el-button>
      <h2 style="margin:0">动态详情</h2>
    </div>

    <div v-if="!m" style="text-align:center;padding:60px 0;color:var(--text-secondary)">加载中...</div>

    <template v-if="m">
      <!-- Author + status -->
      <div class="glass-card" style="margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
          <el-avatar :src="userImageUrl(m.user?.avatar_url)" :size="44" @click="$router.push(`/profile/${m.user?.id}`)" style="cursor:pointer" />
          <div>
            <div style="font-weight:600;font-size:16px">{{ m.user?.nickname || m.user?.username }}</div>
            <div style="font-size:12px;color:var(--text-secondary)">{{ new Date(m.created_at).toLocaleString() }}</div>
          </div>
          <el-tag v-if="m.status==='pending_review'" type="warning" size="small" style="margin-left:auto">审核中</el-tag>
          <el-tag v-else-if="m.status==='rejected'" type="danger" size="small" style="margin-left:auto">审核未通过</el-tag>
        </div>
        <!-- Content -->
        <div v-if="m.content_text" style="line-height:1.7;margin-bottom:12px;white-space:pre-wrap">{{ m.content_text }}</div>
        <!-- Images -->
        <div v-if="m.images?.length" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
          <el-image v-for="(img, idx) in m.images" :key="idx" :src="userImageUrl(img.thumb)" style="width:clamp(100px,16vw,160px);height:clamp(100px,16vw,160px);border-radius:10px;cursor:pointer" fit="cover" :preview-src-list="m.images.map(i=>userImageUrl(i.url))" :initial-index="idx" />
        </div>
        <!-- Reject reason -->
        <div v-if="m.status==='rejected' && m.review_comment" style="padding:8px 12px;background:rgba(255,69,58,0.1);border-radius:8px;font-size:13px;color:var(--danger);margin-bottom:8px">
          拒绝原因：{{ m.review_comment }}
        </div>
        <!-- Actions -->
        <div style="display:flex;gap:20px;align-items:center;border-top:1px solid var(--card-border);padding-top:12px">
          <span @click="doLike" style="cursor:pointer;display:flex;align-items:center;gap:4px;font-size:15px;color:var(--text-secondary);user-select:none" :style="m.liked?{color:'#ff9500'}:{}">
            <el-icon :size="20"><StarFilled v-if="m.liked"/><Star v-else/></el-icon> {{ m.like_count }}
          </span>
          <span @click="doFavorite" style="cursor:pointer;display:flex;align-items:center;gap:4px;font-size:15px;color:var(--text-secondary);user-select:none" :style="m.favorited?{color:'#ff9f0a'}:{}">
            <el-icon :size="20"><FolderOpened v-if="m.favorited"/><Folder v-else/></el-icon> 收藏 {{ m.favorite_count || 0 }}
          </span>
          <span @click="focusComment" style="cursor:pointer;display:flex;align-items:center;gap:4px;font-size:15px;color:var(--text-secondary)">
            <el-icon :size="20"><ChatDotSquare /></el-icon> {{ m.comment_count }}
          </span>
          <el-button v-if="store.user?.id === m.user?.id" size="small" type="danger" @click="doDelete" style="margin-left:auto">删除</el-button>
        </div>
      </div>

      <!-- Comments -->
      <div class="glass-card">
        <h4 style="margin-bottom:12px">评论 ({{ comments.length }})</h4>
        <div v-if="!comments.length" style="color:var(--text-secondary);text-align:center;padding:20px 0">暂无评论</div>
        <div v-for="c in comments" :key="c.id" style="padding:10px 0;border-bottom:1px solid var(--card-border)">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <span style="font-weight:600;font-size:14px;margin-bottom:2px">{{ c.user?.nickname || c.user?.username || '用户' }}</span>
            <el-button v-if="store.user?.id === c.user?.id || store.isAdmin" size="small" type="danger" text @click="delComment(c)">删除</el-button>
          </div>
          <div style="font-size:14px;color:var(--text);line-height:1.5">{{ c.content }}</div>
          <div style="font-size:11px;color:var(--text-tertiary);margin-top:4px">{{ new Date(c.created_at).toLocaleString() }}</div>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <el-input ref="commentInput" v-model="commentText" placeholder="写评论..." @keyup.enter="submitComment" size="large" />
          <el-button type="primary" @click="submitComment" :disabled="!commentText.trim()">发送</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, StarFilled, ChatDotSquare, Folder, FolderOpened } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { getMoment, toggleLike, toggleFavorite, getComments, addComment, deleteComment, deleteMoment, userImageUrl } from '../api'

const route = useRoute()
const router = useRouter()
const store = useAuthStore()
const m = ref(null)
const comments = ref([])
const commentText = ref('')
const commentInput = ref(null)

onMounted(async () => {
  try {
    const [mr, cr] = await Promise.all([
      getMoment(route.params.id),
      getComments(route.params.id),
    ])
    m.value = mr.data
    comments.value = cr.data.list || []
  } catch (e) {
    ElMessage.error('动态不存在或无权查看')
    router.back()
  }
})

async function doLike() {
  if (!m.value) return
  try {
    const r = await toggleLike(m.value.id)
    m.value.liked = r.data.liked
    m.value.like_count = r.data.like_count
  } catch {}
}

async function doFavorite() {
  if (!m.value) return
  try {
    const r = await toggleFavorite(m.value.id)
    m.value.favorited = r.data.favorited
    m.value.favorite_count = r.data.favorite_count
  } catch {}
}

async function submitComment() {
  if (!commentText.value.trim() || !m.value) return
  try {
    const r = await addComment(m.value.id, { content: commentText.value })
    comments.value.push(r.data)
    m.value.comment_count++
    commentText.value = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '评论失败')
  }
}

function focusComment() { commentInput.value?.focus() }

async function delComment(c) {
  try {
    await ElMessageBox.confirm('确定删除这条评论？', '删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteComment(m.value.id, c.id)
    comments.value = comments.value.filter(x => x.id !== c.id)
    m.value.comment_count--
    ElMessage.success('已删除')
  } catch {}
}
async function doDelete() {
  try {
    await ElMessageBox.confirm('确定删除这条动态？', '删除', { type: 'danger', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteMoment(m.value.id)
    ElMessage.success('已删除')
    router.back()
  } catch {}
}
</script>
