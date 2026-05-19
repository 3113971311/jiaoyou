<template>
  <div class="page-container">
    <div class="chat-list-header">
      <div>
        <div class="chat-list-header__title">消息</div>
        <div class="chat-list-header__sub">查看私聊、语音和视频通话记录</div>
      </div>
      <el-button circle @click="$router.push('/')">
        <el-icon><Back /></el-icon>
      </el-button>
    </div>

    <div v-if="!list.length" class="glass-card chat-list-empty">
      <el-empty description="还没有聊天记录" />
    </div>

    <div v-else class="chat-list">
      <router-link
        v-for="conversation in list"
        :key="conversation.id"
        :to="`/chat/${conversation.id}`"
        class="chat-card"
      >
        <el-avatar :size="52" :src="userImageUrl(conversation.other_user?.avatar_url)" />
        <div class="chat-card__body">
          <div class="chat-card__top">
            <span class="chat-card__name">
              {{ conversation.other_user?.nickname || conversation.other_user?.username || '未命名用户' }}
            </span>
            <span class="chat-card__time">
              {{ conversation.last_message_at ? new Date(conversation.last_message_at).toLocaleString() : '' }}
            </span>
          </div>
          <div class="chat-card__bottom">
            <span class="chat-card__preview">{{ conversation.preview_text || '暂无消息' }}</span>
          </div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Back } from '@element-plus/icons-vue'
import { getConversations, userImageUrl } from '../api'

const list = ref([])

onMounted(async () => {
  try {
    const response = await getConversations()
    list.value = response.data.list || []
  } catch (error) {
    console.warn(error)
  }
})
</script>

<style scoped>
.chat-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.chat-list-header__title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
}

.chat-list-header__sub {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.chat-list-empty {
  text-align: center;
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-card {
  width: 100%;
  border: 1px solid var(--card-border);
  border-radius: 18px;
  background: var(--card-bg);
  box-shadow: var(--shadow);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: inherit;
  text-align: left;
  cursor: pointer;
  text-decoration: none;
  appearance: none;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.chat-card:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 132, 255, 0.22);
  background: var(--card-bg-hover);
}

.chat-card__body {
  min-width: 0;
  flex: 1;
}

.chat-card__top,
.chat-card__bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.chat-card__name {
  font-weight: 700;
  font-size: 16px;
  color: var(--text);
}

.chat-card__time,
.chat-card__preview {
  font-size: 13px;
  color: var(--text-secondary);
}

.chat-card__preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

@media (max-width: 640px) {
  .chat-card {
    align-items: flex-start;
  }

  .chat-card__top,
  .chat-card__bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
