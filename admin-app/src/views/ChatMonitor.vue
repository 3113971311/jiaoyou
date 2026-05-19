<template>
  <div class="chat-monitor page-container">
    <div class="chat-monitor__header">
      <div>
        <h2>聊天监控</h2>
        <p>查看所有私聊消息、语音消息、视频消息和通话录音录像。</p>
      </div>
      <div class="chat-monitor__filters">
        <el-input
          v-model="search"
          placeholder="搜索用户昵称、用户名或 ID"
          clearable
          @keyup.enter="loadChats"
        />
        <el-button @click="loadChats">刷新</el-button>
      </div>
    </div>

    <div class="chat-monitor__layout">
      <aside class="glass-card chat-monitor__list">
        <div class="chat-monitor__list-title">会话列表</div>
        <div v-if="!chats.length" class="chat-monitor__empty">暂无聊天记录</div>
        <button
          v-for="chat in chats"
          :key="chat.id"
          type="button"
          class="chat-item"
          :class="{ 'chat-item--active': selectedChat?.id === chat.id }"
          @click="selectChat(chat)"
        >
          <div class="chat-item__top">
            <div class="chat-item__names">
              <span>{{ chat.user1_name }}</span>
              <span class="chat-item__divider">·</span>
              <span>{{ chat.user2_name }}</span>
            </div>
            <span class="chat-item__time">{{ formatDate(chat.last_message_at) }}</span>
          </div>
          <div class="chat-item__preview">{{ chat.preview_text || '暂无消息' }}</div>
          <div class="chat-item__tags">
            <el-tag v-if="chat.contact_blocked" size="small" type="danger">已断联</el-tag>
            <el-tag v-if="chat.deleted_for_user1 || chat.deleted_for_user2" size="small">已删除</el-tag>
          </div>
        </button>
      </aside>

      <section class="glass-card chat-monitor__detail">
        <div v-if="!selectedChat" class="chat-monitor__empty chat-monitor__empty--detail">
          选择左侧会话查看详情
        </div>

        <template v-else>
          <div class="chat-detail__header">
            <div>
              <div class="chat-detail__title">{{ selectedChat.user1_name }} · {{ selectedChat.user2_name }}</div>
              <div class="chat-detail__meta">
                <span>会话 ID: {{ selectedChat.id }}</span>
                <span>最后活跃: {{ formatDate(selectedChat.last_message_at) }}</span>
              </div>
            </div>
            <div class="chat-detail__tags">
              <el-tag v-if="selectedChat.contact_blocked" type="danger">双方已无法再联系</el-tag>
              <el-tag v-if="selectedChat.deleted_for_user1 || selectedChat.deleted_for_user2">存在删除记录</el-tag>
            </div>
          </div>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="消息记录" name="messages">
              <div class="message-list">
                <div v-if="!messages.length" class="chat-monitor__empty">暂无消息</div>
                <div v-for="message in messages" :key="message.id" class="message-card">
                  <div class="message-card__top">
                    <div class="message-card__sender">
                      <strong>{{ message.sender_name }}</strong>
                      <span class="message-card__type">{{ messageTypeLabel(message.content_type) }}</span>
                    </div>
                    <div class="message-card__time">{{ formatDate(message.created_at) }}</div>
                  </div>

                  <div class="message-card__body">
                    <template v-if="message.content_type === 'text'">
                      <div class="message-text">{{ message.content }}</div>
                    </template>

                    <template v-else-if="message.content_type === 'image'">
                      <el-image :src="message.media_url || message.image_url" fit="cover" class="message-image" />
                    </template>

                    <template v-else-if="message.content_type === 'audio' || message.content_type === 'call_audio'">
                      <div class="message-media">
                        <div>{{ message.content || messageTypeLabel(message.content_type) }}</div>
                        <audio v-if="message.media_url" :src="message.media_url" controls preload="metadata" />
                      </div>
                    </template>

                    <template v-else-if="message.content_type === 'video' || message.content_type === 'call_video'">
                      <div class="message-media">
                        <div>{{ message.content || messageTypeLabel(message.content_type) }}</div>
                        <video v-if="message.media_url" :src="message.media_url" controls preload="metadata" class="message-video" />
                      </div>
                    </template>
                  </div>

                  <div class="message-card__footer">
                    <span v-if="message.duration_seconds">时长 {{ formatDuration(message.duration_seconds) }}</span>
                    <el-tag v-if="message.is_deleted" size="small" type="warning">已删除</el-tag>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="通话记录" name="calls">
              <div class="call-list">
                <div v-if="!calls.length" class="chat-monitor__empty">暂无通话记录</div>
                <div v-for="call in calls" :key="call.id" class="call-card">
                  <div class="call-card__header">
                    <div class="call-card__title">
                      {{ call.call_type === 'video' ? '视频通话' : '语音通话' }}
                    </div>
                    <el-tag :type="callTagType(call.status)">{{ callStatusLabel(call.status) }}</el-tag>
                  </div>
                  <div class="call-card__meta">
                    <span>发起人: {{ call.caller_id }}</span>
                    <span>接听人: {{ call.callee_id }}</span>
                    <span>开始: {{ formatDate(call.started_at) }}</span>
                    <span>结束: {{ formatDate(call.ended_at) }}</span>
                    <span v-if="call.duration_seconds">时长: {{ formatDuration(call.duration_seconds) }}</span>
                  </div>
                  <audio
                    v-if="call.recording_url && call.call_type === 'audio'"
                    :src="call.recording_url"
                    controls
                    preload="metadata"
                    class="call-card__audio"
                  />
                  <video
                    v-if="call.recording_url && call.call_type === 'video'"
                    :src="call.recording_url"
                    controls
                    preload="metadata"
                    class="call-card__video"
                  />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { adminChatCalls, adminChatMsgs, adminChats } from '../api'

