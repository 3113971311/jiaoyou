<template>
  <div class="page-container">
    <!-- Profile header -->
    <div class="glass-card" style="text-align:center">
      <el-image :src="userImageUrl(auth.user?.avatar_url)" style="width:clamp(60px,10vw,80px);height:clamp(60px,10vw,80px);border-radius:50%" @click="changeAvatar" />
      <h3 style="margin-top:12px">{{ auth.user?.nickname || auth.user?.username }}</h3>

      <!-- Tags row -->
      <div style="display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-top:8px">
        <el-tag v-if="auth.isVip" type="warning" size="small">VIP会员</el-tag>
        <el-tag v-if="auth.user?.is_verified" type="success" size="small">已实名</el-tag>
        <el-tag v-else-if="auth.user?.verify_status === 'pending'" type="info" size="small">实名审核中</el-tag>
        <el-tag v-if="auth.user?.gender" size="small">{{ auth.user.gender === 'male' ? '男' : '女' }}</el-tag>
      </div>

      <!-- Info rows -->
      <div style="margin-top:12px;font-size:clamp(12px,1.1vw,14px);color:var(--text-secondary);line-height:2">
        <p v-if="auth.user?.location"><el-icon><Location /></el-icon> {{ auth.user.location }}</p>
        <p>{{ auth.user?.bio || '暂无简介' }}</p>
        <p style="color:var(--text-tertiary);font-size:clamp(10px,0.9vw,12px)">
          @{{ auth.user?.username }} · {{ auth.user?.email }} · {{ auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString() : '' }} 加入
        </p>
      </div>
    </div>

    <!-- Menu -->
    <div class="glass-card" style="margin-top:12px">
      <div class="menu-item" @click="$router.push('/following')">关注 <span style="color:var(--text-secondary)">→</span></div>
      <div class="menu-item" @click="$router.push('/followers')">粉丝 <span style="color:var(--text-secondary)">→</span></div>
      <div class="menu-item" @click="$router.push('/vip')">VIP <span style="color:var(--text-secondary)">{{ auth.isVip ? '已开通' : '未开通' }} →</span></div>
    </div>
    <div class="glass-card" style="margin-top:12px">
      <div class="menu-item" @click="$router.push('/verify')">实名认证 <span style="color:var(--text-secondary)">{{ auth.user?.is_verified ? '已认证 ✓' : auth.user?.verify_status === 'pending' ? '审核中...' : '未认证 →' }}</span></div>
      <div class="menu-item" @click="$router.push('/notifications')">通知 →</div>
      <div class="menu-item" @click="$router.push('/settings')">编辑资料 →</div>
      <div class="menu-item" @click="$router.push('/feedback')">问题反馈 →</div>
    </div>

    <!-- Tabs: Likes & Favorites -->
    <div style="margin-top:16px">
      <el-tabs v-model="tab" @tab-change="loadTab">
        <el-tab-pane label="我的点赞" name="likes" />
        <el-tab-pane label="我的收藏" name="favorites" />
      </el-tabs>
    </div>
    <div v-if="tabItems.length === 0 && !tabLoading" style="text-align:center;padding:40px 0;color:var(--text-secondary)">暂无内容</div>
    <div v-for="m in tabItems" :key="m.id" class="glass-card" style="margin-bottom:10px;cursor:pointer" @click="$router.push(`/moment/${m.id}`)">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <el-avatar :src="userImageUrl(m.user?.avatar_url)" :size="30" />
        <span style="font-weight:600;font-size:14px">{{ m.user?.nickname || m.user?.username }}</span>
        <span style="color:var(--text-secondary);font-size:11px;margin-left:auto">{{ new Date(m.created_at).toLocaleDateString() }}</span>
      </div>
      <div v-if="m.content_text" style="font-size:14px;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;margin-bottom:6px">{{ m.content_text }}</div>
      <div v-if="m.images?.length" style="display:flex;gap:4px;flex-wrap:wrap">
        <el-image v-for="(img, idx) in m.images.slice(0,4)" :key="idx" :src="userImageUrl(img.thumb)" style="width:60px;height:60px;border-radius:6px" fit="cover" @click.stop :preview-src-list="m.images.map(i=>userImageUrl(i.url))" :initial-index="idx" />
      </div>
    </div>
    <el-button style="width:100%;margin-top:20px" @click="auth.logout()">退出登录</el-button>
    <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="onAvatarChange" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { uploadAvatar, myLikes, myFavorites, userImageUrl } from '../api'

const auth = useAuthStore()
const avatarInput = ref(null)
const tab = ref('likes')
const tabItems = ref([])
const tabLoading = ref(false)

// 进页面时同步最新用户信息
onMounted(async () => {
  await auth.fetchMe()
  loadTab()
})

function changeAvatar() { avatarInput.value?.click() }
async function onAvatarChange(e) {
  const f = e.target.files[0]; if (!f) return
  const fd = new FormData(); fd.append('file', f)
  try { await uploadAvatar(fd); ElMessage.success('头像已上传，等待审核'); await auth.fetchMe() } catch {}
}

async function loadTab() {
  tabLoading.value = true
  try {
    const fn = tab.value === 'likes' ? myLikes : myFavorites
    const r = await fn({ limit: 50 })
    tabItems.value = r.data.items || []
  } catch {}
  tabLoading.value = false
}
</script>

<style scoped>
.menu-item { padding: 12px 0; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid var(--card-border); }
.menu-item:last-child { border-bottom: none; }
</style>
