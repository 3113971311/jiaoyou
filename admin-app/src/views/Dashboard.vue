<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:20px">仪表盘</h2>

    <!-- Clickable stat cards -->
    <el-row :gutter="16">
      <el-col :xs="12" :sm="6" v-for="s in stats" :key="s.type">
        <div class="glass-card stat-card" @click="openDetail(s)">
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-hint">点击查看详情 →</div>
        </div>
      </el-col>
    </el-row>

    <!-- Activity feeds -->
    <el-row :gutter="16" style="margin-top:20px">
      <el-col :xs="24" :md="8">
        <div class="glass-card" style="margin-bottom:16px">
          <h4 style="margin-bottom:8px">最新动态</h4>
          <div v-for="m in data.latest_moments" :key="m.id" style="padding:4px 0;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"><b>{{ m.user }}</b>: {{ m.text }}</div>
          <el-empty v-if="!data.latest_moments?.length" description="暂无" />
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="glass-card" style="margin-bottom:16px">
          <h4 style="margin-bottom:8px">最新匹配</h4>
          <div v-for="m in data.latest_matches" :key="m.id" style="padding:4px 0;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ m.user1 || '用户' }} ↔ {{ m.user2 || '用户' }} <el-tag size="small">{{ m.scope }}</el-tag></div>
          <el-empty v-if="!data.latest_matches?.length" description="暂无" />
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="glass-card" style="margin-bottom:16px">
          <h4 style="margin-bottom:8px">最新用户</h4>
          <div v-for="u in data.latest_users" :key="u.id" style="padding:4px 0;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ u.nickname || u.username }}</div>
          <el-empty v-if="!data.latest_users?.length" description="暂无" />
        </div>
      </el-col>
    </el-row>

    <!-- Drill-down dialog -->
    <el-dialog v-model="showDetail" :title="detailTitle" style="width:min(95vw,800px)">
      <el-table :data="detailItems" max-height="60vh">
        <el-table-column v-for="col in detailCols" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.width || 100" />
      </el-table>
      <el-empty v-if="!detailItems.length" description="暂无数据" />
      <el-pagination v-if="detailTotal > 20" :total="detailTotal" v-model:current-page="detailPage"
        :page-size="20" layout="prev,pager,next" @current-change="loadDetail" style="margin-top:12px;justify-content:center" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminDashboard } from '../api'
import api from '../api'

const stats = ref([])
const data = reactive({ latest_moments: [], latest_matches: [], latest_users: [] })
const showDetail = ref(false)
const detailTitle = ref('')
const detailType = ref('')
const detailItems = ref([])
const detailTotal = ref(0)
const detailPage = ref(1)

const COL_MAP = {
  total_users: [{prop:'c1',label:'用户名',width:120},{prop:'c2',label:'邮箱',width:180},{prop:'c3',label:'昵称',width:100},{prop:'c4',label:'类型',width:80},{prop:'c5',label:'注册日期',width:110}],
  today_new_users: [{prop:'c1',label:'用户名',width:120},{prop:'c2',label:'邮箱',width:180},{prop:'c3',label:'昵称',width:100},{prop:'c4',label:'注册时间',width:110}],
  active_vip: [{prop:'c1',label:'用户名',width:120},{prop:'c2',label:'昵称',width:100},{prop:'c3',label:'VIP到期',width:110},{prop:'c4',label:'剩余',width:80}],
  banned_users: [{prop:'c1',label:'用户名',width:120},{prop:'c2',label:'邮箱',width:180},{prop:'c3',label:'昵称',width:100},{prop:'c4',label:'注册日期',width:110}],
  pending_reviews: [{prop:'c1',label:'类型',width:80},{prop:'c2',label:'图片',width:200},{prop:'c3',label:'提交时间',width:160}],
  pending_reports: [{prop:'c1',label:'目标类型',width:80},{prop:'c2',label:'目标ID',width:160},{prop:'c3',label:'原因',width:200},{prop:'c4',label:'时间',width:160}],
  today_matches: [{prop:'c1',label:'用户1',width:160},{prop:'c2',label:'用户2',width:160},{prop:'c3',label:'范围',width:80},{prop:'c4',label:'匹配时间',width:160}],
  today_moments: [{prop:'c1',label:'用户',width:120},{prop:'c2',label:'内容',width:300},{prop:'c3',label:'时间',width:160}],
}

const LABEL_MAP = {
  total_users:'所有用户', today_new_users:'今日新增用户', active_vip:'活跃VIP用户',
  banned_users:'封禁用户', pending_reviews:'待审核图片', pending_reports:'待处理举报',
  today_matches:'今日匹配', today_moments:'今日动态',
}

const detailCols = ref([])

onMounted(async () => {
  try {
    const res = await adminDashboard()
    const d = res.data
    Object.assign(data, { latest_moments: d.latest_moments||[], latest_matches: d.latest_matches||[], latest_users: d.latest_users||[] })
    stats.value = [
      { type:'total_users', label:'总用户', value:d.total_users },
      { type:'today_new_users', label:'今日新增', value:d.today_new_users },
      { type:'active_vip', label:'活跃VIP', value:d.active_vip },
      { type:'today_matches', label:'今日匹配', value:d.today_matches },
      { type:'pending_reviews', label:'待审核', value:d.pending_reviews },
      { type:'today_moments', label:'今日动态', value:d.today_moments },
      { type:'pending_reports', label:'待处理举报', value:d.pending_reports },
      { type:'banned_users', label:'封禁用户', value:d.banned_users },
    ]
  } catch {}
})

function openDetail(s) {
  if (!s.value) return
  detailTitle.value = LABEL_MAP[s.type] || s.label
  detailType.value = s.type
  detailCols.value = COL_MAP[s.type] || []
  detailPage.value = 1
  showDetail.value = true
  loadDetail()
}
async function loadDetail() {
  try {
    const r = await api.get('/admin/dashboard/detail', { params: { type: detailType.value, page: detailPage.value } })
    detailItems.value = r.data.items || []
    detailTotal.value = r.data.total || 0
  } catch {}
}
</script>

<style scoped>
.stat-card { cursor: pointer; position: relative; }
.stat-card:hover { border-color: var(--accent); }
.stat-hint {
  font-size: 11px; color: var(--text-tertiary); margin-top: 8px;
  opacity: 0; transition: opacity 0.2s;
}
.stat-card:hover .stat-hint { opacity: 1; }
</style>
