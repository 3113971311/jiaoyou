<template>
  <div class="page">
    <van-nav-bar title="问题反馈" left-arrow fixed placeholder @click-left="$router.back()" />
    <van-form @submit="onSubmit" style="padding:16px">
      <van-cell-group inset>
        <van-field v-model="form.title" label="标题" placeholder="简要描述问题" :rules="[{ required: true }]" />
        <van-field v-model="form.content" label="详细描述" type="textarea" rows="5" placeholder="请详细描述你遇到的问题" :rules="[{ required: true }]" />
        <van-field v-model="form.contact" label="联系方式" placeholder="QQ号或邮箱（选填）" />
      </van-cell-group>
      <div style="margin:20px 0">
        <van-button block type="primary" native-type="submit" :loading="loading">提交反馈</van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { showSuccessToast, showFailToast } from 'vant';
import client from '../api/client';

const form = reactive({ title: '', content: '', contact: '' });
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  try {
    await client.post('/feedback', form);
    showSuccessToast('反馈已提交，站长将通过邮箱与你联系');
    form.title = '';
    form.content = '';
    form.contact = '';
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '提交失败');
  } finally { loading.value = false; }
}
</script>
<style scoped>.page { background: #f7f8fa; min-height: 100vh; }</style>
