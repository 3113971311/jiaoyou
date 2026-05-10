<template>
  <div style="display:flex;flex-direction:column;height:100vh;background:var(--bg)">
    <div class="navbar" style="padding:12px 16px">
      <el-button link @click="$router.back()"><el-icon><ArrowLeft /></el-icon></el-button>
      <span style="font-weight:600;margin-left:8px">聊天</span>
    </div>
    <div ref="msgBox" style="flex:1;overflow-y:auto;padding:12px 16px">
      <div v-for="m in messages" :key="m.id" :style="{display:'flex',justifyContent:m.sender_id===userId?'flex-end':'flex-start',marginBottom:'10px'}">
        <div :style="{maxWidth:'70%',padding:'10px 14px',borderRadius:'12px',fontSize:'14px',lineHeight:'1.5',background:m.sender_id===userId?'var(--accent)':'#fff',color:m.sender_id===userId?'#fff':'var(--text)'}">
          <div v-if="m.content_type==='text'">{{ m.content }}</div>
          <el-image v-else-if="m.image_url" :src="m.image_url" style="max-width:200px;border-radius:8px" fit="contain" :preview-src-list="[m.image_url]" />
        </div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:#fff;border-top:1px solid rgba(0,0,0,0.05)">
      <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="sendImage" />
      <el-button link @click="fileInput.click()"><el-icon :size="22"><PictureFilled /></el-icon></el-button>
      <el-input v-model="text" placeholder="输入消息..." @keyup.enter="sendText" style="flex:1" />
      <el-button type="primary" size="small" @click="sendText" :disabled="!text.trim()">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getMessages, uploadChatImage } from '../api'

const route = useRoute()
const auth = useAuthStore()
const userId = auth.user?.id
const messages = ref([])
const text = ref('')
const msgBox = ref(null)
const fileInput = ref(null)
let timer = null

onMounted(async ()=>{
  await loadMsgs()
  timer = setInterval(loadMsgs, 3000)
})
onUnmounted(()=>clearInterval(timer))

async function loadMsgs() {
  try { const r=await getMessages(route.params.id); messages.value=r.data.list||[]; scrollBottom() } catch {}
}
function scrollBottom() { nextTick(()=>{ if(msgBox.value) msgBox.value.scrollTop=msgBox.value.scrollHeight }) }

function sendText() {
  if (!text.value.trim()) return
  const temp = { id:Date.now().toString(), sender_id:userId, content:text.value, content_type:'text', created_at:new Date().toISOString() }
  messages.value.push(temp)
  // Use fetch directly since backend doesn't have a dedicated send-message endpoint via REST
  fetch('/api/chat/send/'+route.params.id,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('user_token')},body:JSON.stringify({content:text.value,content_type:'text'})})
  text.value = ''
  scrollBottom()
}

async function sendImage(e) {
  const f = e.target.files[0]; if (!f) return
  const fd = new FormData(); fd.append('file', f)
  try { const r=await uploadChatImage(fd); messages.value.push({id:Date.now().toString(),sender_id:userId,content_type:'image',image_url:r.data.url,created_at:new Date().toISOString()}); scrollBottom() } catch {}
  e.target.value = ''
}
</script>
