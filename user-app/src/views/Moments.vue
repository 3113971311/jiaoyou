<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <el-button @click="$router.push('/')" circle><el-icon><Back /></el-icon></el-button>
      <h2 style="margin:0;flex:1">动态</h2>
      <el-button type="primary" @click="showPost=true">发布动态</el-button>
    </div>
    <div v-if="!moments.length"><el-empty description="暂无动态" /></div>
    <div v-for="m in moments" :key="m.id" class="glass-card" style="margin-bottom:14px;cursor:pointer" @click="$router.push(`/moment/${m.id}`)">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <el-avatar :src="userImageUrl(m.user?.avatar_url)" :size="36" />
        <div>
          <span style="font-weight:600">{{ m.user?.nickname||m.user?.username }}</span>
          <el-tag v-if="m.status==='pending_review'" type="warning" size="small" style="margin-left:6px">审核中</el-tag>
          <el-tag v-else-if="m.status==='rejected'" type="danger" size="small" style="margin-left:6px">未通过</el-tag>
        </div>
        <span style="color:var(--text-secondary);font-size:12px;margin-left:auto">{{ new Date(m.created_at).toLocaleDateString() }}</span>
        <el-button v-if="store.user?.id === m.user?.id" size="small" type="danger" @click.stop="delMoment(m)" style="margin-left:8px">删除</el-button>
      </div>
      <div v-if="m.content_text" style="margin-bottom:8px;line-height:1.6;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical">{{ m.content_text }}</div>
      <div v-if="m.images?.length" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px" @click.stop>
        <el-image v-for="(img, idx) in m.images.slice(0, 6)" :key="idx" :src="userImageUrl(img.thumb)" style="width:clamp(70px,10vw,100px);height:clamp(70px,10vw,100px);border-radius:8px" fit="cover" :preview-src-list="m.images.map(i=>userImageUrl(i.url))" :initial-index="idx" />
        <div v-if="m.images.length > 6" style="display:flex;align-items:center;justify-content:center;width:clamp(70px,10vw,100px);height:clamp(70px,10vw,100px);background:var(--card-bg);border-radius:8px;font-size:14px;color:var(--text-secondary)">+{{ m.images.length - 6 }}</div>
      </div>
      <div style="display:flex;gap:20px;color:var(--text-secondary);font-size:13px">
        <span @click.stop="toggleLikeM(m)" style="cursor:pointer"><el-icon><StarFilled v-if="m.liked" style="color:#ff9500"/><Star v-else/></el-icon> {{ m.like_count }}</span>
        <span><el-icon><ChatDotSquare /></el-icon> {{ m.comment_count }}</span>
        <span @click.stop="toggleFavM(m)" style="cursor:pointer"><el-icon><FolderOpened v-if="m.favorited" style="color:#ff9f0a"/><Folder v-else/></el-icon> {{ m.favorite_count || 0 }}</span>
      </div>
    </div>

    <el-dialog v-model="showPost" title="发布动态" style="width:min(95vw,500px)">
      <el-input v-model="postText" type="textarea" :rows="4" placeholder="说点什么..." maxlength="500" show-word-limit />
      <input ref="fileInput" type="file" accept="image/*" multiple style="display:none" @change="onFileChange" />
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin:12px 0"><div v-for="(f,i) in previews" :key="i" style="position:relative"><img :src="f" style="width:80px;height:80px;border-radius:8px;object-fit:cover" /><span @click="removeImg(i)" style="position:absolute;top:-6px;right:-6px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;text-align:center;line-height:20px;font-size:12px;cursor:pointer">×</span></div></div>
      <el-button @click="fileInput.click()" :disabled="uploadFiles.length>=9">选择图片 ({{ uploadFiles.length }}/9)</el-button>
      <template #footer><el-button @click="showPost=false">取消</el-button><el-button type="primary" @click="submitPost" :loading="posting">发布</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { getFeed, createMoment, toggleLike, toggleFavorite, deleteMoment, userImageUrl } from '../api'

const store = useAuthStore()

const moments = ref([])
const showPost = ref(false)
const postText = ref('')
const uploadFiles = ref([])
const previews = ref([])
const fileInput = ref(null)
const posting = ref(false)

onMounted(loadFeed)
async function loadFeed() { try { const r=await getFeed(); moments.value=r.data.list||[] } catch {} }

function onFileChange(e) {
  const files = e.target.files; if (!files) return
  for (let i=0;i<files.length;i++) { if (files[i].size>10*1024*1024) { ElMessage.warning('图片不能超过10MB'); continue }; uploadFiles.value.push(files[i]); previews.value.push(URL.createObjectURL(files[i])) }
  e.target.value = ''
}
function removeImg(i) { uploadFiles.value.splice(i,1); previews.value.splice(i,1) }

async function submitPost() {
  if (!postText.value && !uploadFiles.value.length) return
  posting.value = true
  try { const f=new FormData(); f.append('content_text',postText.value||''); uploadFiles.value.forEach(ff=>f.append('images',ff)); await createMoment(f); ElMessage.success('发布成功'); showPost.value=false; postText.value=''; uploadFiles.value=[]; previews.value=[]; loadFeed() }
  catch(e) { ElMessage.error(e.response?.data?.detail||'发布失败') }
  finally { posting.value = false }
}

async function toggleLikeM(m) {
  try { const r=await toggleLike(m.id); m.liked=r.data.liked; m.like_count=r.data.like_count } catch {}
}
async function toggleFavM(m) {
  try { const r=await toggleFavorite(m.id); m.favorited=r.data.favorited; m.favorite_count=r.data.favorite_count } catch {}
}
async function delMoment(m) {
  try {
    await ElMessageBox.confirm('确定删除这条动态？', '删除', { type: 'danger', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteMoment(m.id)
    ElMessage.success('已删除')
    loadFeed()
  } catch {}
}
</script>
