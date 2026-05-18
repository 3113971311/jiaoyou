<template>
  <div class="vip-plan-page">
    <div class="page-head">
      <div>
        <h2>套餐设置</h2>
        <p>价格、专属收款码、首次充值折扣和折扣专用收款码都在这里维护。首次充值优惠按“每个账号每个套餐首充一次”独立计算。</p>
      </div>
      <div class="head-actions">
        <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增套餐</el-button>
      </div>
    </div>

    <div class="glass-card table-shell">
      <el-table :data="plans" v-loading="loading" row-key="id">
        <el-table-column label="排序" prop="sort_order" width="80" />
        <el-table-column label="套餐" min-width="200">
          <template #default="{ row }">
            <div class="plan-name">
              <span>{{ row.title || `${row.days} 天 VIP` }}</span>
              <el-tag v-if="row.badge" size="small" effect="dark">{{ row.badge }}</el-tag>
            </div>
            <div class="plan-desc">{{ row.description || '无描述' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="天数" width="100">
          <template #default="{ row }">{{ row.days }} 天</template>
        </el-table-column>
        <el-table-column label="价格" width="120">
          <template #default="{ row }">
            <span class="price">¥{{ Number(row.price).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="首充优惠" width="150">
          <template #default="{ row }">
            <div class="discount-cell">
              <span v-if="Number(row.first_discount_rate) > 0" class="discount-value">{{ Number(row.first_discount_rate).toFixed(1) }} 折</span>
              <span v-else class="discount-empty">未启用</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="收款码" width="160">
          <template #default="{ row }">
            <div class="qr-stack">
              <div class="qr-row">
                <img v-if="row.payment_qr_url" :src="row.payment_qr_url" alt="标准收款码" class="qr-thumb" />
                <el-tag v-else type="danger" size="small">未配置</el-tag>
                <span class="qr-text">标准</span>
              </div>
              <div class="qr-row">
                <img v-if="row.first_discount_qr_url" :src="row.first_discount_qr_url" alt="首充折扣收款码" class="qr-thumb" />
                <el-tag v-else type="info" size="small">{{ Number(row.first_discount_rate) > 0 ? '未配置' : '无折扣' }}</el-tag>
                <span class="qr-text">首充</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row)" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑套餐' : '新增套餐'" style="width:min(95vw,720px)">
      <el-form :model="form" label-width="108px">
        <el-form-item label="套餐名称">
          <el-input v-model="form.title" placeholder="例如：30 天 VIP" maxlength="50" />
        </el-form-item>
        <el-form-item label="天数">
          <el-input-number v-model="form.days" :min="1" :max="9999" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="标准收款码">
          <div class="qr-editor">
            <div v-if="form.payment_qr_url" class="qr-preview-shell">
              <img :src="form.payment_qr_url" alt="套餐收款码" class="qr-preview" />
            </div>
            <div v-else class="qr-empty">请上传标准收款码</div>
            <div class="qr-actions">
              <el-upload :show-file-list="false" accept="image/*" :http-request="(option) => uploadQr(option, 'payment_qr_url')" :disabled="uploading">
                <el-button :icon="Upload" :loading="uploading">{{ form.payment_qr_url ? '替换标准收款码' : '上传标准收款码' }}</el-button>
              </el-upload>
              <el-button v-if="form.payment_qr_url" :icon="Delete" @click="form.payment_qr_url = ''">清空</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="首次折扣">
          <div class="discount-editor">
            <el-input-number v-model="form.first_discount_rate" :min="0" :max="9.9" :step="0.1" :precision="1" />
            <span class="discount-help">填 0 表示不启用；例如 8.5 表示首充 8.5 折。</span>
          </div>
        </el-form-item>
        <el-form-item label="折扣收款码">
          <div class="qr-editor">
            <div v-if="form.first_discount_qr_url" class="qr-preview-shell">
              <img :src="form.first_discount_qr_url" alt="首次折扣收款码" class="qr-preview" />
            </div>
            <div v-else class="qr-empty">{{ Number(form.first_discount_rate) > 0 ? '请上传首次折扣专用收款码' : '未启用首次折扣' }}</div>
            <div class="qr-actions">
              <el-upload :show-file-list="false" accept="image/*" :http-request="(option) => uploadQr(option, 'first_discount_qr_url')" :disabled="uploading || Number(form.first_discount_rate) <= 0">
                <el-button :icon="Upload" :loading="uploading" :disabled="Number(form.first_discount_rate) <= 0">
                  {{ form.first_discount_qr_url ? '替换折扣收款码' : '上传折扣收款码' }}
                </el-button>
              </el-upload>
              <el-button v-if="form.first_discount_qr_url" :icon="Delete" @click="form.first_discount_qr_url = ''">清空</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="角标">
          <el-input v-model="form.badge" placeholder="例如：热门、最值，可留空" maxlength="20" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus, Refresh, Upload } from '@element-plus/icons-vue'
import {
  adminCreateVipPlan,
  adminDeleteVipPlan,
  adminUpdateVipPlan,
  adminUploadVipPlanQr,
  adminVipPlans,
} from '../api'

const plans = ref([])
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const showDialog = ref(false)
const editingId = ref('')

const form = reactive(emptyForm())

function emptyForm() {
  return {
    days: 30,
    price: 0,
    title: '',
    description: '',
    badge: '',
    payment_qr_url: '',
    first_discount_rate: 0,
    first_discount_qr_url: '',
    sort_order: 10,
    is_active: true,
  }
}

function setForm(data) {
  Object.assign(form, emptyForm(), data)
}

async function load() {
  loading.value = true
  try {
    const r = await adminVipPlans()
    plans.value = r.data.items || []
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '套餐加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = ''
  setForm(emptyForm())
  showDialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  setForm({
    days: row.days,
    price: Number(row.price),
    title: row.title,
    description: row.description,
    badge: row.badge,
    payment_qr_url: row.payment_qr_url || '',
    first_discount_rate: Number(row.first_discount_rate || 0),
    first_discount_qr_url: row.first_discount_qr_url || '',
    sort_order: row.sort_order,
    is_active: row.is_active,
  })
  showDialog.value = true
}

async function uploadQr(option, field) {
  uploading.value = true
  try {
    const { data } = await adminUploadVipPlanQr(option.file)
    form[field] = data.url || ''
    ElMessage.success('收款码已上传')
    option.onSuccess?.(data)
  } catch (e) {
    const message = e.response?.data?.detail || '收款码上传失败'
    ElMessage.error(message)
    option.onError?.(e)
  } finally {
    uploading.value = false
  }
}

async function save() {
  if (!form.payment_qr_url) {
    ElMessage.warning('请先上传标准收款码')
    return
  }
  if (Number(form.first_discount_rate) > 0 && !form.first_discount_qr_url) {
    ElMessage.warning('启用首次折扣时，请上传折扣收款码')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form,
      price: Number(form.price),
      days: Number(form.days),
      first_discount_rate: Number(form.first_discount_rate || 0),
      sort_order: Number(form.sort_order),
    }
    if (editingId.value) await adminUpdateVipPlan(editingId.value, payload)
    else await adminCreateVipPlan(payload)
    ElMessage.success('已保存')
    showDialog.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.title || `${row.days} 天 VIP`}」？`, '删除套餐', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await adminDeleteVipPlan(row.id)
    ElMessage.success('已删除')
    load()
  } catch {
    /* cancelled */
  }
}

load()
</script>

<style scoped>
.vip-plan-page { padding: 24px; }
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.page-head h2 { margin: 0 0 6px; }
.page-head p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  max-width: 800px;
  white-space: normal;
}
.head-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.table-shell { padding: 8px 0; overflow: hidden; }
.plan-name { display: flex; align-items: center; gap: 8px; font-weight: 700; }
.plan-desc {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.price { color: var(--danger); font-weight: 800; }
.discount-cell { font-size: 13px; }
.discount-value { color: var(--warning); font-weight: 700; }
.discount-empty { color: var(--text-tertiary); }
.qr-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.qr-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.qr-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: #fff;
}
.qr-text {
  font-size: 12px;
  color: var(--text-secondary);
}
.qr-editor {
  width: 100%;
}
.discount-editor {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.discount-help,
.qr-help {
  font-size: 12px;
  color: var(--text-tertiary);
}
.qr-preview-shell,
.qr-empty {
  width: 180px;
  height: 180px;
  border-radius: 14px;
  border: 1px dashed var(--card-border);
  background: rgba(255, 255, 255, 0.03);
  display: grid;
  place-items: center;
  overflow: hidden;
}
.qr-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #fff;
}
.qr-empty {
  color: var(--text-secondary);
  font-size: 13px;
  text-align: center;
  padding: 16px;
}
.qr-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .vip-plan-page { padding: 16px; }
  .page-head { flex-direction: column; }
  .head-actions { width: 100%; justify-content: flex-start; }
}
</style>
