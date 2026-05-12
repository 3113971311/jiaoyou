<template>
  <div v-if="!['/login','/buy-card'].includes($route.path) && store.user" class="app">
    <nav class="navbar">
      <div class="nav-left">
        <router-link to="/" class="logo">拾光</router-link>
        <div class="nav-links">
          <router-link to="/">首页</router-link>
          <router-link to="/moments">动态</router-link>
          <router-link to="/match">匹配</router-link>
          <router-link to="/chat">聊天</router-link>
          <router-link to="/vip">VIP</router-link>
        </div>
      </div>
      <div class="nav-right">
        <router-link to="/notifications" class="notif-link">
          <el-badge :value="store.unreadCount" :hidden="!store.unreadCount" :max="99">
            <el-icon :size="22"><Bell /></el-icon>
          </el-badge>
        </router-link>
        <router-link to="/profile" class="nav-user">
          <el-avatar :src="userImageUrl(store.user?.avatar_url)" :size="34" />
          <span>{{ store.user?.nickname || store.user?.username || '我的' }}</span>
        </router-link>
      </div>
    </nav>
    <!-- Floating notification banner -->
    <Transition name="slide-down">
      <div v-if="store.latestNotif" class="notif-banner" @click="$router.push('/notifications')">
        <div class="notif-banner-inner">
          <span class="notif-dot"></span>
          <span class="notif-banner-title">{{ store.latestNotif.title }}</span>
          <span class="notif-banner-content">{{ store.latestNotif.content?.slice(0, 40) }}{{ store.latestNotif.content?.length > 40 ? '...' : '' }}</span>
          <span class="notif-banner-hint">点击查看 →</span>
        </div>
      </div>
    </Transition>
    <!-- System announcement -->
    <div v-if="sysAnnouncement" class="sys-announce">
      <span class="sys-announce-icon">📢</span>
      <span>{{ sysAnnouncement }}</span>
    </div>
    <router-view class="fade-in-up main-content" />

    <!-- 右下角悬浮反馈气泡 -->
    <el-popover placement="top-end" :width="340" trigger="click" v-model:visible="fbVisible">
      <template #reference>
        <div class="feedback-bubble">
          <el-icon :size="22"><ChatLineSquare /></el-icon>
        </div>
      </template>
      <div style="padding:4px 0">
        <p style="font-weight:600;font-size:15px;margin-bottom:12px">问题反馈</p>
        <el-input v-model="fb.title" placeholder="问题标题" style="margin-bottom:8px" />
        <el-input v-model="fb.content" type="textarea" :rows="3" placeholder="描述你遇到的问题..." style="margin-bottom:8px" />
        <el-input v-model="fb.contact" placeholder="QQ/邮箱（站长处理后通知你）" style="margin-bottom:12px" />
        <el-button type="primary" @click="submitFb" :loading="fbSending" style="width:100%">提交反馈</el-button>
        <p style="font-size:11px;color:var(--text-tertiary);margin-top:8px;text-align:center">无法开卡或其他问题？反馈后站长会尽快处理</p>
      </div>
    </el-popover>
  </div>
  <router-view v-else class="full-page" />
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Bell, ChatLineSquare } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth'
import { getSiteConfig, userImageUrl, submitFeedback } from './api'

const store = useAuthStore()
const sysAnnouncement = ref('')
let timer = null

// 反馈气泡
const fbVisible = ref(false)
const fbSending = ref(false)
const fb = reactive({ title: '', content: '', contact: '' })

async function submitFb() {
  if (!fb.title || !fb.content) { ElMessage.warning('请填写标题和问题描述'); return }
  fbSending.value = true
  try {
    await submitFeedback(fb)
    ElMessage.success('反馈已提交，站长会尽快处理')
    fbVisible.value = false
    fb.title = ''; fb.content = ''; fb.contact = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  }
  fbSending.value = false
}

onMounted(async () => {
  if (store.isLoggedIn) {
    store.pollUnread()
    timer = setInterval(() => store.pollUnread(), 15000)
  }
  try {
    const r = await getSiteConfig('announcement_enabled,announcement_text')
    if (r.data?.announcement_enabled?.value === 'true' && r.data?.announcement_text?.value) {
      sysAnnouncement.value = r.data.announcement_text.value
    }
  } catch {}
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.nav-left { display: flex; align-items: center; gap: 28px; }
.nav-right { display: flex; align-items: center; gap: clamp(10px, 1.5vw, 20px); }
.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: clamp(13px, 1.2vw, 15px);
  transition: color 0.2s;
}
.nav-user:hover { color: var(--accent); }
.notif-link { display: inline-flex; align-items: center; justify-content: center; line-height: 1; color: var(--text-secondary); text-decoration: none; }
.notif-link:hover { color: var(--accent); }
.notif-link .el-badge { display: inline-flex; align-items: center; line-height: 1; }

.notif-banner {
  position: sticky;
  top: 57px;
  z-index: 99;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  cursor: pointer;
  animation: bannerPulse 2s ease-in-out infinite;
}
.notif-banner-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #fff;
  overflow: hidden;
  white-space: nowrap;
}
.notif-dot {
  width: 8px; height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: dotBlink 1s ease-in-out infinite;
  flex-shrink: 0;
}
.notif-banner-title { font-weight: 600; flex-shrink: 0; }
.notif-banner-content {
  flex: 1; overflow: hidden; text-overflow: ellipsis; opacity: 0.85;
}
.notif-banner-hint { flex-shrink: 0; font-size: 12px; opacity: 0.75; }

@keyframes bannerPulse {
  0%, 100% { box-shadow: 0 2px 12px rgba(10, 132, 255, 0.3); }
  50% { box-shadow: 0 2px 24px rgba(10, 132, 255, 0.6); }
}
@keyframes dotBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.slide-down-enter-active { transition: all 0.3s ease; }
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from { transform: translateY(-100%); opacity: 0; }
.slide-down-leave-to { transform: translateY(-100%); opacity: 0; }

.sys-announce {
  background: rgba(255, 159, 10, 0.12);
  border-bottom: 1px solid rgba(255, 159, 10, 0.2);
  padding: 8px 24px;
  font-size: 13px;
  color: var(--warning);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sys-announce-icon { margin-right: 6px; }
.main-content { flex: 1; }
.full-page { min-height: 100vh; display: flex; flex-direction: column; }

/* 右下角悬浮反馈气泡 */
.feedback-bubble {
  position: fixed;
  bottom: clamp(20px, 3vw, 36px);
  right: clamp(20px, 3vw, 36px);
  width: clamp(44px, 5vw, 56px);
  height: clamp(44px, 5vw, 56px);
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(10, 132, 255, 0.4);
  z-index: 1000;
  transition: transform 0.3s, box-shadow 0.3s;
}
.feedback-bubble:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 28px rgba(10, 132, 255, 0.6);
}
</style>
