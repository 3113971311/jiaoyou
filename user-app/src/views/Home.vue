<template>
  <div class="page-container">
    <div v-if="!auth.isVip" class="glass-card" style="margin-bottom:16px;text-align:center;cursor:pointer" @click="$router.push('/vip')">
      <span style="color:var(--accent);font-weight:600">开通VIP会员，解锁全部功能 →</span>
    </div>

    <!-- Banner carousel -->
    <div v-if="banners.length" class="banner-wrap">
      <div class="banner-track" :style="{ transform: `translateX(-${bannerIdx * 100}%)` }">
        <div v-for="(b, i) in banners" :key="i" class="banner-slide"
          :style="{ backgroundImage: `url(${b.url})` }"
          @click="b.link && (b.link.startsWith('/') ? $router.push(b.link) : window.open(b.link, '_blank'))">
        </div>
      </div>
      <div v-if="banners.length > 1" class="banner-dots">
        <span v-for="(b, i) in banners" :key="i" class="banner-dot" :class="{ active: i === bannerIdx }" @click="bannerIdx = i"></span>
      </div>
    </div>

    <!-- Text notice -->
    <div v-if="homeNotice" class="home-notice">
      <span>📌</span> {{ homeNotice }}
    </div>

    <!-- Shortcuts -->
    <el-row :gutter="16">
      <el-col :xs="12" :sm="6" v-for="item in shortcuts" :key="item.label">
        <div class="glass-card stat-card" @click="$router.push(item.path)" style="cursor:pointer">
          <el-icon :size="28" :color="item.color"><component :is="item.icon" /></el-icon>
          <div style="font-size:14px;font-weight:600;margin-top:8px">{{ item.label }}</div>
        </div>
      </el-col>
    </el-row>

    <h3 style="margin:24px 0 12px">最新动态</h3>
    <el-empty v-if="!moments.length" description="暂无动态" />
    <div v-for="m in moments" :key="m.id" class="glass-card" style="margin-bottom:12px">
      <div style="font-weight:600">{{ m.user?.nickname || m.user?.username }}</div>
      <div v-if="m.content_text" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ m.content_text.slice(0, 120) }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getFeed, getSiteConfig } from '../api'
import { Search, ChatDotSquare, Star, Money } from '@element-plus/icons-vue'

const auth = useAuthStore()
const moments = ref([])
const homeNotice = ref('')
const banners = ref([])
const bannerIdx = ref(0)
let bannerTimer = null

const shortcuts = [
  { label: '匹配', icon: Search, path: '/match', color: '#0a84ff' },
  { label: '聊天', icon: ChatDotSquare, path: '/chat', color: '#30d158' },
  { label: '动态', icon: Star, path: '/moments', color: '#ff9f0a' },
  { label: 'VIP', icon: Money, path: '/vip', color: '#ff453a' },
]

onMounted(async () => {
  try { const r = await getFeed(); moments.value = r.data.list || [] } catch {}
  try {
    const r = await getSiteConfig('home_banners,home_notice')
    if (r.data?.home_notice?.value) homeNotice.value = r.data.home_notice.value
    if (r.data?.home_banners?.value) {
      try { banners.value = JSON.parse(r.data.home_banners.value) } catch {}
    }
  } catch {}
  if (banners.value.length > 1) {
    bannerTimer = setInterval(() => { bannerIdx.value = (bannerIdx.value + 1) % banners.value.length }, 4000)
  }
})
onUnmounted(() => clearInterval(bannerTimer))
</script>

<style scoped>
.banner-wrap {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 16px;
  aspect-ratio: 3 / 1;
  max-height: 280px;
}
.banner-track {
  display: flex;
  height: 100%;
  transition: transform 0.5s ease;
}
.banner-slide {
  min-width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  cursor: pointer;
}
.banner-dots {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}
.banner-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: all 0.3s;
}
.banner-dot.active { background: #fff; width: 20px; border-radius: 4px; }

.home-notice {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-sm);
  padding: 10px 16px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
