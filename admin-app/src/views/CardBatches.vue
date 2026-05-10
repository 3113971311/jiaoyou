<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:16px">发卡管理 <el-button type="primary" size="small" @click="showGen=true" style="margin-left:12px">生成卡密</el-button></h2>
    <el-table :data="batches">
      <el-table-column prop="batch_name" label="批次名称" />
      <el-table-column prop="denomination_days" label="面值(天)" width="80" />
      <el-table-column prop="expire_days" label="有效期(天)" width="90" />
      <el-table-column prop="quantity" label="数量" width="60" />
      <el-table-column label="已用/未用/过期" width="150"><template #default="{row}">{{ row.used }} / {{ row.unused }} / {{ row.expired }}</template></el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}"><el-button size="small" type="info" @click="showDetail(row)">详情</el-button><el-button size="small" @click="doExport(row)">导出</el-button></template>
      </el-table-column>
    </el-table>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDlg" :title="detailBatch?.batch_name" width="800px">
      <div style="margin-bottom:12px;display:flex;gap:8px">
        <el-select v-model="detailFilter" @change="loadDetail" style="width:100px">
          <el-option label="全部" value="" /><el-option label="未用" value="unused" /><el-option label="已用" value="used" /><el-option label="过期" value="expired" />
        </el-select>
        <el-button @click="copyAll">一键复制当前页</el-button>
      </div>
      <el-table :data="detailItems" max-height="400">
        <el-table-column prop="card_code" label="卡密" width="220" />
        <el-table-column prop="denomination_days" label="面值" width="60" />
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='unused'?'success':row.status==='used'?'info':'warning'" size="small">{{ {unused:'未用',used:'已用',expired:'过期'}[row.status] }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="140"><template #default="{row}"><el-button size="small" @click="copyOne(row.card_code)">复制</el-button><el-button size="small" type="danger" @click="delCard(row)">删除</el-button></template></el-table-column>
      </el-table>
      <el-pagination :total="detailTotal" v-model:current-page="detailPage" :page-size="30" layout="prev,pager,next" @current-change="loadDetail" style="margin-top:12px;justify-content:center" />
    </el-dialog>

    <!-- 生成弹窗 -->
    <el-dialog v-model="showGen" title="生成卡密批次" width="500px">
      <el-form :model="gen" label-width="100px">
        <el-form-item label="批次名称"><el-input v-model="gen.batch_name" /></el-form-item>
        <el-form-item label="面值天数"><el-input-number v-model="gen.denomination_days" :min="1" /></el-form-item>
        <el-form-item label="销毁天数">
          <el-radio-group v-model="gen.expire_days">
            <el-radio-button :value="3">3天</el-radio-button><el-radio-button :value="7">7天</el-radio-button><el-radio-button :value="30">30天</el-radio-button><el-radio-button :value="90">90天</el-radio-button><el-radio-button :value="180">180天</el-radio-button><el-radio-button :value="360">360天</el-radio-button>
          </el-radio-group>
          <el-input-number v-model="gen.expire_days" :min="1" placeholder="自定义" style="margin-left:8px" />
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="gen.quantity" :min="1" :max="10000" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="gen.note" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showGen=false">取消</el-button><el-button type="primary" @click="doGenerate" :loading="genLoading">生成</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { adminListBatches, adminBatchDetail, adminGenerateCards, adminDeleteCard, adminExportBatch } from '../api'

const batches = ref([])
const showGen = ref(false)
const genLoading = ref(false)
const gen = reactive({ batch_name:'', denomination_days:30, expire_days:7, quantity:10, note:'' })

const showDlg = ref(false)
const detailBatch = ref(null)
const detailItems = ref([])
const detailTotal = ref(0)
const detailPage = ref(1)
const detailFilter = ref('')

loadBatches()

async function loadBatches() { try { const r = await adminListBatches(); batches.value = r.data.items||[] } catch {} }
async function doGenerate() {
  genLoading.value = true
  try { const r = await adminGenerateCards(gen); ElMessage.success(`生成 ${r.data.quantity} 张卡密`); showGen.value=false; loadBatches() } catch(e) { ElMessage.error(e.response?.data?.detail||'生成失败') }
  finally { genLoading.value = false }
}
async function showDetail(row) {
  detailBatch.value = row; detailPage.value = 1; detailFilter.value = ''; showDlg.value = true; await loadDetail()
}
async function loadDetail() {
  if (!detailBatch.value) return
  try { const r = await adminBatchDetail(detailBatch.value.id, { page:detailPage.value, status:detailFilter.value||undefined }); detailItems.value = r.data.items||[]; detailTotal.value = r.data.total||0 } catch {}
}
function copyOne(code) { navigator.clipboard.writeText(code).then(()=>ElMessage.success('已复制')).catch(()=>ElMessage.info(code)) }
function copyAll() { const codes = detailItems.value.map(c=>c.card_code).join('\n'); navigator.clipboard.writeText(codes).then(()=>ElMessage.success(`已复制 ${detailItems.value.length} 张`)).catch(()=>{}) }
async function delCard(row) { try { await adminDeleteCard(row.id); ElMessage.success('已删除'); loadDetail(); loadBatches() } catch {} }
async function doExport(row) {
  try { const r = await adminExportBatch(row.id); const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([r.data])); a.download=row.batch_name+'.csv'; a.click(); ElMessage.success('导出成功') } catch {}
}
</script>
