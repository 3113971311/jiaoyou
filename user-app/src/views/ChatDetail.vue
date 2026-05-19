<template>
  <div class="chat-page">
    <input ref="imageInput" type="file" accept="image/*" hidden @change="onImageSelected" />
    <input ref="videoInput" type="file" accept="video/*" hidden @change="onVideoSelected" />

    <header class="chat-header">
      <div class="chat-header__left">
        <el-button circle @click="router.push('/chat')">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <el-avatar :size="42" :src="userImageUrl(otherUser.avatar_url)" />
        <div class="chat-header__meta">
          <div class="chat-header__name">{{ otherUser.nickname || otherUser.username || '聊天' }}</div>
          <div class="chat-header__sub">
            <span v-if="activeCallStatusLabel">{{ activeCallStatusLabel }}</span>
            <span v-else>{{ audioRecording ? `语音录制中 ${recordingSecondsText}` : '发送文字、图片、语音和视频' }}</span>
          </div>
        </div>
      </div>
      <div class="chat-header__actions">
        <el-tooltip content="语音通话" placement="bottom">
          <el-button circle @click="startCall('audio')" :disabled="Boolean(currentCall)">
            <el-icon><Phone /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="视频通话" placement="bottom">
          <el-button circle @click="startCall('video')" :disabled="Boolean(currentCall)">
            <el-icon><VideoCamera /></el-icon>
          </el-button>
        </el-tooltip>
        <el-dropdown trigger="click">
          <el-button circle>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="confirmDeleteConversation">
                删除聊天记录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <section v-if="incomingCall && !currentCall" class="chat-banner">
      <div class="chat-banner__text">
        <strong>{{ incomingLabel }}</strong>
        <span>{{ otherUser.nickname || otherUser.username || '对方' }} 邀请你{{ incomingCall.call_type === 'video' ? '视频通话' : '语音通话' }}</span>
      </div>
      <div class="chat-banner__actions">
        <el-button type="success" @click="acceptIncomingCall">接听</el-button>
        <el-button @click="rejectIncomingCall">拒绝</el-button>
      </div>
    </section>

    <main ref="messageBox" class="chat-messages">
      <div v-if="!messages.length" class="glass-card chat-empty">
        暂无消息，发一句试试看。
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        class="chat-row"
        :class="{ 'chat-row--self': isOwnMessage(message) }"
      >
        <div class="chat-row__bubble-wrap">
          <div class="chat-row__meta-line">
            <span>{{ formatMessageTime(message.created_at) }}</span>
            <el-dropdown
              v-if="isOwnMessage(message)"
              trigger="click"
              @command="(command) => onMessageCommand(command, message)"
            >
              <span class="chat-row__menu">
                <el-icon><MoreFilled /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="delete">删除消息</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="chat-bubble" :class="{ 'chat-bubble--self': isOwnMessage(message) }">
            <template v-if="message.content_type === 'text'">
              <div class="chat-text">{{ message.content }}</div>
            </template>

            <template v-else-if="message.content_type === 'image'">
              <el-image
                :src="userImageUrl(message.media_url || message.image_url)"
                fit="cover"
                :preview-src-list="[userImageUrl(message.media_url || message.image_url)]"
                class="chat-image"
              />
            </template>

            <template v-else-if="message.content_type === 'audio'">
              <div class="chat-media-card">
                <div class="chat-media-card__title">语音消息</div>
                <audio :src="userImageUrl(message.media_url)" controls preload="metadata" class="chat-audio" />
                <div v-if="message.duration_seconds" class="chat-media-card__meta">
                  {{ formatDuration(message.duration_seconds) }}
                </div>
              </div>
            </template>

            <template v-else-if="message.content_type === 'video'">
              <div class="chat-media-card chat-media-card--video">
                <video :src="userImageUrl(message.media_url)" controls preload="metadata" class="chat-video" />
                <div class="chat-media-card__meta">
                  {{ message.content || '视频消息' }}
                  <span v-if="message.duration_seconds"> · {{ formatDuration(message.duration_seconds) }}</span>
                </div>
              </div>
            </template>

            <template v-else-if="message.content_type === 'call_audio'">
              <div class="chat-media-card">
                <div class="chat-media-card__title">{{ message.content || '语音通话记录' }}</div>
                <audio
                  v-if="message.media_url"
                  :src="userImageUrl(message.media_url)"
                  controls
                  preload="metadata"
                  class="chat-audio"
                />
                <div class="chat-media-card__meta">
                  {{ callStatusLabel(message) }}
                </div>
              </div>
            </template>

            <template v-else-if="message.content_type === 'call_video'">
              <div class="chat-media-card chat-media-card--video">
                <video
                  v-if="message.media_url"
                  :src="userImageUrl(message.media_url)"
                  controls
                  preload="metadata"
                  class="chat-video"
                />
                <div class="chat-media-card__meta">
                  {{ callStatusLabel(message) }}
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </main>

    <footer class="chat-composer">
      <div class="chat-composer__toolbar">
        <el-tooltip content="发送图片" placement="top">
          <el-button circle :disabled="Boolean(currentCall)" @click="imageInput?.click()">
            <el-icon><PictureFilled /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip :content="audioRecording ? '结束录音并发送' : '录制语音'" placement="top">
          <el-button circle :type="audioRecording ? 'danger' : 'default'" :disabled="Boolean(currentCall)" @click="toggleAudioRecording">
            <el-icon><Microphone /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="发送视频" placement="top">
          <el-button circle :disabled="Boolean(currentCall)" @click="videoInput?.click()">
            <el-icon><VideoCamera /></el-icon>
          </el-button>
        </el-tooltip>
      </div>

      <div class="chat-composer__input">
        <el-input
          v-model="text"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="输入你想说的话"
          :disabled="sendingText || Boolean(currentCall)"
          @keyup.enter.exact.prevent="sendText"
        />
      </div>

      <div class="chat-composer__send">
        <el-button type="primary" :loading="sendingText" :disabled="!text.trim()" @click="sendText">
          发送
        </el-button>
      </div>
    </footer>

    <el-dialog
      v-model="callDialogVisible"
      :title="callDialogTitle"
      width="min(92vw, 860px)"
      :close-on-click-modal="false"
      :show-close="false"
      destroy-on-close
    >
      <div class="call-panel">
        <div class="call-panel__hero">
          <div class="call-panel__identity">
            <el-avatar :size="64" :src="userImageUrl(otherUser.avatar_url)" />
            <div>
              <div class="call-panel__name">{{ otherUser.nickname || otherUser.username || '对方' }}</div>
              <div class="call-panel__status">{{ activeCallStatusLabel || '正在建立连接…' }}</div>
            </div>
          </div>
          <div class="call-panel__timer">{{ callElapsedText }}</div>
        </div>

        <div class="call-stage" :class="{ 'call-stage--video': currentCall?.call_type === 'video' }">
          <div class="call-stage__remote">
            <video
              v-if="currentCall?.call_type === 'video'"
              ref="remoteVideo"
              autoplay
              playsinline
              class="call-video-screen"
            />
            <div v-else class="call-audio-state">
              <el-icon class="call-audio-state__icon"><Phone /></el-icon>
              <span>语音通话中</span>
            </div>
          </div>
          <video
            v-if="currentCall?.call_type === 'video'"
            ref="localVideo"
            autoplay
            muted
            playsinline
            class="call-stage__local"
          />
        </div>

        <div class="call-panel__actions">
          <el-button type="danger" size="large" @click="hangupCurrentCall">挂断</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  acceptChatCall,
  attachChatCallRecording,
  createChatCall,
  deleteChatMessage,
  deleteConversation,
  endChatCall,
  getActiveCall,
  getChatCall,
  getMessages,
  rejectChatCall,
  sendCallSignal,
  sendChatMessage,
  uploadChatMedia,
  userImageUrl,
} from '../api'
import { useAuthStore } from '../stores/auth'
import { ArrowLeft, Microphone, MoreFilled, Phone, PictureFilled, VideoCamera } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const messageBox = ref(null)
const imageInput = ref(null)
const videoInput = ref(null)
const localVideo = ref(null)
const remoteVideo = ref(null)

