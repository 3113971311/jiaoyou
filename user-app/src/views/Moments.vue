<template>
  <div class="page-container">
    <el-button type="primary" @click="showPost=true" style="margin-bottom:16px">发布动态</el-button>
    <div v-if="!moments.length"><el-empty description="暂无动态" /></div>
    <div v-for="m in moments" :key="m.id" class="glass-card" style="margin-bottom:12px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-weight:600">{{ m.user?.nickname||m.user?.username }}</span>
        <span style="color:var(--text-secondary);font-size:12px">{{ new Date(m.created_at).toLocaleDateString() }}</span>
      </div>
      <div v-if="m.content_text" style="margin-bottom:8px;line-height:1.6">{{ m.content_text }}</div>
      <div v-if="m.images?.length" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">
        <el-image v-for="img in m.images" :key="img.thumb" :src="img.thumb||img.url" style="width:clamp(70px,12vw,100px);height:clamp(70px,12vw,100px);border-radius:8px" fit="cover" :preview-src-list="m.images.map(i=>i.url||i.thumb)" />
      </div>
      <div style="display:flex;gap:16px;color:var(--text-secondary);font-size:13px">
        <span @click="toggleLike(m)" style="cursor:pointer"><el-icon><StarFilled v-if="m.liked" style="color:#ff9500"/><Star v-else/></el-icon> {{ m.like_count }}</span>
        <span @click="openComment(m)" style="cursor:pointer"><el-icon><ChatDotSquare /></el-icon> {{ m.comment_count }}</span>
      </div>
    </div>

    <el-dialog v-model="showPost" title="发布动态" style="width:min(95vw,500px)">
      <el-input v-model="postText" type="textarea" :rows="4" placeholder="说点什么..." maxlength="500" show-word-limit />
      <input ref="fileInput" type="file" accept="image/*" multiple style="display:none" @change="onFileChange" />
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin:12px 0"><div v-for="(f,i) in previews" :key="i" style="position:relative"><img :src="f" style="width:80px;height:80px;border-radius:8px;object-fit:cover" /><span @click="removeImg(i)" style="position:absolute;top:-6px;right:-6px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;text-align:center;line-height:20px;font-size:12px;cursor:pointer">×</span></div></div>
      <el-button @click="fileInput.click()" :disabled="uploadFiles.length>=9">选择图片 ({{ uploadFiles.length }}/9)</el-button>
      <template #footer><el-button @click="showPost=false">取消</el-button><el-button type="primary" @click="submitPost" :loading="posting">发布</el-button></template>
    </el-dialog>

    <el-dialog v-model="showComment" title="评论" style="width:min(95vw,500px)">
      <div v-for="c in comments" :key="c.id" style="padding:8px 0;border-bottom:1px solid var(--card-border);font-size:14px"><strong>{{ c.user?.nickname||c.user?.username }}:</strong> {{ c.content }}</div>
      <div style="display:flex;gap:8px;margin-top:12px"><el-input v-model="commentText" placeholder="写评论..." @keyup.enter="submitComment" /><el-button type="primary" size="small" @click="submitComment">发送</el-button></div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFeed, createMoment, toggleLike, addComment, getComments } from '../api'

const moments = ref([])
const showPost = ref(false)
const postText = ref('')
const uploadFiles = ref([])
const previews = ref([])
const fileInput = ref(null)
const posting = ref(false)
const showComment = ref(false)
const commentText = ref('')
const comments = ref([])
const currentMoment = ref(null)

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

async function toggleLikeM(m) { try { const r=await toggleLike(m.id); m.liked=r.data.liked; m.like_count=r.data.like_count } catch {} }
async function openComment(m) { currentMoment.value=m; showComment.value=true; try { const r=await getComments(m.id); comments.value=r.data.list||[] } catch {} }
async function submitComment() { if (!commentText.value) return; try { const r=await addComment(currentMoment.value.id,{content:commentText.value}); comments.value.push(r.data); commentText.value=''; currentMoment.value.comment_count++ } catch {} }
</script>
