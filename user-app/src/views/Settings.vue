<template>
  <div class="page-container" style="max-width:500px;margin:0 auto">
    <h2 style="margin-bottom:16px">编辑资料</h2>
    <div class="glass-card">
      <el-form label-width="60px">
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="form.gender"><el-option label="男" value="male" /><el-option label="女" value="female" /></el-select></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.bio" type="textarea" :rows="3" maxlength="200" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="saveProfile" :loading="saving" style="width:100%">保存</el-button>
    </div>
    <div class="glass-card" style="margin-top:12px">
      <h4>修改密码</h4>
      <el-input v-model="pw.old" type="password" placeholder="原密码" show-password style="margin-bottom:8px" />
      <el-input v-model="pw.new_pwd" type="password" placeholder="新密码" show-password style="margin-bottom:12px" />
      <el-button type="primary" @click="changePw" style="width:100%">修改密码</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { updateProfile, changePwd } from '../api'
const auth = useAuthStore()
const saving = ref(false)
const form = reactive({ nickname:'',gender:'',bio:'' })
const pw = reactive({ old:'',new_pwd:'' })
onMounted(()=>{ const u=auth.user; if(u) Object.assign(form,{nickname:u.nickname||'',gender:u.gender||'',bio:u.bio||''}) })
async function saveProfile() { saving.value=true; try { await updateProfile(form); ElMessage.success('已保存'); auth.fetchMe() } catch(e) { ElMessage.error(e.response?.data?.detail||'保存失败') } finally { saving.value=false } }
async function changePw() { try { await changePwd({old_password:pw.old,new_password:pw.new_pwd}); ElMessage.success('密码已修改'); pw.old=''; pw.new_pwd='' } catch(e) { ElMessage.error(e.response?.data?.detail||'修改失败') } }
</script>