const conversation = ref(null)
const messages = ref([])
const text = ref('')
const sendingText = ref(false)

const incomingCall = ref(null)
const currentCall = ref(null)
const callDialogVisible = ref(false)
const callRole = ref('')
const callStartedAt = ref(null)
const callElapsedSeconds = ref(0)

const audioRecorder = ref(null)
const audioRecording = ref(false)
const audioRecordingSeconds = ref(0)

let pollTimer = null
let callTimer = null
let audioStream = null
let audioChunks = []
let audioTickTimer = null

let peer = null
let localStream = null
let remoteStream = null
let recorderStream = null
let callRecorder = null
let callChunks = []
let callRecorderStarted = false
let callRecordingUploaded = false
let remoteOfferApplied = false
let remoteAnswerApplied = false
const seenRemoteCandidates = new Set()

const userId = computed(() => auth.user?.id || '')
const otherUser = computed(() => conversation.value?.other_user || {})
const incomingLabel = computed(() => incomingCall.value?.call_type === 'video' ? '视频来电' : '语音来电')
const callDialogTitle = computed(() => currentCall.value?.call_type === 'video' ? '视频通话' : '语音通话')
const recordingSecondsText = computed(() => formatDuration(audioRecordingSeconds.value))
const callElapsedText = computed(() => formatDuration(callElapsedSeconds.value))
const activeCallStatusLabel = computed(() => {
  if (!currentCall.value) return ''
  const statusMap = {
    ringing: callRole.value === 'caller' ? '等待对方接听…' : '正在接听…',
    active: '通话中',
    ended: '通话结束',
    rejected: '对方已拒绝',
    cancelled: '通话已取消',
    missed: '未接听',
  }
  return statusMap[currentCall.value.status] || ''
})

