<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
      <el-button @click="$router.push('/')" circle><el-icon><Back /></el-icon></el-button>
      <h2 style="margin:0;flex:1">匹配交友</h2>
    </div>

    <div v-if="!status.isMatching && !status.isMatched" style="text-align:center">
      <div class="glass-card" style="max-width:min(540px,90vw);margin:0 auto">
        <div style="margin-bottom:12px;text-align:center"><strong>匹配范围</strong><br/><el-radio-group v-model="scope"><el-radio value="city">同区/县</el-radio><el-radio value="province">同省</el-radio></el-radio-group></div>
        <div style="margin-bottom:12px;text-align:center"><strong>期望性别</strong><br/><el-radio-group v-model="preferGender"><el-radio value="male">男</el-radio><el-radio value="female">女</el-radio></el-radio-group></div>
        <div style="margin-bottom:16px;font-size:clamp(12px,1vw,14px);color:var(--text-secondary);text-align:center">
          <p>📍 当前定位：{{ currentLocation || '未获取' }}</p>
          <p v-if="locating" style="color:var(--accent);margin-top:4px">正在通过GPS获取定位...</p>
          <p v-else-if="!savedLat" style="color:var(--danger);margin-top:4px">需要开启GPS定位才能匹配</p>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:8px">
          <el-button @click="tryLocate" :loading="locating" style="width:100%">获取GPS定位</el-button>
          <el-button type="primary" size="large" @click="startMatch" :loading="matching" style="width:100%" :disabled="!savedLat">开始匹配</el-button>
        </div>
      </div>
    </div>

    <div v-if="status.isMatching" class="glass-card" style="max-width:min(540px,90vw);margin:0 auto;padding:clamp(24px,3vw,40px);text-align:center">
      <el-icon :size="60" color="#007aff"><Loading /></el-icon>
      <h3 style="margin-top:16px">正在匹配...</h3>
      <p style="color:var(--text-secondary);margin:8px 0">{{ waitTime }}</p>
      <el-button @click="cancelMatch" :loading="cancelling">取消匹配</el-button>
    </div>

    <div v-if="status.isMatched && status.matchedUser" class="glass-card" style="max-width:min(540px,90vw);margin:0 auto;padding:clamp(24px,3vw,40px);text-align:center">
      <h3 style="color:var(--success)">配对成功!</h3>
      <p style="font-size:clamp(16px,1.5vw,20px);margin:8px 0">{{ status.matchedUser.nickname||status.matchedUser.username }}</p>
      <el-button type="primary" @click="$router.push('/chat')">去聊天</el-button>
      <el-button style="margin-top:8px" @click="closeMatch">重新匹配</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Back } from '@element-plus/icons-vue'
import { startMatch as apiStart, cancelMatch as apiCancel, matchStatus, getMe, updateProfile } from '../api'

const scope = ref('city')
const preferGender = ref('')
const matching = ref(false)
const cancelling = ref(false)
const locating = ref(false)
const currentLocation = ref('')
const savedLat = ref(null)
const savedLng = ref(null)
const status = reactive({ isMatching:false, isMatched:false, matchedUser:null, expiresAt:null })
const waitTime = ref('')
let pollTimer=null, waitTimer=null, startedAt=0

function mapStatus(d) { status.isMatching = d.is_matching; status.isMatched = d.is_matched; status.matchedUser = d.matched_user; status.expiresAt = d.expires_at }

onMounted(async ()=>{
  try {
    const r = await matchStatus(); mapStatus(r.data)
    if (r.data.is_matching) startPolling()
    const me = await getMe()
    if (me.data.location) currentLocation.value = me.data.location
  } catch {}
  tryLocate()
})
onUnmounted(()=>stopPolling())

// 通过 WebRTC STUN 获取真实 IP（跳过 HTTP 代理）
async function getRealIP() {
  return new Promise((resolve) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' }]
    })
    const candidates = []
    const timeout = setTimeout(() => {
      pc.close()
      // 从 candidates 提取真实 IP
      for (const c of candidates) {
        const m = c.match(/(\d+\.\d+\.\d+\.\d+)/)
        if (m) {
          const ip = m[1]
          if (!ip.startsWith('10.') && !ip.startsWith('192.168.') && !ip.startsWith('172.')) {
            resolve(ip); return
          }
        }
      }
      resolve(null)
    }, 3000)
    pc.onicecandidate = (e) => {
      if (e.candidate) candidates.push(e.candidate.candidate)
      else { clearTimeout(timeout); pc.close(); timeout._called = true; }
    }
    pc.createDataChannel('')
    pc.createOffer().then(o => pc.setLocalDescription(o))
  })
}

