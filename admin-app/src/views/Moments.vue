<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">动态管理</h2>
    <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width:140px" @change="onFilterChange" clearable>
        <el-option label="全部" value="" />
        <el-option label="待审核" value="pending_review" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-input v-model="search" placeholder="搜索动态内容" style="width:220px" clearable @keyup.enter="onFilterChange" @clear="onFilterChange">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button @click="onFilterChange">搜索</el-button>
    </div>
    <el-table :data="items" style="width:100%" @selection-change="onSelect">
      <el-table-column label="用户" min-width="120">
        <template #default="{row}">
          <div style="display:flex;align-items:center;gap:8px">
            <el-avatar :src="row.user?.avatar_url ? imgUrl(row.user.avatar_url) : ''" :size="32" />
            <span>{{ row.user?.nickname || row.user?.username || '-' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="内容" min-width="200" show-overflow-tooltip>
        <template #default="{row}">{{ row.content_text || '(无文字)' }}</template>
      </el-table-column>
      <el-table-column label="图片" min-width="120">
        <template #default="{row}">
          <div style="display:flex;gap:4px;flex-wrap:wrap">
            <el-image v-for="img in row.images" :key="img.id" :src="imgUrl(img.thumbnail_url)" style="width:40px;height:40px;border-radius:6px" fit="cover" :preview-src-list="[imgUrl(img.public_url||img.image_url)]" />
            <span v-if="!row.images.length" style="color:var(--text-secondary)">-</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="90">
        <template #default="{row}">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="点赞/评论" min-width="90">
        <template #default="{row}">{{ row.like_count }} / {{ row.comment_count }}</template>
      </el-table-column>
      <el-table-column label="发布时间" min-width="140">
        <template #default="{row}">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="200" fixed="right">
        <template #default="{row}">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <template v-if="row.status==='pending_review'">
            <el-button size="small" type="success" @click="reviewMoment(row, 'approve')">通过</el-button>
            <el-button size="small" type="danger" @click="reviewMoment(row, 'reject')">拒绝</el-button>
          </template>
          <el-button size="small" type="danger" @click="deleteMoment(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next" @current-change="load" style="margin-top:16px;justify-content:center" />

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="动态详情" width="600px">
      <template v-if="detail">
        <div style="margin-bottom:12px">
          <span style="font-weight:600">用户：</span>{{ detail.user?.nickname }} ({{ detail.user?.username }})
        </div>
        <div style="margin-bottom:12px">
          <span style="font-weight:600">内容：</span><br/>
          <div style="white-space:pre-wrap;margin-top:4px;padding:8px;background:var(--bg);border-radius:8px">{{ detail.content_text || '(无文字)' }}</div>
        </div>
        <div style="margin-bottom:12px">
          <span style="font-weight:600">图片：</span>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
            <el-image v-for="img in detail.images" :key="img.id" :src="imgUrl(img.public_url||img.thumbnail_url)" style="width:120px;height:120px;border-radius:8px" fit="cover" :preview-src-list="[imgUrl(img.public_url||img.image_url)]" />
            <span v-if="!detail.images.length">无</span>
          </div>
        </div>
        <div style="margin-bottom:12px">
          <span style="font-weight:600">状态：</span>
          <el-tag :type="statusType(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
        </div>
        <div style="margin-bottom:12px">
          <span style="font-weight:600">点赞：</span>{{ detail.like_count }} &nbsp; <span style="font-weight:600">评论：</span>{{ detail.comment_count }}
        </div>
        <div v-if="detail.review_comment" style="margin-bottom:12px">
          <span style="font-weight:600">审核备注：</span>{{ detail.review_comment }}
        </div>
        <div style="margin-bottom:12px">
          <span style="font-weight:600">发布时间：</span>{{ new Date(detail.created_at).toLocaleString() }}
        </div>
        <div v-if="detail.comments?.length" style="margin-bottom:12px">
          <span style="font-weight:600">评论列表：</span>
          <div v-for="c in detail.comments" :key="c.id" style="padding:4px 8px;margin-top:4px;background:var(--bg);border-radius:6px;font-size:13px">{{ c.content }}</div>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editVisible" title="编辑动态" width="500px">
      <template v-if="editForm">
        <el-form label-width="80px">
          <el-form-item label="内容">
            <el-input v-model="editForm.content_text" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="editForm.status">
              <el-option label="待审核" value="pending_review" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
          <el-form-item label="审核备注">
            <el-input v-model="editForm.review_comment" type="textarea" :rows="2" placeholder="可选" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="doEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminListMoments, adminGetMoment, adminUpdateMoment, adminDeleteMoment, adminReviewMoment, adminImageUrl } from '../api'

const statusFilter = ref('')
const search = ref('')
const items = ref([])
const selected = ref([])
const page = ref(1)
const total = ref(0)
const detail = ref(null)
const detailVisible = ref(false)
const editForm = ref(null)
const editVisible = ref(false)

load()

function imgUrl(p) { return p ? adminImageUrl(p) : '' }

function statusLabel(s) {
  return { pending_review: '待审核', approved: '已通过', rejected: '已拒绝' }[s] || s
}
function statusType(s) {
  return { pending_review: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info'
}

async function load() {
  try {
    const params = { page: page.value }
    if (statusFilter.value) params.status = statusFilter.value
    if (search.value) params.search = search.value
    const r = await adminListMoments(params)
    items.value = r.data.items || []
    total.value = r.data.total || 0
  } catch {}
}

function onFilterChange() { page.value = 1; load() }
function onSelect(rows) { selected.value = rows }

async function viewDetail(row) {
  try {
    const r = await adminGetMoment(row.id)
    detail.value = r.data
    detailVisible.value = true
  } catch {}
}

function openEdit(row) {
  editForm.value = {
    id: row.id,
    content_text: row.content_text,
    status: row.status,
    review_comment: row.review_comment || '',
  }
  editVisible.value = true
}

async function doEdit() {
  try {
    await adminUpdateMoment(editForm.value.id, {
      content_text: editForm.value.content_text,
      status: editForm.value.status,
      review_comment: editForm.value.review_comment,
    })
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } catch {}
}

async function reviewMoment(row, action) {
  const title = action === 'approve' ? '确认通过该动态？' : '确认拒绝该动态？'
  try {
    await ElMessageBox.confirm(title, '审核动态', {
      confirmButtonText: action === 'approve' ? '通过' : '拒绝',
      cancelButtonText: '取消',
      type: action === 'approve' ? 'success' : 'warning',
    })
    const comment = action === 'reject' ? '管理员审核未通过' : ''
    await adminReviewMoment(row.id, { action, comment })
    ElMessage.success(action === 'approve' ? '已通过' : '已拒绝')
    load()
  } catch { /* cancelled */ }
}

async function deleteMoment(row) {
  try {
    await ElMessageBox.confirm('确认删除该动态？此操作不可恢复。', '删除动态', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'danger',
    })
    await adminDeleteMoment(row.id)
    ElMessage.success('已删除')
    load()
  } catch { /* cancelled */ }
}
</script>