onMounted(async () => {
  await loadMessages()
  await pollChatState()
  pollTimer = window.setInterval(pollChatState, 2500)
  callTimer = window.setInterval(updateCallElapsed, 1000)
})

onUnmounted(() => {
  window.clearInterval(pollTimer)
  window.clearInterval(callTimer)
  window.clearInterval(audioTickTimer)
  if (currentCall.value?.id) {
    endChatCall(currentCall.value.id, {
      status: currentCall.value.status === 'active' ? 'ended' : 'cancelled',
    }).catch(() => {})
  }
  stopAudioRecorder()
  teardownPeer()
})

function isOwnMessage(message) {
  return message.sender_id === userId.value
}

function formatMessageTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

function formatDuration(value) {
  const total = Number(value || 0)
  const minutes = String(Math.floor(total / 60)).padStart(2, '0')
  const seconds = String(total % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

function callStatusLabel(message) {
  const extra = message.extra || {}
  const base = {
    ringing: '等待接听',
    active: '通话中',
    ended: '通话结束',
    rejected: '已拒绝',
    cancelled: '已取消',
    missed: '未接听',
  }[extra.status] || '通话记录'
  if (message.duration_seconds) {
    return `${base} · ${formatDuration(message.duration_seconds)}`
  }
  return base
}

async function loadMessages() {
  try {
    const response = await getMessages(route.params.id)
    const lastId = messages.value.at(-1)?.id
    conversation.value = response.data.conversation
    messages.value = response.data.list || []
    if (messages.value.at(-1)?.id !== lastId) {
      scrollToBottom()
    }
  } catch (error) {
    const detail = error.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
    }
  }
}

async function pollChatState() {
  await loadMessages()
  await pollCallState()
}

function scrollToBottom() {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight
    }
  })
}

async function sendText() {
  const content = text.value.trim()
  if (!content || sendingText.value) return
  sendingText.value = true
  try {
    await sendChatMessage(route.params.id, { content, content_type: 'text' })
    text.value = ''
    await loadMessages()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
  } finally {
    sendingText.value = false
  }
}

