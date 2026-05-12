<template>
  <div style="padding:24px">
    <h2 style="margin-bottom:24px">系统配置</h2>

    <div v-for="group in groups" :key="group.label" style="margin-bottom:28px">
      <h3 style="font-size:16px;color:var(--text-secondary);margin-bottom:12px;font-weight:500">{{ group.label }}</h3>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="item in group.items" :key="item.key">
          <div class="glass-card config-card" @click="editCfg(item)">
            <div class="config-label">{{ item.label }}</div>
            <div class="config-value" :class="{ 'is-empty': !item.value }">
              {{ item.display || '未设置' }}
            </div>
            <div class="config-desc" v-if="item.desc">{{ item.desc }}</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="showEdit" :title="'编辑: ' + editingLabel" style="width:min(95vw,520px)">
      <el-select v-if="editingKey === 'smtp_port'" v-model="editVal" style="width:100%">
        <el-option label="465 (SSL)" value="465" />
        <el-option label="587 (STARTTLS)" value="587" />
        <el-option label="25" value="25" />
      </el-select>
      <el-input v-else-if="editingType === 'password'" v-model="editVal" type="password" show-password placeholder="留空不修改" />
      <el-input v-else-if="editingType === 'textarea'" v-model="editVal" type="textarea" :rows="6" />
      <el-input v-else v-model="editVal" :placeholder="editingDesc" />
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { adminSiteConfigs, adminUpdateConfig } from '../api'

const LABELS = {
  smtp_host:   { label: 'SMTP 服务器',    desc: '邮件发送服务器地址', group: '邮件服务' },
  smtp_port:   { label: 'SMTP 端口',      desc: '465(SSL) / 587(STARTTLS)', group: '邮件服务' },
  smtp_user:   { label: '发件邮箱',       desc: '用于发送验证码和通知', group: '邮件服务' },
  smtp_pass:   { label: '邮箱授权码',     desc: 'QQ邮箱→设置→账户→POP3/SMTP', group: '邮件服务', type: 'password' },
  alipay_app_id:      { label: '支付宝应用 APPID',     desc: '支付宝开放平台应用ID', group: '支付配置' },
  alipay_private_key: { label: '支付宝应用私钥',       desc: 'RSA2，需自己生成密钥对(PKCS8格式)', group: '支付配置', type: 'textarea' },
  alipay_public_key:  { label: '支付宝公钥',           desc: '从支付宝开发者后台下载(非应用公钥)', group: '支付配置', type: 'textarea' },
  site_name:          { label: '网站名称',          desc: '显示在页面标题和导航栏', group: '基础设置' },
  site_subtitle:      { label: '网站副标题',        desc: '显示在首页标题下方', group: '基础设置' },
  announcement_enabled: { label: '启用公告',        desc: '是否显示全站顶部公告', group: '前端展示' },
  announcement_text:  { label: '系统公告内容',      desc: '全站顶部公告栏文字', group: '前端展示', type: 'textarea' },
  home_banners:       { label: '首页轮播图',        desc: 'JSON数组：[{"url":"...","link":"..."}]', group: '前端展示', type: 'textarea' },
  home_notice:        { label: '首页文字公告',      desc: '显示在首页动态上方的文字', group: '前端展示', type: 'textarea' },
}

const GROUPS = ['基础设置', '前端展示', '邮件服务', '支付配置']
const configs = ref([])
const showEdit = ref(false)
const editingKey = ref('')
const editingLabel = ref('')
const editingDesc = ref('')
const editingType = ref('text')
const editVal = ref('')
const saving = ref(false)

const groups = computed(() => {
  const dbMap = {}
  for (const c of configs.value) dbMap[c.config_key] = c
  return GROUPS.map(glabel => {
    const items = []
    for (const [key, meta] of Object.entries(LABELS)) {
      if (meta.group !== glabel) continue
      const db = dbMap[key]
      const isSecret = meta.type === 'password'
      items.push({
        key,
        label: meta.label,
        desc: meta.desc,
        value: db?.config_value || '',
        display: isSecret ? (db?.config_value ? '••••••••' : '') : ((db?.config_value || '').slice(0, 60) || ''),
        type: meta.type || db?.value_type || 'text',
        raw: db?.config_value || '',
      })
    }
    return { label: glabel, items }
  }).filter(g => g.items.length)
})

load()
async function load() {
  try { const r = await adminSiteConfigs(); configs.value = r.data || [] } catch {}
}
function editCfg(item) {
  editingKey.value = item.key
  editingLabel.value = item.label
  editingDesc.value = item.desc
  editingType.value = item.type
  editVal.value = item.raw || ''
  showEdit.value = true
}
async function save() {
  saving.value = true
  try {
    await adminUpdateConfig(editingKey.value, { value: editVal.value, type: editingType.value })
    ElMessage.success('已保存')
    showEdit.value = false
    load()
  } catch(e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}
</script>

<style scoped>
.config-card {
  cursor: pointer;
  padding: 20px;
  margin-bottom: 8px;
  min-height: 90px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.config-card:hover { border-color: var(--accent); }
.config-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.config-value {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.config-value.is-empty {
  color: var(--text-tertiary);
  font-weight: 400;
  font-style: italic;
  font-size: 14px;
}
.config-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
