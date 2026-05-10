<template>
  <div class="users-page">
    <div class="toolbar">
      <h2>用户管理</h2>
      <el-input v-model="search" placeholder="搜索用户名/邮箱/昵称" clearable @clear="load" @keyup.enter="load" style="width:220px" />
      <el-select v-model="statusFilter" @change="load" style="width:110px">
        <el-option label="正常" value="active" />
        <el-option label="封禁" value="banned" />
        <el-option label="已删除" value="deleted" />
        <el-option label="含已删除" value="all" />
      </el-select>
      <el-button type="primary" @click="showCreate">创建用户</el-button>
    </div>

    <el-table :data="users" style="width:100%">
      <el-table-column prop="username" label="用户名" width="100" />
      <el-table-column prop="email" label="邮箱" width="180" />
      <el-table-column prop="nickname" label="昵称" width="100" />
      <el-table-column prop="location" label="位置" width="120">
        <template #default="{ row }">{{ row.location || '-' }}</template>
      </el-table-column>
      <el-table-column label="VIP到期" width="110">
        <template #default="{ row }">{{ row.vipExpiresAt ? new Date(row.vipExpiresAt).toLocaleDateString() : '-' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="70">
        <template #default="{ row }"><el-tag :type="row.status === 'active' ? 'success' : row.status === 'banned' ? 'danger' : 'info'">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="管理员" width="70">
        <template #default="{ row }"><el-tag v-if="row.isAdmin" type="warning" size="small">是</el-tag><span v-else>-</span></template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="info" @click="showUserDetail(row)">详情</el-button>
          <el-button size="small" @click="showEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.status === 'banned' ? 'success' : 'danger'" @click="toggleBan(row)">{{ row.status === 'banned' ? '解封' : '封禁' }}</el-button>
          <el-dropdown @command="(cmd: string) => userAction(cmd, row)" style="margin-left:4px">
            <el-button size="small">更多 ▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="row.vipExpiresAt" command="removeVip">取消VIP</el-dropdown-item>
                <el-dropdown-item command="warn">发送警告</el-dropdown-item>
                <el-dropdown-item command="delete" style="color:#e63946">删除用户</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination :total="total" v-model:current-page="page" :page-size="20" layout="prev,pager,next" @current-change="load" style="margin-top:16px;justify-content:center" />

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="showDetailDlg" title="用户详情" width="700px">
      <template v-if="detailUser">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detailUser.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ detailUser.gender === 'male' ? '男' : detailUser.gender === 'female' ? '女' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="所在地">{{ detailUser.location || '未定位' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailUser.status }}</el-descriptions-item>
          <el-descriptions-item label="VIP到期">{{ detailUser.vipExpiresAt ? new Date(detailUser.vipExpiresAt).toLocaleString() : '无' }}</el-descriptions-item>
          <el-descriptions-item label="警告次数">{{ detailUser.warningCount }}</el-descriptions-item>
          <el-descriptions-item label="管理员">{{ detailUser.isAdmin ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ new Date(detailUser.createdAt).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">{{ detailUser.bio || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="showForm" :title="editingId ? '编辑用户' : '创建用户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" :placeholder="editingId ? '留空则不修改' : '必填'" type="password" show-password /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender"><el-option label="男" value="male" /><el-option label="女" value="female" /></el-select>
        </el-form-item>
        <el-form-item label="管理员"><el-switch v-model="form.isAdmin" /></el-form-item>
        <el-form-item label="VIP天数"><el-input-number v-model="form.vipDays" :min="0" placeholder="赠送VIP天数" /></el-form-item>
        <el-form-item label="封禁状态">
          <el-switch v-model="form.isBanned" active-text="封禁" inactive-text="正常" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="submit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import client from '../api/client';

const users = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const search = ref('');
const statusFilter = ref('');
const showForm = ref(false);
const editingId = ref('');
const saving = ref(false);
const showDetailDlg = ref(false);
const detailUser = ref<any>(null);

const form = reactive({
  username: '', email: '', password: '', nickname: '',
  gender: '', isAdmin: false, vipDays: 0, isBanned: false,
});

onMounted(load);

async function load() {
  try {
    const res = await client.get('/admin/users', { params: { search: search.value, status: statusFilter.value, page: page.value } });
    users.value = res.data.items;
    total.value = res.data.total;
  } catch {}
}

function showCreate() {
  editingId.value = '';
  Object.assign(form, { username: '', email: '', password: '', nickname: '', gender: '', isAdmin: false, vipDays: 0, isBanned: false });
  showForm.value = true;
}

async function showUserDetail(row: any) {
  try {
    const res = await client.get(`/users/${row.id}`);
    detailUser.value = res.data;
    showDetailDlg.value = true;
  } catch {}
}

function showEdit(row: any) {
  editingId.value = row.id;
  Object.assign(form, {
    username: row.username, email: row.email, password: '',
    nickname: row.nickname || '', gender: row.gender || '',
    isAdmin: row.isAdmin, vipDays: 0, isBanned: row.status === 'banned',
  });
  showForm.value = true;
}

async function submit() {
  saving.value = true;
  try {
    const body: any = {
      username: form.username, email: form.email,
      nickname: form.nickname, gender: form.gender,
      isAdmin: form.isAdmin,
      status: form.isBanned ? 'banned' : 'active',
    };
    if (form.password) body.password = form.password;

    if (editingId.value) {
      await client.put(`/admin/users/${editingId.value}`, body);
      ElMessage.success('已更新');
    } else {
      if (!form.password) { ElMessage.warning('密码不能为空'); saving.value = false; return; }
      body.vipDays = form.vipDays;
      await client.post('/admin/users', body);
      ElMessage.success('已创建');
    }
    showForm.value = false;
    load();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || '操作失败');
  } finally { saving.value = false; }
}

function userAction(cmd: string, row: any) {
  if (cmd === 'removeVip') removeVip(row);
  else if (cmd === 'warn') warnUser(row);
  else if (cmd === 'delete') deleteUser(row);
}

async function removeVip(row: any) {
  await client.post(`/admin/users/${row.id}/remove-vip`);
  row.vipExpiresAt = null;
  ElMessage.success('VIP已移除');
}

async function toggleBan(row: any) {
  const newStatus = row.status === 'banned' ? 'active' : 'banned';
  await client.put(`/admin/users/${row.id}/status`, { status: newStatus });
  row.status = newStatus;
  ElMessage.success(newStatus === 'banned' ? '已封禁' : '已解封');
}

async function warnUser(row: any) {
  const { value: reason } = await ElMessageBox.prompt('警告原因', '发送警告', { confirmButtonText: '发送', cancelButtonText: '取消' });
  if (!reason) return;
  try {
    const res = await client.post(`/admin/users/${row.id}/warn`, { reason });
    if (res.data.banned) ElMessage.warning('已累计3次警告，该用户已自动封禁');
    else ElMessage.success(`警告已发送（累计 ${res.data.warningCount} 次）`);
    load();
  } catch {}
}

async function deleteUser(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除用户 "${row.username}" 吗？`, '确认删除', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' });
    await client.delete(`/admin/users/${row.id}`);
    ElMessage.success(`"${row.username}" 已删除`);
    load();
  } catch {}
}
</script>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.toolbar h2 { margin: 0; flex: 1; }
</style>
