<template>
  <div style="padding:24px">
    <div class="users-toolbar">
      <h2 style="margin:0;white-space:nowrap">用户管理</h2>
      <div class="users-filters">
        <el-input v-model="search" placeholder="搜索用户名/邮箱" clearable @clear="load" @keyup.enter="load" style="flex:1;min-width:140px;max-width:260px" />
        <el-button type="primary" @click="showCreate">创建用户</el-button>
      </div>
    </div>

    <!-- Inline status filter tabs -->
    <div class="status-tabs">
      <span class="status-tab" :class="{ active: statusFilter === '' }" @click="statusFilter = ''; load()">全部</span>
      <span class="status-tab" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'; load()">正常</span>
      <span class="status-tab" :class="{ active: statusFilter === 'banned' }" @click="statusFilter = 'banned'; load()">封禁</span>
      <span class="status-tab" :class="{ active: statusFilter === 'deleted' }" @click="statusFilter = 'deleted'; load()">已删除</span>
      <span class="status-tab" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'; load()">含已删除</span>
    </div>

    <el-table :data="users">
      <el-table-column prop="username" label="用户名" min-width="80">
        <template #default="{row}">
          <span>{{ row.username }}</span>
          <el-tag v-if="row.is_admin" size="small" type="danger" effect="dark" style="margin-left:4px">站长</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="140" />
      <el-table-column prop="nickname" label="昵称" min-width="80" />
      <el-table-column label="实名" min-width="70">
        <template #default="{row}">
          <el-tag v-if="row.is_verified" type="success" size="small">已认证</el-tag>
          <el-tag v-else-if="row.verify_status==='pending'" type="warning" size="small">审核中</el-tag>
          <span v-else style="color:var(--text-tertiary);font-size:12px">-</span>
        </template>
      </el-table-column>
      <el-table-column label="位置" min-width="80">
        <template #default="{row}">{{ row.location || '-' }}</template>
      </el-table-column>
      <el-table-column label="VIP" min-width="90">
        <template #default="{row}">{{ row.vip_expires_at ? new Date(row.vip_expires_at).toLocaleDateString() : '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" min-width="60">
        <template #default="{row}">
          <el-tag :type="row.status==='active'?'success':row.status==='banned'?'danger':'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="260" fixed="right">
        <template #default="{row}">
          <div class="action-btns">
            <el-button size="small" type="info" @click="showDetail(row)">详情</el-button>
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <template v-if="!row.is_admin">
              <template v-if="row.status==='active'">
                <el-button size="small" type="danger" @click="setStatus(row,'banned')">封禁</el-button>
                <el-dropdown @command="c=>action(c,row)">
                  <el-button size="small">更多</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="row.vip_expires_at" command="removeVip">取消VIP</el-dropdown-item>
                      <el-dropdown-item command="warn">发送警告</el-dropdown-item>
                      <el-dropdown-item command="delete" style="color:var(--danger)">删除用户</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
              <template v-else-if="row.status==='banned'">
                <el-button size="small" type="success" @click="setStatus(row,'active')">恢复正常</el-button>
                <el-dropdown @command="c=>action(c,row)">
                  <el-button size="small">更多</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="row.vip_expires_at" command="removeVip">取消VIP</el-dropdown-item>
                      <el-dropdown-item command="warn">发送警告</el-dropdown-item>
                      <el-dropdown-item command="delete" style="color:var(--danger)">删除用户</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
              <template v-else-if="row.status==='deleted'">
                <el-button size="small" type="success" @click="setStatus(row,'active')">恢复用户</el-button>
                <el-button size="small" type="danger" @click="action('permDelete',row)">永久删除</el-button>
              </template>
            </template>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next"
      @current-change="load" style="margin-top:16px;justify-content:center" />

    <!-- Create/Edit dialog -->
    <el-dialog v-model="showForm" :title="editingId?'编辑用户':'创建用户'" style="width:min(95vw,540px)">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" :placeholder="editingId?'留空不修改':'必填'" show-password /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="form.gender" style="width:100%"><el-option label="男" value="male" /><el-option label="女" value="female" /></el-select></el-form-item>
        <el-form-item v-if="!editingIsAdmin" label="管理员"><el-switch v-model="form.is_admin" active-text="设为站长" inactive-text="普通用户" /></el-form-item>
        <el-form-item label="VIP天数"><el-input-number v-model="form.vip_days" :min="0" placeholder="设置剩余VIP天数" /></el-form-item>
        <el-form-item v-if="!editingIsAdmin" label="封禁"><el-switch v-model="form.is_banned" active-text="封禁" inactive-text="正常" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showForm=false">取消</el-button><el-button type="primary" @click="submit" :loading="saving">保存</el-button></template>
    </el-dialog>

    <!-- Detail dialog -->
    <el-dialog v-model="showDetailDlg" title="用户详情" style="width:min(95vw,680px)">
      <template v-if="detailUser">
        <!-- 头像 + 实名照片 -->
        <div style="display:flex;gap:20px;align-items:flex-start;margin-bottom:16px;flex-wrap:wrap">
          <div style="text-align:center">
            <el-avatar :src="detailUser.avatar_url||''" :size="72" />
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">头像</div>
          </div>
          <template v-if="detailUser.id_photo">
            <div style="text-align:center">
              <el-image :src="verifyPhotoUrl(detailUser.id_photo)" style="width:72px;height:72px;border-radius:8px" fit="cover" :preview-src-list="[verifyPhotoUrl(detailUser.id_photo)]" />
              <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">实名照片</div>
            </div>
          </template>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID" :span="2">{{ detailUser.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detailUser.nickname||'-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ detailUser.gender==='male'?'男':detailUser.gender==='female'?'女':'-' }}</el-descriptions-item>
          <el-descriptions-item label="所在地">{{ detailUser.location||'未定位' }}</el-descriptions-item>
          <el-descriptions-item label="个人简介">{{ detailUser.bio||'-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailUser.status==='active'?'success':detailUser.status==='banned'?'danger':'info'" size="small">{{ detailUser.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="VIP到期">{{ detailUser.vip_expires_at?new Date(detailUser.vip_expires_at).toLocaleString():'无' }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ detailUser.is_admin?'站长':'普通用户' }}</el-descriptions-item>
          <el-descriptions-item label="警告次数">{{ detailUser.warning_count }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ new Date(detailUser.created_at).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="实名状态">
            <el-tag v-if="detailUser.is_verified" type="success" size="small">已认证</el-tag>
            <el-tag v-else-if="detailUser.verify_status==='pending'" type="warning" size="small">审核中</el-tag>
            <span v-else>未认证</span>
          </el-descriptions-item>
          <el-descriptions-item label="真实姓名">{{ detailUser.real_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="身份证号" :span="2">{{ detailUser.id_card || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { adminListUsers, adminCreateUser, adminUpdateUser, adminDeleteUser, adminToggleStatus, adminRemoveVip, adminWarnUser, adminVerifyPhotoUrl, getUser } from '../api'
import api from '../api'

const authStore = useAuthStore()

const users = ref([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const statusFilter = ref('')
const showForm = ref(false)
const editingId = ref('')
const editingIsAdmin = ref(false)
const saving = ref(false)
const showDetailDlg = ref(false)
const detailUser = ref(null)
const form = reactive({ username:'',email:'',password:'',nickname:'',gender:'',is_admin:false,vip_days:0,is_banned:false })

function getRemainingVipDays(vipExpiresAt) {
  if (!vipExpiresAt) return 0
  const expire = new Date(vipExpiresAt)
  const now = new Date()
  if (Number.isNaN(expire.getTime()) || expire <= now) return 0
  return Math.ceil((expire.getTime() - now.getTime()) / 86400000)
}

load()
async function load() {
  try { const r = await adminListUsers({ search:search.value, status:statusFilter.value||undefined, page:page.value }); users.value=r.data.items||[]; total.value=r.data.total||0 } catch {}
}

function showCreate() {
  editingId.value = ''; editingIsAdmin.value = false
  Object.assign(form, { username:'',email:'',password:'',nickname:'',gender:'',is_admin:false,vip_days:0,is_banned:false })
  showForm.value = true
}
function editUser(row) {
  editingId.value = row.id; editingIsAdmin.value = row.is_admin
  Object.assign(form, {
    username:row.username,
    email:row.email,
    password:'',
    nickname:row.nickname||'',
    gender:row.gender||'',
    is_admin:row.is_admin,
    vip_days:getRemainingVipDays(row.vip_expires_at),
    is_banned:row.status==='banned',
  })
  showForm.value = true
}
async function submit() {
  saving.value = true
  try {
    const body = {
      username:form.username,
      email:form.email,
      nickname:form.nickname,
      gender:form.gender,
      is_admin:form.is_admin,
      status:form.is_banned?'banned':'active',
      vip_days:Number(form.vip_days || 0),
    }
    const pwdChanged = !!form.password
    if (pwdChanged) body.password = form.password
    if (editingId.value) {
      await adminUpdateUser(editingId.value, body)
      ElMessage.success('已更新')
      // If editing own account and password/username changed, force re-login
      if (authStore.user?.id === editingId.value && (pwdChanged || form.username !== authStore.user?.username)) {
        ElMessageBox.alert('账号或密码已修改，请重新登录', '提示', { confirmButtonText: '确定', callback: () => { authStore.logout() } })
      }
    } else {
      await adminCreateUser(body)
      ElMessage.success('已创建')
    }
    showForm.value = false; load()
  } catch(e) { ElMessage.error(e.response?.data?.detail||'操作失败') }
  finally { saving.value = false }
}
async function setStatus(row, status) {
  const labels = { active:'恢复', banned:'封禁', deleted:'删除' }
  try {
    await adminToggleStatus(row.id, { status })
    row.status = status
    ElMessage.success(`已${labels[status] || status}`)
  } catch {}
}
function verifyPhotoUrl(p) {
  return adminVerifyPhotoUrl(p)
}
async function showDetail(row) { try { const r = await getUser(row.id); detailUser.value = r.data; showDetailDlg.value = true } catch {} }
function action(cmd, row) {
  if (cmd==='removeVip') removeVip(row)
  else if (cmd==='warn') warnUser(row)
  else if (cmd==='delete') deleteUser(row)
  else if (cmd==='permDelete') permDelete(row)
}
async function removeVip(row) { try { await adminRemoveVip(row.id); row.vip_expires_at=null; ElMessage.success('VIP已移除') } catch {} }
async function warnUser(row) {
  try {
    const { value } = await ElMessageBox.prompt('警告原因','发送警告',{confirmButtonText:'发送',cancelButtonText:'取消'})
    if (!value) return
    await adminWarnUser(row.id, { reason: value })
    ElMessage.success('警告已发送'); load()
  } catch {}
}
async function deleteUser(row) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.username}" 吗？（可恢复）`,'确认删除',{type:'warning',confirmButtonText:'确认删除',cancelButtonText:'取消'})
    await adminDeleteUser(row.id); ElMessage.success('已删除'); load()
  } catch {}
}
async function permDelete(row) {
  try {
    await ElMessageBox.confirm(`永久删除 "${row.username}" 将无法恢复，确定？`,'永久删除',{type:'error',confirmButtonText:'永久删除',cancelButtonText:'取消'})
    await api.delete(`/admin/users/${row.id}/permanent`)
    ElMessage.success('已永久删除'); load()
  } catch {}
}
</script>

<style scoped>
.users-toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.users-filters { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; justify-content: flex-end; }

.status-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.status-tab {
  padding: 5px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  color: var(--text-secondary);
  user-select: none;
}
.status-tab:hover { border-color: var(--accent); color: var(--accent); }
.status-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.action-btns { display: flex; gap: 4px; flex-wrap: wrap; }
@media (max-width: 768px) {
  .users-toolbar { flex-direction: column; align-items: stretch; }
  .users-filters { justify-content: stretch; }
  .users-filters .el-input { max-width: none !important; }
  .action-btns { gap: 2px; }
  .action-btns .el-button { padding: 4px 8px; font-size: 12px; }
  .status-tabs { gap: 4px; }
  .status-tab { padding: 4px 10px; font-size: 12px; }
}
</style>
