<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">审核</h2>

    <!-- 顶部切换：图片 / 实名 -->
    <el-tabs v-model="tab" @tab-change="onTabChange" style="margin-bottom:12px">
      <el-tab-pane label="图片审核" name="image" />
      <el-tab-pane label="实名审核" name="verify" />
    </el-tabs>

    <!-- ========== 图片审核 ========== -->
    <template v-if="tab === 'image'">
      <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <el-select v-model="image_type" placeholder="图片类型" style="width:140px" @change="onImageFilterChange" clearable>
          <el-option label="全部" value="" />
          <el-option label="头像" value="avatar" />
          <el-option label="动态图片" value="moment" />
        </el-select>
        <el-tabs v-model="imageFilter" @tab-change="onImageFilterChange" style="flex:1;min-width:200px">
          <el-tab-pane label="待审" name="pending" />
          <el-tab-pane label="已通过" name="approved" />
          <el-tab-pane label="已拒绝" name="rejected" />
        </el-tabs>
      </div>
      <div style="margin-bottom:12px;display:flex;gap:8px">
        <template v-if="imageFilter==='pending'">
          <el-button type="success" @click="batchApprove" :disabled="!imageSelected.length">批量通过 ({{ imageSelected.length }})</el-button>
          <el-button type="danger" @click="batchReject" :disabled="!imageSelected.length">批量拒绝 ({{ imageSelected.length }})</el-button>
        </template>
        <template v-if="imageFilter==='rejected'">
          <el-button type="danger" @click="batchDelete" :disabled="!imageSelected.length">批量删除 ({{ imageSelected.length }})</el-button>
        </template>
      </div>
      <el-table :data="imageItems" @selection-change="onImageSelect" style="width:100%">
        <el-table-column type="selection" min-width="35" />
        <el-table-column label="缩略图" min-width="90">
          <template #default="{row}"><el-image :src="imgUrl(row.thumbnail_url)" style="width:clamp(40px,8vw,60px);height:clamp(40px,8vw,60px);border-radius:8px" fit="cover" :preview-src-list="[imgUrl(row.image_url)]" /></template>
        </el-table-column>
        <el-table-column label="类型" min-width="70">
          <template #default="{row}">{{ row.image_type==='avatar'?'头像':'动态图片' }}</template>
        </el-table-column>
        <el-table-column label="提交者" min-width="100">
          <template #default="{row}">{{ row.submitter?.nickname || row.submitter?.username || '-' }}</template>
        </el-table-column>
        <el-table-column label="关联内容" min-width="160">
          <template #default="{row}">
            <template v-if="row.related_moment">{{ row.related_moment.content_text?.slice(0, 80) }}</template>
            <template v-else-if="row.related_user">{{ row.related_user.nickname || row.related_user.username }}</template>
            <template v-else>-</template>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="140">
          <template #default="{row}">{{ new Date(row.submitted_at).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="审核备注" min-width="100" v-if="imageFilter!=='pending'">
          <template #default="{row}">{{ row.review_comment || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right">
          <template #default="{row}">
            <template v-if="imageFilter==='pending'">
              <el-button size="small" type="success" @click="approve(row)">通过</el-button>
              <el-button size="small" type="danger" @click="openReject(row)">拒绝</el-button>
            </template>
            <template v-if="imageFilter==='rejected'">
              <el-button size="small" type="danger" @click="removeOne(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination :total="imageTotal" v-model:current-page="imagePage" :page-size="20" layout="prev,pager,next" @current-change="loadImages" style="margin-top:16px;justify-content:center" />

      <el-dialog v-model="rejectVisible" title="拒绝原因" width="400px">
        <el-input v-model="rejectComment" type="textarea" :rows="3" placeholder="填写拒绝原因（可选）" />
        <template #footer>
          <el-button @click="rejectVisible=false">取消</el-button>
          <el-button type="danger" @click="doReject">确认拒绝</el-button>
        </template>
      </el-dialog>
    </template>

    <!-- ========== 实名审核 ========== -->
    <template v-if="tab === 'verify'">
      <el-tabs v-model="verifyFilter" @tab-change="loadVerifications" style="margin-bottom:12px">
        <el-tab-pane label="待审" name="pending" />
        <el-tab-pane label="已通过" name="approved" />
        <el-tab-pane label="已拒绝" name="rejected" />
      </el-tabs>
      <el-table :data="verifyItems" style="width:100%">
        <el-table-column label="用户" min-width="140">
          <template #default="{row}">
            <div style="display:flex;align-items:center;gap:8px">
              <el-avatar :src="row.avatar_url||''" :size="36" />
              <span>{{ row.nickname || row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="real_name" label="姓名" min-width="80" />
        <el-table-column prop="id_card" label="身份证号" min-width="170" />
        <el-table-column label="手持照片" min-width="120">
          <template #default="{row}">
            <el-image v-if="row.id_photo" :src="verifyPhotoUrl(row.id_photo)" style="width:60px;height:60px;border-radius:8px" fit="cover" :preview-src-list="[verifyPhotoUrl(row.id_photo)]" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right">
          <template #default="{row}">
            <template v-if="verifyFilter==='pending'">
              <el-button size="small" type="success" @click="verifyApprove(row)">通过</el-button>
              <el-button size="small" type="danger" @click="verifyReject(row)">拒绝</el-button>
            </template>
            <template v-else>
              <el-button size="small" type="danger" @click="resetVerify(row)">删除记录</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination :total="verifyTotal" v-model:current-page="verifyPage" :page-size="20" layout="prev,pager,next" @current-change="loadVerifications" style="margin-top:16px;justify-content:center" />
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminReviewQueue, adminApprove, adminReject, adminBatchReview, adminBatchDelete, adminImageUrl, adminVerifyPhotoUrl } from '../api'
import api from '../api'

// ── Tab ──
const tab = ref('image')

// ── 图片审核 ──
const imageFilter = ref('pending')
const image_type = ref('')
const imageItems = ref([])
const imageSelected = ref([])
const imagePage = ref(1)
const imageTotal = ref(0)
const rejectVisible = ref(false)
const rejectComment = ref('')
const rejectRow = ref(null)

function imgUrl(p) { return adminImageUrl(p) }
async function loadImages() {
  try {
    const params = { status: imageFilter.value, page: imagePage.value }
    if (image_type.value) params.image_type = image_type.value
    const r = await adminReviewQueue(params)
    imageItems.value = r.data.items || []
    imageTotal.value = r.data.total || 0
  } catch {}
}
function onImageFilterChange() { imagePage.value = 1; loadImages() }
function onImageSelect(rows) { imageSelected.value = rows }
async function approve(row) { try { await adminApprove(row.id); ElMessage.success('已通过'); loadImages() } catch {} }
function openReject(row) { rejectRow.value = row; rejectComment.value = ''; rejectVisible.value = true }
async function doReject() {
  try { await adminReject(rejectRow.value.id, { comment: rejectComment.value }); ElMessage.success('已拒绝'); rejectVisible.value = false; loadImages() } catch {}
}
async function removeOne(row) { try { await adminBatchDelete({ ids: [row.id] }); ElMessage.success('已删除'); loadImages() } catch {} }
async function batchApprove() {
  try { await adminBatchReview({ ids: imageSelected.value.map(i => i.id), action: 'approve' }); ElMessage.success('批量通过'); imageSelected.value = []; loadImages() } catch {}
}
async function batchReject() {
  try { await adminBatchReview({ ids: imageSelected.value.map(i => i.id), action: 'reject' }); ElMessage.success('批量拒绝'); imageSelected.value = []; loadImages() } catch {}
}
async function batchDelete() {
  try { await adminBatchDelete({ ids: imageSelected.value.map(i => i.id) }); ElMessage.success('已删除'); imageSelected.value = []; loadImages() } catch {}
}

// ── 实名审核 ──
const verifyFilter = ref('pending')
const verifyItems = ref([])
const verifyPage = ref(1)
const verifyTotal = ref(0)

function verifyPhotoUrl(p) {
  return adminVerifyPhotoUrl(p)
}
async function loadVerifications() {
  try {
    const r = await api.get('/admin/verifications', { params: { status: verifyFilter.value, page: verifyPage.value } })
    verifyItems.value = r.data.items || []
    verifyTotal.value = r.data.total || 0
  } catch {}
}
async function verifyApprove(row) {
  try { await api.post(`/admin/verifications/${row.id}/review`, { action: 'approve' }); ElMessage.success('已通过'); loadVerifications() } catch {}
}
async function verifyReject(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝认证', { confirmButtonText: '确认拒绝', cancelButtonText: '取消', inputType: 'textarea', inputPlaceholder: '填写拒绝原因...' })
    await api.post(`/admin/verifications/${row.id}/review`, { action: 'reject', comment: value || '' })
    ElMessage.success('已拒绝'); loadVerifications()
  } catch {}
}
async function resetVerify(row) {
  try {
    await ElMessageBox.confirm('确定删除该用户的实名认证记录？', '删除记录', { type: 'danger', confirmButtonText: '删除', cancelButtonText: '取消' })
    await api.post(`/admin/verifications/${row.id}/reset`)
    ElMessage.success('已删除'); loadVerifications()
  } catch {}
}

// ── Init ──
loadImages()
function onTabChange() {
  if (tab.value === 'image') loadImages()
  else loadVerifications()
}
</script>
