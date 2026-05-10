<template>
  <div style="padding:24px">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <h2 style="flex:1;margin:0">用户管理</h2>
      <el-input v-model="search" placeholder="搜索用户名/邮箱" clearable @clear="load" @keyup.enter="load" style="width:200px" />
      <el-select v-model="statusFilter" @change="load" style="width:110px">
        <el-option label="正常" value="active" /><el-option label="封禁" value="banned" /><el-option label="已删除" value="deleted" /><el-option label="含已删除" value="all" />
      </el-select>
      <el-button type="primary" @click="showCreate">创建用户</el-button>
    </div>

    <el-table :data="users">
      <el-table-column prop="username" label="用户名" width="100" />
      <el-table-column prop="email" label="邮箱" width="180" />
      <el-table-column prop="nickname" label="昵称" width="100" />
      <el-table-column prop="location" label="位置" width="100">
        <template #default="{row}">{{ row.location || '-' }}</template>
      </el-table-column>
      <el-table-column label="VIP" width="110">
        <template #default="{row}">{{ row.vip_expires_at ? new Date(row.vip_expires_at).toLocaleDateString() : '-' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="70">
        <template #default="{row}"><el-tag :type="row.status==='active'?'success':row.status==='banned'?'danger':'info'" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{row}">
          <el-button size="small" type="info" @click="showDetail(row)">详情</el-button>
          <el-button size="small" @click="editUser(row)">编辑</el-button>
          <el-button size="small" :type="row.status==='banned'?'success':'danger'" @click="toggleBan(row)">{{ row.status==='banned'?'解封':'封禁' }}</el-button>
          <el-dropdown @command="c=>action(c,row)" style="margin-left:4px">
            <el-button size="small">更多 ▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="row.vip_expires_at" command="removeVip">取消VIP</el-dropdown-item>
                <el-dropdown-item command="warn">发送警告</el-dropdown-item>
                <el-dropdown-item command="delete" style="color:#e63946">删除用户</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next" @current-change="load" style="margin-top:16px;justify-content:center" />

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="showForm" :title="editingId?'编辑用户':'创建用户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" :placeholder="editingId?'留空不修改':'必填'" show-password /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="form.gender"><el-option label="男" value="male" /><el-option label="女" value="female" /></el-select></el-form-item>
        <el-form-item label="管理员"><el-switch v-model="form.is_admin" /></el-form-item>
        <el-form-item label="VIP天数"><el-input-number v-model="form.vip_days" :min="0" placeholder="赠送VIP天数" /></el-form-item>
        <el-form-item label="封禁"><el-switch v-model="form.is_banned" active-text="封禁" inactive-text="正常" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showForm=false">取消</el-button><el-button type="primary" @click="submit" :loading="saving">保存</el-button></template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDlg" title="用户详情" width="600px">
      <template v-if="detailUser">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detailUser.nickname||'-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ detailUser.gender==='male'?'男':detailUser.gender==='female'?'女':'-' }}</el-descriptions-item>
          <el-descriptions-item label="所在地">{{ detailUser.location||'未定位' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailUser.status }}</el-descriptions-item>
          <el-descriptions-item label="VIP到期">{{ detailUser.vip_expires_at?new Date(detailUser.vip_expires_at).toLocaleString():'无' }}</el-descriptions-item>
          <el-descriptions-item label="警告次数">{{ detailUser.warning_count }}</el-descriptions-item>
          <el-descriptions-item label="管理员">{{ detailUser.is_admin?'是':'否' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ new Date(detailUser.created_at).toLocaleString() }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminListUsers, adminCreateUser, adminUpdateUser, adminDeleteUser, adminToggleStatus, adminRemoveVip, adminWarnUser } from '../api'
import { getUser } from '../api'

const users = ref([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const statusFilter = ref('')
const showForm = ref(false)
const editingId = ref('')
const saving = ref(false)
const showDetailDlg = ref(false)
const detailUser = ref(null)
const form = reactive({ username:'',email:'',password:'',nickname:'',gender:'',is_admin:false,vip_days:0,is_banned:false })

load()
async function load() {
  try { const r = await adminListUsers({ search:search.value, status:statusFilter.value||undefined, page:page.value }); users.value=r.data.items||[]; total.value=r.data.total||0 } catch {}
}

function showCreate() {
  editingId.value = ''; Object.assign(form, { username:'',email:'',password:'',nickname:'',gender:'',is_admin:false,vip_days:0,is_banned:false }); showForm.value = true
}
function editUser(row) {
  editingId.value = row.id; Object.assign(form, { username:row.username,email:row.email,password:'',nickname:row.nickname||'',gender:row.gender||'',is_admin:row.is_admin,vip_days:0,is_banned:row.status==='banned' }); showForm.value = true
}
async function submit() {
  saving.value = true
  try {
    const body = { username:form.username, email:form.email, nickname:form.nickname, gender:form.gender, is_admin:form.is_admin, status:form.is_banned?'banned':'active' }
    if (form.password) body.password = form.password
    if (editingId.value) { await adminUpdateUser(editingId.value, body); ElMessage.success('已更新') }
    else { body.vip_days = form.vip_days; await adminCreateUser(body); ElMessage.success('已创建') }
    showForm.value = false; load()
  } catch(e) { ElMessage.error(e.response?.data?.detail||'操作失败') }
  finally { saving.value = false }
}
async function toggleBan(row) {
  const s = row.status==='banned'?'active':'banned'
  try { await adminToggleStatus(row.id, { status:s }); row.status = s; ElMessage.success(s==='banned'?'已封禁':'已解封') } catch {}
}
async function showDetail(row) { try { const r = await getUser(row.id); detailUser.value = r.data; showDetailDlg.value = true } catch {} }
function action(cmd, row) {
  if (cmd==='removeVip') removeVip(row)
  else if (cmd==='warn') warnUser(row)
  else if (cmd==='delete') deleteUser(row)
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
    await ElMessageBox.confirm(`确定删除 "${row.username}" 吗？`,'确认删除',{type:'warning',confirmButtonText:'确认删除',cancelButtonText:'取消'})
    await adminDeleteUser(row.id); ElMessage.success('已删除'); load()
  } catch {}
}
</script>
