<template>
  <div style="padding:24px">
    <div style="display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px">
      <h2 style="margin:0;flex:1">发卡管理</h2>
      <el-button type="primary" @click="showGen = true">生成卡密</el-button>
    </div>

    <div v-if="!batches.length" style="margin-top:40px"><el-empty description="暂无卡密批次" /></div>

    <div v-for="b in batches" :key="b.id" class="glass-card batch-card">
      <div class="batch-main" @click="toggleBatch(b)">
        <div class="batch-info">
          <div class="batch-name">{{ b.batch_name }}</div>
          <div class="batch-meta">
            <span>面值 <b>{{ b.denomination_days }}</b> 天</span>
            <span>有效期 <b>{{ b.expire_days }}</b> 天</span>
            <span>共 <b>{{ b.quantity }}</b> 张</span>
          </div>
        </div>
        <div class="batch-stats">
          <span class="stat"><span class="num green">{{ b.unused }}</span> 未用</span>
          <span class="stat"><span class="num blue">{{ b.used }}</span> 已用</span>
          <span class="stat"><span class="num orange">{{ b.expired }}</span> 过期</span>
        </div>
        <div class="batch-actions-top">
          <el-button size="small" @click.stop="doExport(b)">导出</el-button>
          <el-button size="small" type="danger" @click.stop="delBatch(b)">删除</el-button>
          <el-icon :size="18" style="transition:transform 0.3s" :style="{ transform: b._open ? 'rotate(180deg)' : '' }"><ArrowDown /></el-icon>
        </div>
      </div>

      <!-- Expanded codes -->
      <div v-if="b._open" class="batch-codes">
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;align-items:center">
          <el-select v-model="b._filter" @change="loadCodes(b)" size="small" style="width:90px">
            <el-option label="全部" value="" />
            <el-option label="未用" value="unused" />
            <el-option label="已用" value="used" />
            <el-option label="过期" value="expired" />
          </el-select>
          <el-button size="small" @click="copyCodes(b)">复制当前页</el-button>
          <span style="font-size:12px;color:var(--text-secondary);margin-left:auto">共 {{ b._total || 0 }} 条</span>
        </div>
        <div class="code-list">
          <div v-for="c in (b._codes || [])" :key="c.id" class="code-row">
            <code class="code-text">{{ c.card_code }}</code>
            <el-tag :type="c.status==='unused'?'success':c.status==='used'?'info':'warning'" size="small">
              {{ {unused:'未用',used:'已用',expired:'过期'}[c.status] }}
            </el-tag>
            <el-button size="small" @click="copyOne(c.card_code)" style="margin-left:8px">复制</el-button>
            <el-button size="small" type="danger" @click="delCode(b, c)">删除</el-button>
          </div>
        </div>
        <el-pagination
          v-if="b._total > 30"
          :total="b._total"
          v-model:current-page="b._page"
          :page-size="30"
          layout="prev,pager,next"
          @current-change="loadCodes(b)"
          size="small"
          style="margin-top:8px;justify-content:center" />
      </div>
    </div>

    <!-- Generate dialog -->
    <el-dialog v-model="showGen" title="生成卡密批次" style="width:min(95vw,540px)">
      <el-form :model="gen" label-width="90px">
        <el-form-item label="批次名称"><el-input v-model="gen.batch_name" /></el-form-item>
        <el-form-item label="面值天数"><el-input-number v-model="gen.denomination_days" :min="1" /></el-form-item>
        <el-form-item label="销毁天数">
          <el-radio-group v-model="gen.expire_days" size="small">
            <el-radio-button :value="3">3天</el-radio-button>
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
            <el-radio-button :value="90">90天</el-radio-button>
            <el-radio-button :value="180">180天</el-radio-button>
            <el-radio-button :value="360">360天</el-radio-button>
          </el-radio-group>
          <el-input-number v-model="gen.expire_days" :min="1" placeholder="自定义" size="small" style="margin-left:8px;width:100px" />
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="gen.quantity" :min="1" :max="10000" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="gen.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGen = false">取消</el-button>
        <el-button type="primary" @click="doGenerate" :loading="genLoading">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { adminListBatches, adminBatchDetail, adminGenerateCards, adminDeleteCard, adminExportBatch, adminDeleteBatch } from '../api'