const search = ref('')
const chats = ref([])
const selectedChat = ref(null)
const messages = ref([])
const calls = ref([])
const activeTab = ref('messages')

onMounted(loadChats)

async function loadChats() {
  try {
    const response = await adminChats({ search: search.value })
    chats.value = response.data || []
    if (!selectedChat.value && chats.value.length) {
      await selectChat(chats.value[0])
    } else if (selectedChat.value) {
      const next = chats.value.find((item) => item.id === selectedChat.value.id)
      if (next) {
        await selectChat(next)
      } else {
        selectedChat.value = null
        messages.value = []
        calls.value = []
      }
    }
  } catch (error) {
    console.warn(error)
  }
}

async function selectChat(chat) {
  selectedChat.value = chat
  activeTab.value = 'messages'
  try {
    const [messageResponse, callResponse] = await Promise.all([
      adminChatMsgs(chat.id),
      adminChatCalls(chat.id),
    ])
    messages.value = messageResponse.data || []
    calls.value = callResponse.data || []
  } catch (error) {
    console.warn(error)
  }
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function formatDuration(value) {
  const total = Number(value || 0)
  const minutes = String(Math.floor(total / 60)).padStart(2, '0')
  const seconds = String(total % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

function messageTypeLabel(type) {
  return {
    text: '文字',
    image: '图片',
    audio: '语音',
    video: '视频',
    call_audio: '语音通话',
    call_video: '视频通话',
  }[type] || type
}

function callStatusLabel(status) {
  return {
    ringing: '等待接听',
    active: '通话中',
    ended: '通话结束',
    rejected: '已拒绝',
    cancelled: '已取消',
    missed: '未接听',
  }[status] || status
}

function callTagType(status) {
  return {
    ended: 'success',
    active: 'primary',
    rejected: 'warning',
    cancelled: 'info',
    missed: 'danger',
  }[status] || ''
}
</script>

<style scoped>
.chat-monitor__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.chat-monitor__header h2 {
  margin: 0;
  font-size: 28px;
}

.chat-monitor__header p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.chat-monitor__filters {
  display: flex;
  gap: 10px;
  width: min(460px, 100%);
}

.chat-monitor__layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 18px;
  min-height: 720px;
}

.chat-monitor__list,
.chat-monitor__detail {
  display: flex;
  flex-direction: column;
  min-height: 720px;
}

.chat-monitor__list-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 14px;
}

.chat-monitor__empty {
  color: var(--text-secondary);
  text-align: center;
  padding: 48px 12px;
}

.chat-monitor__empty--detail {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-item {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  padding: 14px;
  text-align: left;
  color: inherit;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;
  margin-bottom: 10px;
}

.chat-item:hover,
.chat-item--active {
  border-color: rgba(10, 132, 255, 0.3);
  background: rgba(10, 132, 255, 0.08);
}

.chat-item__top,
.chat-item__tags {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-item__names {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
}

.chat-item__divider,
.chat-item__time,
.chat-item__preview {
  color: var(--text-secondary);
  font-size: 12px;
}

.chat-item__preview {
  margin: 8px 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-detail__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 16px;
}

.chat-detail__title {
  font-size: 20px;
  font-weight: 700;
}

.chat-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.chat-detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.message-list,
.call-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-card,
.call-card {
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
}

.message-card__top,
.message-card__footer,
.call-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.message-card__sender {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-card__type,
.message-card__time,
.message-card__footer,
.call-card__meta {
  color: var(--text-secondary);
  font-size: 12px;
}

.message-card__body {
  margin-top: 10px;
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.7;
}

.message-image {
  width: min(260px, 100%);
  border-radius: 12px;
  overflow: hidden;
}

.message-media {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-media audio,
.call-card__audio {
  width: min(360px, 100%);
}

.message-video,
.call-card__video {
  width: min(420px, 100%);
  border-radius: 12px;
}

.call-card__title {
  font-weight: 700;
}

.call-card__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px 12px;
  margin: 12px 0;
}

@media (max-width: 1100px) {
  .chat-monitor__layout {
    grid-template-columns: 1fr;
  }

  .chat-monitor__list,
  .chat-monitor__detail {
    min-height: auto;
  }
}

@media (max-width: 720px) {
  .chat-monitor__header,
  .chat-detail__header {
    flex-direction: column;
  }

  .chat-monitor__filters {
    width: 100%;
  }
}
</style>
