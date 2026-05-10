<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:20px">仪表盘</h2>
    <el-row :gutter="16">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <div class="glass-card stat-card"><div class="stat-num">{{ s.value }}</div><div class="stat-label">{{ s.label }}</div></div>
      </el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top:20px">
      <el-col :span="8"><div class="glass-card"><h4>最新动态</h4><div v-if="data.latestMoments?.length">{{ data.latestMoments[0]?.text }}</div><el-empty v-else description="暂无" /></div></el-col>
      <el-col :span="8"><div class="glass-card"><h4>最新匹配</h4><div v-if="data.latestMatches?.length">{{ data.latestMatches.length }}条</div><el-empty v-else description="暂无" /></div></el-col>
      <el-col :span="8"><div class="glass-card"><h4>最新用户</h4><div v-if="data.latestUsers?.length" v-for="u in data.latestUsers.slice(0,3)" :key="u.id">{{ u.nickname || u.username }}</div><el-empty v-else description="暂无" /></div></el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminDashboard } from '../../api'

const stats = ref([])
const data = reactive({ latestMoments: [], latestMatches: [], latestUsers: [] })

onMounted(async () => {
  try {
    const res = await adminDashboard()
    const d = res.data
    Object.assign(data, { latestMoments: d.latest_moments || [], latestMatches: d.latest_matches || [], latestUsers: d.latest_users || [] })
    stats.value = [
      { label: '总用户', value: d.total_users }, { label: '今日新增', value: d.today_new_users },
      { label: '活跃VIP', value: d.active_vip }, { label: '今日匹配', value: d.today_matches },
      { label: '待审核', value: d.pending_reviews }, { label: '今日动态', value: d.today_moments },
      { label: '待处理举报', value: d.pending_reports }, { label: '封禁用户', value: d.banned_users },
    ]
  } catch {}
})
</script>
