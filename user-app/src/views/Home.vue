<template>
  <div class="page-container">
    <div v-if="!store.isVip" class="glass-card" style="margin-bottom:16px;text-align:center;cursor:pointer" @click="$router.push('/vip')">
      <span style="color:var(--accent);font-weight:600">开通VIP会员，解锁全部功能 →</span>
    </div>

    <!-- Banner carousel -->
    <div v-if="displayBanners.length" class="banner-wrap">
      <div class="banner-track" :style="{ transform: `translateX(-${bannerIdx * 100}%)` }">
        <div v-for="(b, i) in displayBanners" :key="i" class="banner-slide"
          :class="{ 'banner-placeholder': b.isPlaceholder }"
          :style="b.url && !b.isPlaceholder ? { backgroundImage: `url(${b.url})` } : {}"
          @click="b.link ? (b.link.startsWith('/') ? $router.push(b.link) : window.open(b.link, '_blank')) : null">
          <div v-if="b.isPlaceholder" class="banner-content">
            <div class="banner-title">拾光</div>
            <div class="banner-subtitle">遇见美好，拾取时光</div>
          </div>
        </div>
      </div>
      <div v-if="displayBanners.length > 1" class="banner-dots">
        <span v-for="(b, i) in displayBanners" :key="i" class="banner-dot" :class="{ active: i === bannerIdx }" @click="bannerIdx = i"></span>
      </div>
    </div>

    <!-- Text notice -->
    <div v-if="homeNotice" class="home-notice">
      <span>📌</span> {{ homeNotice }}
    </div>

    <!-- Shortcuts -->
    <el-row :gutter="20">
      <el-col :xs="12" :sm="6" v-for="item in shortcuts" :key="item.label">
        <div class="glass-card stat-card" @click="$router.push(item.path)" style="cursor:pointer;padding:28px 16px">
          <el-icon :size="32" :color="item.color"><component :is="item.icon" /></el-icon>
          <div style="font-size:15px;font-weight:600;margin-top:10px">{{ item.label }}</div>
        </div>
      </el-col>
    </el-row>

    <h3 style="margin:28px 0 16px">最新动态</h3>
    <el-empty v-if="!moments.length" description="暂无动态" />
    <div v-for="m in moments" :key="m.id" class="glass-card" style="margin-bottom:14px;cursor:pointer" @click="$router.push(`/moment/${m.id}`)">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <el-avatar :src="userImageUrl(m.user?.avatar_url)" :size="36" />
        <span style="font-weight:600">{{ m.user?.nickname || m.user?.username }}</span>
        <span style="color:var(--text-secondary);font-size:12px;margin-left:auto">{{ new Date(m.created_at).toLocaleDateString() }}</span>
        <el-button v-if="store.user?.id === m.user?.id" size="small" type="danger" @click.stop="delMoment(m)" style="margin-left:8px">删除</el-button>
      </div>
      <div v-if="m.content_text" style="margin-bottom:8px;line-height:1.6;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical">{{ m.content_text }}</div>
      <div v-if="m.images?.length" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">
        <el-image v-for="(img, idx) in m.images.slice(0, 6)" :key="idx" :src="userImageUrl(img.thumb)" style="width:clamp(70px,10vw,100px);height:clamp(70px,10vw,100px);border-radius:8px" fit="cover" :preview-src-list="m.images.map(i=>userImageUrl(i.url))" :initial-index="idx" />
        <div v-if="m.images.length > 6" style="display:flex;align-items:center;justify-content:center;width:clamp(70px,10vw,100px);height:clamp(70px,10vw,100px);background:var(--card-bg);border-radius:8px;font-size:14px;color:var(--text-secondary)">+{{ m.images.length - 6 }}</div>
      </div>
      <div style="display:flex;gap:20px;color:var(--text-secondary);font-size:13px">
        <span><el-icon><StarFilled v-if="m.liked" style="color:#ff9500"/><Star v-else/></el-icon> {{ m.like_count }}</span>
        <span><el-icon><ChatDotSquare /></el-icon> {{ m.comment_count }}</span>
        <span><el-icon><FolderOpened v-if="m.favorited" style="color:#ff9f0a"/><Folder /></el-icon> {{ m.favorite_count || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getFeed, getSiteConfig, deleteMoment, userImageUrl } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ChatDotSquare, Star, Money, StarFilled, Folder, FolderOpened } from '@element-plus/icons-vue'

const store = useAuthStore()
const moments = ref([])
const homeNotice = ref('')
const banners = ref([])
const bannerIdx = ref(0)
let bannerTimer = null

const DEFAULT_BANNERS = [
  { isPlaceholder: true },
  { isPlaceholder: true, color1: '#5e5ce6', color2: '#30d158' },
  { isPlaceholder: true, color1: '#ff9f0a', color2: '#ff453a' },
]

const displayBanners = computed(() => {
  if (banners.value.length) return banners.value
  return DEFAULT_BANNERS
})

const shortcuts = [
  { label: '匹配', icon: Search, path: '/match', color: '#0a84ff' },
  { label: '聊天', icon: ChatDotSquare, path: '/chat', color: '#30d158' },
  { label: '动态', icon: Star, path: '/moments', color: '#ff9f0a' },
  { label: 'VIP', icon: Money, path: '/vip', color: '#ff453a' },
]

onMounted(async () => {
  try {
    const r = await getFeed()
    moments.value = r.data.list || []
  } catch {}
  try {
    const r = await getSiteConfig('home_banners,home_notice')
    if (r.data?.home_notice?.value) homeNotice.value = r.data.home_notice.value
    if (r.data?.home_banners?.value) {
      try { banners.value = JSON.parse(r.data.home_banners.value) } catch {}
    }
  } catch {}
  bannerTimer = setInterval(() => {
    const total = displayBanners.value.length
    if (total > 1) bannerIdx.value = (bannerIdx.value + 1) % total
  }, 4000)
})
onUnmounted(() => clearInterval(bannerTimer))

async function delMoment(m) {
  try {
    await ElMessageBox.confirm('确定删除这条动态？', '删除', { type: 'danger', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteMoment(m.id)
    ElMessage.success('已删除')
    moments.value = moments.value.filter(x => x.id !== m.id)
  } catch {}
}
</script>

<style scoped>
.banner-wrap {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: clamp(12px, 2vw, 24px);
  width: 100%;
  height: clamp(180px, 28vw, 400px);
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
.banner-placeholder {
  background: linear-gradient(135deg, #0a84ff, #5e5ce6);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
}
.banner-content { text-align: center; color: #fff; }
.banner-title { font-size: clamp(24px,4vw,40px); font-weight: 700; letter-spacing: 2px; }
.banner-subtitle { font-size: clamp(12px,2vw,18px); opacity: 0.8; margin-top: 8px; }
.banner-dots {
  position: absolute;
  bottom: 12px;
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
}
</style>
