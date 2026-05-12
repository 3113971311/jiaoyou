<template>
  <div class="page-container">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
      <el-button @click="$router.push('/')" circle><el-icon><Back /></el-icon></el-button>
      <h2 style="margin:0">实名认证</h2>
    </div>

    <div class="glass-card" style="max-width:min(600px,90vw);margin:0 auto" v-if="!submitted && !status.verified">
      <div style="background:rgba(255,159,10,0.1);border:1px solid rgba(255,159,10,0.3);border-radius:12px;padding:clamp(12px,1.5vw,20px);margin-bottom:20px;text-align:center">
        <div style="font-size:clamp(32px,4vw,48px);margin-bottom:8px">🪪</div>
        <p style="font-weight:700;font-size:clamp(14px,1.3vw,17px);margin-bottom:4px">手持身份证拍照</p>
        <p style="color:var(--text-secondary);font-size:clamp(12px,1vw,14px)">
          请将<strong>身份证正面</strong>置于脸旁，确保<strong>面部和证件信息清晰可见</strong>，不得遮挡或修改
        </p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="真实姓名">
          <el-input v-model="form.real_name" placeholder="与身份证一致" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card" placeholder="18位身份证号码" maxlength="18" />
        </el-form-item>
        <el-form-item label="手持照片">
          <div v-if="preview" style="margin-bottom:8px">
            <img :src="preview" style="max-width:200px;border-radius:8px" />
          </div>
          <el-button @click="fileInput.click()">选择照片</el-button>
          <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="onFile" />
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="submit" :loading="sending" :disabled="!form.real_name || !form.id_card || !uploadFile" style="width:100%;margin-top:8px">
        提交审核
      </el-button>
    </div>

    <div class="glass-card" style="max-width:min(600px,90vw);margin:0 auto;text-align:center" v-else-if="submitted && !status.verified">
      <div style="font-size:clamp(36px,4vw,52px);margin-bottom:12px">📷</div>
      <h3>认证申请已提交</h3>
      <p style="color:var(--text-secondary);margin:12px 0">您的实名认证正在审核中，请耐心等待</p>
    </div>

    <div class="glass-card" style="max-width:min(600px,90vw);margin:0 auto;text-align:center" v-else>
      <div style="font-size:clamp(36px,4vw,52px);margin-bottom:12px">✅</div>
      <h3 style="color:var(--success)">已通过实名认证</h3>
      <p style="color:var(--text-secondary);margin-top:8px">{{ status.real_name }} {{ status.id_card }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { submitVerify, getVerifyStatus } from '../api'

const form = reactive({ real_name: '', id_card: '' })
const uploadFile = ref(null)
const preview = ref('')
const fileInput = ref(null)
const sending = ref(false)
const submitted = ref(false)
const status = reactive({ verified: false, status: '', real_name: '', id_card: '' })

onMounted(async () => {
  try {
    const r = await getVerifyStatus()
    Object.assign(status, r.data)
    if (status.status === 'pending') submitted.value = true
  } catch {}
})

function onFile(e) {
  const f = e.target.files[0]
  if (!f) return
  uploadFile.value = f
  preview.value = URL.createObjectURL(f)
}

async function submit() {
  sending.value = true
  try {
    const fd = new FormData()
    fd.append('real_name', form.real_name)
    fd.append('id_card', form.id_card)
    fd.append('photo', uploadFile.value)
    await submitVerify(fd)
    submitted.value = true
    status.status = 'pending'
    ElMessage.success('已提交，等待审核')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  }
  sending.value = false
}
</script>