async function tryLocate() {
  locating.value = true
  currentLocation.value = ''
  let permState = 'unknown'

  // --- 第1步：GPS/设备定位 ---
  if (navigator.geolocation) {
    try {
      if (navigator.permissions) {
        try { permState = (await navigator.permissions.query({ name: 'geolocation' })).state } catch {}
      }
    } catch {}
    for (const highAccuracy of [false, true]) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: highAccuracy, timeout: 10000, maximumAge: 120000,
          })
        })
        savedLat.value = pos.coords.latitude
        savedLng.value = pos.coords.longitude
        // 反查地址
        const r = await fetch(`/api/geocode/reverse?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`)
        if (r.ok) {
          const d = await r.json()
          currentLocation.value = d.location || `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`
        }
        if (currentLocation.value) await updateProfile({ location: currentLocation.value })
        ElMessage.success('已通过GPS获取位置')
        locating.value = false
        return
      } catch {}
    }
  }

  // --- 第2步：WebRTC 真实IP（跳过代理）---
  currentLocation.value = '正在通过真实IP获取位置...'
  try {
    const realIP = await getRealIP()
    if (realIP) {
      const r = await fetch(`/api/geocode/ip-locate?ip=${realIP}`)
      if (r.ok) {
        const d = await r.json()
        if (d.lat && d.lng) {
          savedLat.value = d.lat
          savedLng.value = d.lng
          currentLocation.value = d.location || `${d.lat.toFixed(4)}, ${d.lng.toFixed(4)}`
          await updateProfile({ location: currentLocation.value })
          ElMessage.success('已通过真实IP获取大致位置')
          locating.value = false
          return
        }
      }
    }
  } catch {}

  // --- 第3步：服务端IP定位（最后的回退）---
  try {
    const r = await fetch('/api/geocode/my-ip')
    if (r.ok) {
      const d = await r.json()
      if (d.lat && d.lng) {
        savedLat.value = d.lat
        savedLng.value = d.lng
        currentLocation.value = d.location || `${d.lat.toFixed(4)}, ${d.lng.toFixed(4)}`
        await updateProfile({ location: currentLocation.value })
        ElMessage.success('已通过网络获取大致位置')
        locating.value = false
        return
      }
    }
  } catch {}

  // 全部失败
  savedLat.value = null; savedLng.value = null; currentLocation.value = '获取失败'
  ElMessage.error('无法获取位置。请检查：① 设备GPS/Wi-Fi是否开启 ② Windows定位服务是否开启')
  locating.value = false
}

function startPolling() { stopPolling(); startedAt=Date.now(); updateWait(); waitTimer=setInterval(updateWait,1000); pollTimer=setInterval(async ()=>{ try { const r=await matchStatus(); mapStatus(r.data); if(!r.data.is_matching&&!r.data.is_matched) stopPolling() } catch {} },8000) }
function stopPolling() { clearInterval(pollTimer); clearInterval(waitTimer); pollTimer=null; waitTimer=null }
function updateWait() { const s=Math.floor((Date.now()-startedAt)/1000); waitTime.value=s>60?Math.floor(s/60)+'分'+s%60+'秒':s+'秒' }

async function doMatch(lat, lng) {
  try {
    const me = await getMe()
    const r = await apiStart({
      scope: scope.value,
      latitude: lat,
      longitude: lng,
      prefer_gender: preferGender.value || (me.data.gender === 'male' ? 'female' : 'male'),
    })
    if (r.data.matched) {
      mapStatus({ is_matched: true, is_matching: false, matched_user: r.data.matched_user })
    } else {
      status.isMatching = true; startPolling()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '匹配失败')
  }
}

async function startMatch() {
  if (!savedLat.value) { ElMessage.warning('请先获取GPS定位'); return }
  matching.value = true
  try { await doMatch(savedLat.value, savedLng.value) } catch {}
  matching.value = false
}

async function cancelMatch() { cancelling.value=true; try { await apiCancel(); status.isMatching=false; stopPolling(); ElMessage.success('已取消') } catch {} finally { cancelling.value=false } }
async function closeMatch() { await cancelMatch(); status.isMatched=false; status.matchedUser=null }
</script>
