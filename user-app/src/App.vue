<template>
  <div v-if="!['/login','/buy-card'].includes($route.path) && store.user" class="app">
    <nav class="navbar">
      <router-link to="/" class="logo">拾光</router-link>
      <div class="nav-links">
        <router-link to="/moments">动态</router-link>
        <router-link to="/match">匹配</router-link>
        <router-link to="/chat">聊天</router-link>
        <router-link to="/vip">VIP</router-link>
        <router-link to="/notifications" class="notif-link">
          <el-badge :value="store.unreadCount" :hidden="!store.unreadCount" :max="99" class="notif-badge">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
        </router-link>
        <router-link to="/profile">{{ store.user?.nickname || store.user?.username || '我的' }}</router-link>
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
    <router-view class="fade-in-up" />
  </div>
  <router-view v-else />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { getSiteConfig } from './api'

const store = useAuthStore()
const sysAnnouncement = ref('')
let timer = null

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
.notif-link { position: relative; display: flex; align-items: center; }
.notif-badge :deep(.el-badge__content) {
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 5px;
  top: -4px;
  right: -14px;
}

.notif-banner {
  position: sticky;
  top: 57px;
  z-index: 99;
  background: linear-gradient(135deg, var(--accent), #5e5ce6);
  cursor: pointer;
  animation: bannerPulse 2s ease-in-out infinite;
}
.notif-banner-inner {
  max-width: 1200px;
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
.notif-banner-title {
  font-weight: 600;
  flex-shrink: 0;
}
.notif-banner-content {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.85;
}
.notif-banner-hint {
  flex-shrink: 0;
  font-size: 12px;
  opacity: 0.75;
}

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
</style>