async function uploadAndSend(file, contentType, content = '') {
  const form = new FormData()
  form.append('file', file)
  const uploadResponse = await uploadChatMedia(form)
  const durationSeconds = Math.round(file.__durationSeconds || 0)
  await sendChatMessage(route.params.id, {
    content_type: contentType,
    content,
    media_url: uploadResponse.data.url,
    duration_seconds: durationSeconds || undefined,
  })
}

async function onImageSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    await uploadAndSend(file, 'image')
    await loadMessages()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '图片发送失败')
  } finally {
    event.target.value = ''
  }
}

async function onVideoSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    file.__durationSeconds = await probeMediaDuration(file)
    await uploadAndSend(file, 'video', file.name || '视频消息')
    await loadMessages()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '视频发送失败')
  } finally {
    event.target.value = ''
  }
}

async function toggleAudioRecording() {
  if (audioRecording.value) {
    audioRecorder.value?.stop()
    return
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    ElMessage.error('当前浏览器不支持语音录制')
    return
  }
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    audioRecordingSeconds.value = 0
    const recorder = new MediaRecorder(audioStream)
    audioRecorder.value = recorder
    recorder.ondataavailable = (event) => {
      if (event.data?.size) {
        audioChunks.push(event.data)
      }
    }
    recorder.onstop = async () => {
      const durationSeconds = audioRecordingSeconds.value
      audioRecording.value = false
      window.clearInterval(audioTickTimer)
      stopAudioRecorder()
      if (!audioChunks.length) return
      const blob = new Blob(audioChunks, { type: recorder.mimeType || 'audio/webm' })
      const file = new File([blob], `voice-${Date.now()}.webm`, { type: blob.type || 'audio/webm' })
      file.__durationSeconds = durationSeconds
      try {
        await uploadAndSend(file, 'audio', '语音消息')
        await loadMessages()
        ElMessage.success('语音已发送')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '语音发送失败')
      }
    }
    recorder.start(250)
    audioRecording.value = true
    audioTickTimer = window.setInterval(() => {
      audioRecordingSeconds.value += 1
    }, 1000)
  } catch (error) {
    stopAudioRecorder()
    ElMessage.error('无法使用麦克风')
  }
}

function stopAudioRecorder() {
  if (audioStream) {
    audioStream.getTracks().forEach((track) => track.stop())
    audioStream = null
  }
  audioRecorder.value = null
}

