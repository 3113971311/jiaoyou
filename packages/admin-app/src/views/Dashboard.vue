<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <el-card shadow="hover"><div class="stat-num">{{ item.value }}</div><div class="stat-label">{{ item.label }}</div></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:20px">
      <el-col :span="8">
        <el-card header="最新动态">
          <div v-if="!data.latestMoments?.length" class="empty">暂无</div>
          <div v-for="m in data.latestMoments" :key="m.id" class="feed-item">
            <strong>{{ m.user }}</strong>: {{ m.text }}
            <small>{{ fmt(m.time) }}</small>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="最新匹配">
          <div v-if="!data.latestMatches?.length" class="empty">暂无</div>
          <div v-for="m in data.latestMatches" :key="m.id" class="feed-item">
            {{ m.user1 }} ↔ {{ m.user2 }}
            <el-tag size="small">{{ m.scope }}</el-tag>
            <small>{{ fmt(m.time) }}</small>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="最新用户">
          <div v-for="u in data.latestUsers" :key="u.id" class="feed-item">
            {{ u.nickname || u.username }}
            <small>{{ fmt(u.time) }}</small>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import client from '../api/client';

interface Stat { label: string; value: number }
const stats = ref<Stat[]>([]);
const data = reactive({ latestMoments: [] as any[], latestMatches: [] as any[], latestUsers: [] as any[] });

onMounted(async () => {
  try {
    const res = await client.get('/admin/dashboard');
    const d = res.data;
    data.latestMoments = d.latestMoments || [];
    data.latestMatches = d.latestMatches || [];
    data.latestUsers = d.latestUsers || [];
    stats.value = [
      { label: '总用户', value: d.totalUsers },
      { label: '今日新增', value: d.todayNewUsers },
      { label: '活跃VIP', value: d.activeVip },
      { label: '今日匹配', value: d.todayMatches },
      { label: '待审核', value: d.pendingReviews },
      { label: '今日动态', value: d.todayMoments },
      { label: '待处理举报', value: d.pendingReports },
      { label: '封禁用户', value: d.bannedUsers },
    ];
  } catch {}
});

function fmt(t: string) { return new Date(t).toLocaleString(); }
</script>

<style scoped>
.dashboard h2 { margin-bottom: 20px; }
.stat-num { font-size: 28px; font-weight: bold; color: #1989fa; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.empty { color: #ccc; text-align: center; padding: 20px; }
.feed-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.feed-item small { display: block; color: #999; margin-top: 2px; }
</style>
