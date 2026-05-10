<template>
  <div class="page-container" style="text-align:center">
    <h2 style="margin-bottom:20px">匹配交友</h2>

    <div v-if="!status.isMatching && !status.isMatched">
      <div class="glass-card rw-sm mx-auto">
        <div style="margin-bottom:12px"><strong>匹配范围</strong><br/><el-radio-group v-model="scope"><el-radio value="city">同城</el-radio><el-radio value="province">同省</el-radio></el-radio-group></div>
        <div style="margin-bottom:20px"><strong>期望性别</strong><br/><el-radio-group v-model="preferGender"><el-radio value="male">男</el-radio><el-radio value="female">女</el-radio></el-radio-group></div>
        <el-button type="primary" size="large" @click="startMatch" :loading="matching" style="width:100%">开始匹配</el-button>
      </div>
    </div>

    <div v-if="status.isMatching" class="glass-card rw-sm mx-auto" style="padding:40px">
      <el-icon :size="60" color="#007aff"><Loading /></el-icon>
      <h3 style="margin-top:16px">正在匹配...</h3>
      <p style="color:var(--text-secondary);margin:8px 0">{{ waitTime }}</p>
      <el-button @click="cancelMatch" :loading="cancelling">取消匹配</el-button>
    </div>

    <div v-if="status.isMatched && status.matchedUser" class="glass-card rw-sm mx-auto" style="padding:40px">
      <h3 style="color:var(--success)">配对成功!</h3>
      <p style="font-size:18px;margin:8px 0">{{ status.matchedUser.nickname||status.matchedUser.username }}</p>
      <el-button type="primary" @click="$router.push('/chat')">去聊天</el-button>
      <el-button style="margin-top:8px" @click="closeMatch">重新匹配</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { startMatch as apiStart, cancelMatch as apiCancel, matchStatus, getMe } from '../api'

const scope = ref('city')
const preferGender = ref('')
const matching = ref(false)
const cancelling = ref(false)
const status = reactive({ isMatching:false, isMatched:false, matchedUser:null, expiresAt:null })
const waitTime = ref('')
let pollTimer=null, waitTimer=null, startedAt=0

function mapStatus(d) { status.isMatching = d.is_matching; status.isMatched = d.is_matched; status.matchedUser = d.matched_user; status.expiresAt = d.expires_at }
onMounted(async ()=>{ try { const r=await matchStatus(); mapStatus(r.data); if(r.data.is_matching) startPolling() } catch {} })
onUnmounted(()=>stopPolling())

function startPolling() { stopPolling(); startedAt=Date.now(); updateWait(); waitTimer=setInterval(updateWait,1000); pollTimer=setInterval(async ()=>{ try { const r=await matchStatus(); mapStatus(r.data); if(!r.data.is_matching&&!r.data.is_matched) stopPolling() } catch {} },8000) }
function stopPolling() { clearInterval(pollTimer); clearInterval(waitTimer); pollTimer=null; waitTimer=null }
function updateWait() { const s=Math.floor((Date.now()-startedAt)/1000); waitTime.value=s>60?Math.floor(s/60)+'分'+s%60+'秒':s+'秒' }

async function doMatch(lat,lng) {
  try { const me=await getMe(); const r=await apiStart({ scope:scope.value, latitude:lat, longitude:lng, prefer_gender:preferGender.value||(me.data.gender==='male'?'female':'male') }); if(r.data.matched){ mapStatus({is_matched:true,is_matching:false,matched_user:r.data.matched_user}) }else{ status.isMatching=true; startPolling() } } catch(e) { ElMessage.error(e.response?.data?.detail||'匹配失败') }
}
async function startMatch() {
  matching.value=true
  try {
    navigator.geolocation.getCurrentPosition(async pos=>{ await doMatch(pos.coords.latitude,pos.coords.longitude); matching.value=false }, async ()=>{
      const me=await getMe()
      if (me.data.location) {
        try { const r=await (await fetch('/api/geocode/search?q='+encodeURIComponent(me.data.location),{headers:{Authorization:'Bearer '+localStorage.getItem('user_token')}})).json(); if(r.lat) { await doMatch(r.lat,r.lng); matching.value=false; return } } catch {}
      }
      ElMessage.error('无法获取定位，请检查GPS或填写个人所在地'); matching.value=false
    },{ timeout:8000 })
  } catch(e) { ElMessage.error('匹配失败'); matching.value=false }
}
async function cancelMatch() { cancelling.value=true; try { await apiCancel(); status.isMatching=false; stopPolling(); ElMessage.success('已取消') } catch {} finally { cancelling.value=false } }
async function closeMatch() { await cancelMatch(); status.isMatched=false; status.matchedUser=null }
</script>