async function onMessageCommand(command, message) {
  if (command !== 'delete') return
  try {
    await ElMessageBox.confirm('删除后这条消息会从双方聊天中消失，确定继续吗？', '删除消息', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteChatMessage(route.params.id, message.id)
    ElMessage.success('消息已删除')
    await loadMessages()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

async function confirmDeleteConversation() {
  try {
    await ElMessageBox.confirm('删除消息后将无法再联系，确定删除这段聊天记录吗？', '删除聊天', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
    await deleteConversation(route.params.id)
    ElMessage.success('聊天已删除')
    router.push('/chat')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

async function startCall(callType) {
  if (currentCall.value) {
    ElMessage.warning('当前已有进行中的通话')
    return
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof RTCPeerConnection === 'undefined') {
    ElMessage.error('当前浏览器不支持音视频通话')
    return
  }
  try {
    const response = await createChatCall(route.params.id, { call_type: callType })
    initCallState(response.data, 'caller')
    await setupPeer(callType)
    const offer = await peer.createOffer()
    await peer.setLocalDescription(offer)
    await sendCallSignal(currentCall.value.id, { type: 'offer', payload: offer.sdp })
    callDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发起通话失败')
    teardownPeer()
  }
}

async function pollCallState() {
  try {
    if (currentCall.value?.id) {
      const response = await getChatCall(currentCall.value.id)
      await syncCall(response.data)
      return
    }

    const response = await getActiveCall(route.params.id)
    const call = response.data.call
    if (call && call.callee_id === userId.value && call.status === 'ringing') {
      incomingCall.value = call
    } else if (!call) {
      incomingCall.value = null
    }
  } catch (error) {
    const detail = error.response?.data?.detail
    if (detail && !detail.includes('删除')) {
      console.warn(detail)
    }
  }
}

function initCallState(call, role) {
  currentCall.value = call
  callRole.value = role
  callDialogVisible.value = true
  callStartedAt.value = call.answered_at || call.started_at || new Date().toISOString()
  callElapsedSeconds.value = 0
  callRecorderStarted = false
  callRecordingUploaded = false
  remoteOfferApplied = false
  remoteAnswerApplied = false
  seenRemoteCandidates.clear()
}

async function acceptIncomingCall() {
  if (!incomingCall.value) return
  try {
    const call = incomingCall.value
    incomingCall.value = null
    initCallState(call, 'callee')
    await setupPeer(call.call_type)
    if (call.offer_sdp) {
      await peer.setRemoteDescription({ type: 'offer', sdp: call.offer_sdp })
      remoteOfferApplied = true
    }
    await acceptChatCall(call.id)
    if (!peer.localDescription) {
      const answer = await peer.createAnswer()
      await peer.setLocalDescription(answer)
      await sendCallSignal(call.id, { type: 'answer', payload: answer.sdp })
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '接听失败')
    teardownPeer()
  }
}

async function rejectIncomingCall() {
  if (!incomingCall.value) return
  try {
    await rejectChatCall(incomingCall.value.id)
    incomingCall.value = null
    ElMessage.success('已拒绝来电')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

async function setupPeer(callType) {
  localStream = await navigator.mediaDevices.getUserMedia({
    audio: true,
    video: callType === 'video',
  })
  remoteStream = new MediaStream()

  peer = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  })

  localStream.getTracks().forEach((track) => {
    peer.addTrack(track, localStream)
  })

  peer.onicecandidate = async (event) => {
    if (event.candidate && currentCall.value?.id) {
      try {
        await sendCallSignal(currentCall.value.id, {
          type: 'ice',
          payload: JSON.stringify(event.candidate.toJSON()),
        })
      } catch (error) {
        console.warn(error)
      }
    }
  }

  peer.ontrack = (event) => {
    event.streams[0].getTracks().forEach((track) => {
      if (!remoteStream.getTracks().find((item) => item.id === track.id)) {
        remoteStream.addTrack(track)
      }
    })
    attachStreams()
    startCallRecorderIfNeeded()
  }

  peer.onconnectionstatechange = () => {
    if (!peer) return
    if (['failed', 'closed', 'disconnected'].includes(peer.connectionState) && currentCall.value?.status === 'active') {
      hangupCurrentCall()
    }
  }

  attachStreams()
}

function attachStreams() {
  nextTick(() => {
    if (localVideo.value && localStream) {
      localVideo.value.srcObject = localStream
    }
    if (remoteVideo.value && remoteStream) {
      remoteVideo.value.srcObject = remoteStream
    }
  })
}

async function syncCall(call) {
  currentCall.value = call
  callStartedAt.value = call.answered_at || call.started_at || callStartedAt.value
  if (['ended', 'rejected', 'cancelled', 'missed'].includes(call.status)) {
    await stopCallRecorderIfNeeded()
    teardownPeer()
    callDialogVisible.value = false
    currentCall.value = null
    await loadMessages()
    if (call.status === 'rejected') {
      ElMessage.warning('对方已拒绝通话')
    }
    return
  }

  if (peer) {
    if (callRole.value === 'caller' && call.answer_sdp && !remoteAnswerApplied) {
      await peer.setRemoteDescription({ type: 'answer', sdp: call.answer_sdp })
      remoteAnswerApplied = true
    }

    if (callRole.value === 'callee' && call.offer_sdp && !remoteOfferApplied) {
      await peer.setRemoteDescription({ type: 'offer', sdp: call.offer_sdp })
      remoteOfferApplied = true
      if (!peer.localDescription) {
        const answer = await peer.createAnswer()
        await peer.setLocalDescription(answer)
        await sendCallSignal(call.id, { type: 'answer', payload: answer.sdp })
      }
    }

    const remoteCandidates = callRole.value === 'caller' ? call.callee_candidates : call.caller_candidates
    if (peer.remoteDescription) {
      for (const candidateText of remoteCandidates || []) {
        if (!candidateText || seenRemoteCandidates.has(candidateText)) continue
        try {
          const parsed = JSON.parse(candidateText)
          await peer.addIceCandidate(parsed)
          seenRemoteCandidates.add(candidateText)
        } catch (error) {
          console.warn(error)
        }
      }
    }

    if (call.status === 'active') {
      startCallRecorderIfNeeded()
    }
  }
}

async function hangupCurrentCall() {
  if (!currentCall.value) return
  const callId = currentCall.value.id
  const status = currentCall.value.status === 'active' ? 'ended' : 'cancelled'
  try {
    await endChatCall(callId, { status })
  } catch (error) {
    console.warn(error)
  }
  await stopCallRecorderIfNeeded()
  teardownPeer()
  callDialogVisible.value = false
  currentCall.value = null
  await loadMessages()
}

function teardownPeer() {
  if (peer) {
    peer.onicecandidate = null
    peer.ontrack = null
    peer.onconnectionstatechange = null
    peer.close()
    peer = null
  }
  if (localStream) {
    localStream.getTracks().forEach((track) => track.stop())
    localStream = null
  }
  if (remoteStream) {
    remoteStream.getTracks().forEach((track) => track.stop())
    remoteStream = null
  }
  if (recorderStream) {
    recorderStream.getTracks().forEach((track) => track.stop())
    recorderStream = null
  }
  if (localVideo.value) {
    localVideo.value.srcObject = null
  }
  if (remoteVideo.value) {
    remoteVideo.value.srcObject = null
  }
  callRecorder = null
  callChunks = []
  callRecorderStarted = false
  callRecordingUploaded = false
  remoteOfferApplied = false
  remoteAnswerApplied = false
  seenRemoteCandidates.clear()
}

function updateCallElapsed() {
  if (!callStartedAt.value) return
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(callStartedAt.value).getTime()) / 1000))
  callElapsedSeconds.value = seconds
}

function startCallRecorderIfNeeded() {
  if (!currentCall.value || callRole.value !== 'caller' || callRecorderStarted || !localStream || !remoteStream) {
    return
  }
  const recordingCallId = currentCall.value.id
  const recordingType = currentCall.value.call_type
  const remoteTracks = remoteStream.getTracks()
  if (!remoteTracks.length) return

  recorderStream = new MediaStream()
  localStream.getAudioTracks().forEach((track) => recorderStream.addTrack(track))
  remoteStream.getAudioTracks().forEach((track) => recorderStream.addTrack(track))

  if (currentCall.value.call_type === 'video') {
    localStream.getVideoTracks().forEach((track) => recorderStream.addTrack(track))
    remoteStream.getVideoTracks().forEach((track) => recorderStream.addTrack(track))
  }

  const preferredTypes = currentCall.value.call_type === 'video'
    ? ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']
    : ['audio/webm;codecs=opus', 'audio/webm']
  const mimeType = preferredTypes.find((item) => MediaRecorder.isTypeSupported?.(item)) || ''
  callChunks = []
  callRecorder = new MediaRecorder(recorderStream, mimeType ? { mimeType } : undefined)
  callRecorder.ondataavailable = (event) => {
    if (event.data?.size) {
      callChunks.push(event.data)
    }
  }
  callRecorder.onstop = async () => {
    if (!callChunks.length || callRecordingUploaded) return
    callRecordingUploaded = true
    const blob = new Blob(callChunks, { type: mimeType || callRecorder.mimeType || 'video/webm' })
    const ext = recordingType === 'video' ? 'webm' : 'webm'
    const file = new File([blob], `call-${Date.now()}.${ext}`, { type: blob.type })
    file.__durationSeconds = callElapsedSeconds.value
    try {
      const form = new FormData()
      form.append('file', file)
      const uploadResponse = await uploadChatMedia(form)
      await attachChatCallRecording(recordingCallId, {
        media_url: uploadResponse.data.url,
        recording_type: recordingType,
        duration_seconds: callElapsedSeconds.value,
      })
    } catch (error) {
      console.warn(error)
    }
  }
  callRecorder.start(1000)
  callRecorderStarted = true
}

async function stopCallRecorderIfNeeded() {
  if (callRecorder && callRecorder.state !== 'inactive') {
    callRecorder.stop()
  }
}

async function probeMediaDuration(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.src = url
    video.onloadedmetadata = () => {
      const duration = Number.isFinite(video.duration) ? Math.round(video.duration) : 0
      URL.revokeObjectURL(url)
      resolve(duration)
    }
    video.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(0)
    }
  })
}
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