const batches = ref([])
const showGen = ref(false)
const genLoading = ref(false)
const gen = reactive({ batch_name:'', denomination_days:30, expire_days:7, quantity:10, note:'' })

loadBatches()

async function loadBatches() {
  try {
    const r = await adminListBatches()
    // Preserve _open state across reloads
    const oldMap = {}
    for (const ob of batches.value) oldMap[ob.id] = { _open: ob._open, _codes: ob._codes, _total: ob._total, _page: ob._page, _filter: ob._filter }
    batches.value = (r.data.items || []).map(b => {
      const old = oldMap[b.id]
      return { ...b, _open: old?._open || false, _codes: old?._codes || [], _total: old?._total || b.quantity, _page: old?._page || 1, _filter: old?._filter || '' }
    })
  } catch {}
}
async function toggleBatch(b) {
  b._open = !b._open
  if (b._open && !b._codes?.length) await loadCodes(b)
}
async function doGenerate() {
  genLoading.value = true
  try { const r = await adminGenerateCards(gen); ElMessage.success(`生成 ${r.data.quantity} 张卡密`); showGen.value = false; loadBatches() }
  catch(e) { ElMessage.error(e.response?.data?.detail||'生成失败') }
  finally { genLoading.value = false }
}
async function loadCodes(batch) {
  try {
    const r = await adminBatchDetail(batch.id, {
      page: batch._page,
      status: batch._filter || undefined
    })
    batch._codes = r.data.items || []
    batch._total = r.data.total || 0
  } catch {}
}
function copyOne(code) { navigator.clipboard.writeText(code).then(() => ElMessage.success('已复制')).catch(() => ElMessage.info(code)) }
function copyCodes(batch) {
  const codes = (batch._codes || []).map(c => c.card_code).join('\n')
  navigator.clipboard.writeText(codes).then(() => ElMessage.success(`已复制 ${batch._codes.length} 张`)).catch(() => {})
}
async function delCode(batch, row) {
  try { await adminDeleteCard(row.id); ElMessage.success('已删除'); loadCodes(batch); loadBatches() } catch {}
}
async function doExport(row) {
  try { const r = await adminExportBatch(row.id); const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([r.data])); a.download = row.batch_name+'.csv'; a.click(); ElMessage.success('导出成功') } catch {}
}
async function delBatch(batch) {
  try {
    await ElMessageBox.confirm(`确认删除批次「${batch.batch_name}」及其所有卡密？此操作不可恢复。`, '删除批次', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'danger' })
    await adminDeleteBatch(batch.id)
    ElMessage.success('批次已删除')
    loadBatches()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.batch-card { padding: 0; overflow: hidden; margin-bottom: 12px; }
.batch-main {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
}
.batch-main:hover { background: rgba(255,255,255,0.02); }
.batch-info { flex: 1; min-width: 0; }
.batch-name { font-size: 16px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.batch-meta { font-size: 13px; color: var(--text-secondary); margin-top: 4px; display: flex; gap: 16px; flex-wrap: wrap; }
.batch-meta b { color: var(--text); }
.batch-stats { display: flex; gap: 14px; }
.stat { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
.num { font-weight: 700; font-size: 16px; }
.num.green { color: var(--success); }
.num.blue { color: var(--accent); }
.num.orange { color: var(--warning); }
.batch-actions-top { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.batch-codes {
  border-top: 1px solid var(--card-border);
  padding: 12px 20px 16px;
}
.code-list { display: flex; flex-direction: column; gap: 4px; max-height: 420px; overflow-y: auto; }
.code-row { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 8px; }
.code-row:hover { background: rgba(255,255,255,0.03); }
.code-text { font-family: monospace; font-size: 14px; letter-spacing: 1px; flex: 1; color: var(--text); }

@media (max-width: 768px) {
  .batch-main { flex-wrap: wrap; gap: 8px; padding: 12px 16px; }
  .batch-stats { width: 100%; }
  .code-text { font-size: 12px; }
}
</style>