.chat-header {
  position: sticky;
  top: 0;
  z-index: 12;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  background: rgba(14, 14, 16, 0.9);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--card-border);
}

.chat-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.chat-header__meta {
  min-width: 0;
}

.chat-header__name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.chat-header__sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.chat-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-banner {
  margin: 12px 16px 0;
  padding: 14px 16px;
  border: 1px solid rgba(48, 209, 88, 0.22);
  background: rgba(48, 209, 88, 0.08);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.chat-banner__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-banner__actions {
  display: flex;
  gap: 10px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px 112px;
}

.chat-empty {
  text-align: center;
  color: var(--text-secondary);
}

.chat-row {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 18px;
}

.chat-row--self {
  justify-content: flex-end;
}

.chat-row__bubble-wrap {
  max-width: min(74vw, 440px);
}

.chat-row__meta-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.chat-row--self .chat-row__meta-line {
  justify-content: flex-end;
}

.chat-row__menu {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  color: var(--text-tertiary);
}

.chat-bubble {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: var(--shadow);
}

.chat-bubble--self {
  background: linear-gradient(135deg, rgba(10, 132, 255, 0.9), rgba(42, 148, 255, 0.72));
  border-color: rgba(10, 132, 255, 0.35);
}

.chat-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
}

.chat-image {
  width: min(280px, 62vw);
  border-radius: 14px;
  overflow: hidden;
}

.chat-media-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: min(280px, 62vw);
}

.chat-media-card--video {
  min-width: min(320px, 68vw);
}

.chat-media-card__title {
  font-weight: 600;
}

.chat-media-card__meta {
  font-size: 12px;
  color: inherit;
  opacity: 0.78;
}

.chat-audio,
.chat-video {
  width: 100%;
  border-radius: 12px;
}

.chat-composer {
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: end;
  padding: 14px 16px 18px;
  background: rgba(14, 14, 16, 0.92);
  backdrop-filter: blur(18px);
  border-top: 1px solid var(--card-border);
}

.chat-composer__toolbar {
  display: flex;
  gap: 8px;
}

.chat-composer__input {
  min-width: 0;
}

.call-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.call-panel__hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.call-panel__identity {
  display: flex;
  align-items: center;
  gap: 14px;
}

.call-panel__name {
  font-size: 18px;
  font-weight: 700;
}

.call-panel__status,
.call-panel__timer {
  font-size: 13px;
  color: var(--text-secondary);
}

.call-stage {
  position: relative;
  min-height: 260px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--card-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
}

.call-stage--video {
  min-height: 360px;
}

.call-stage__remote,
.call-video-screen {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.call-stage__local {
  position: absolute;
  right: 16px;
  bottom: 16px;
  width: 160px;
  height: 120px;
  object-fit: cover;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.35);
  background: rgba(0, 0, 0, 0.45);
}

.call-audio-state {
  height: 100%;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.call-audio-state__icon {
  font-size: 44px;
  color: var(--accent);
}

.call-panel__actions {
  display: flex;
  justify-content: center;
}

@media (max-width: 720px) {
  .chat-header {
    padding: 14px 12px;
  }

  .chat-banner {
    margin: 10px 12px 0;
    flex-direction: column;
    align-items: stretch;
  }

  .chat-banner__actions {
    justify-content: flex-end;
  }

  .chat-composer {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .chat-composer__toolbar,
  .chat-composer__send {
    justify-content: space-between;
  }

  .call-stage__local {
    width: 112px;
    height: 148px;
  }
}
</style>
