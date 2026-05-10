<template>
  <div class="moments-page">
    <van-nav-bar title="动态" fixed placeholder>
      <template #right><van-icon name="add-o" size="22" @click="showPost = true" /></template>
    </van-nav-bar>

    <div class="feed">
      <div class="moment-card" v-for="m in moments" :key="m.id">
        <div class="mc-header" @click="$router.push(`/profile/${m.user.id}`)">
          <van-image round width="36" height="36" :src="m.user.avatarUrl || '/placeholder.png'" />
          <span class="mc-name">{{ m.user.nickname || m.user.username }}</span>
          <span class="mc-time">{{ formatTime(m.createdAt) }}</span>
        </div>
        <div class="mc-text" v-if="m.contentText">{{ m.contentText }}</div>
        <div class="mc-images" v-if="m.images?.length">
          <van-image v-for="(img, i) in m.images" :key="i" width="100" height="100" fit="cover" radius="6" :src="img.thumb || img.url" @click="previewImage(i, m.images)" />
        </div>
        <div class="mc-actions">
          <span @click="toggleLike(m)"><van-icon :name="m.liked ? 'like' : 'like-o'" /> {{ m.likeCount }}</span>
          <span @click="openComment(m)"><van-icon name="comment-o" /> {{ m.commentCount }}</span>
        </div>
      </div>
      <van-empty v-if="!moments.length" description="暂无动态" />
    </div>

    <!-- 发布弹窗 -->
    <van-popup v-model:show="showPost" position="bottom" :style="{ height: '70%' }" round>
      <div class="post-area">
        <h3>发布动态</h3>
        <van-field v-model="postText" type="textarea" rows="5" placeholder="说点什么..." maxlength="500" show-word-limit />
        <div class="upload-row">
          <input ref="fileInput" type="file" accept="image/*" multiple style="display:none" @change="onFileChange" />
          <van-uploader v-model="postFiles" multiple :max-count="9" @click-upload="onUploadClick" />
        </div>
        <van-button block type="primary" @click="submitPost" :loading="posting">发布</van-button>
      </div>
    </van-popup>

    <!-- 评论弹窗 -->
    <van-popup v-model:show="showComment" position="bottom" :style="{ height: '50%' }" round>
      <div class="comment-area">
        <h3>评论</h3>
        <div class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <strong>{{ c.user?.nickname || c.user?.username }}: </strong>{{ c.content }}
          </div>
        </div>
        <div class="comment-input-row">
          <van-field v-model="commentText" placeholder="写评论..." />
          <van-button size="small" type="primary" @click="submitComment">发送</van-button>
        </div>
      </div>
    </van-popup>

    <van-tabbar v-model="active">
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="search" to="/match">匹配</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/chat">聊天</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { showSuccessToast, showFailToast, showImagePreview } from 'vant';
import client from '../api/client';

const active = ref(0);
const moments = ref<any[]>([]);
const showPost = ref(false);
const postText = ref('');
const postFiles = ref<any[]>([]);
const uploadFiles = ref<File[]>([]);
const posting = ref(false);
const showComment = ref(false);
const commentText = ref('');
const comments = ref<any[]>([]);
const currentMoment = ref<any>(null);

onMounted(() => loadFeed());

async function loadFeed() {
  try {
    const res = await client.get('/moments');
    moments.value = res.data.list || [];
  } catch {}
}

function formatTime(t: string) {
  return new Date(t).toLocaleDateString();
}

const fileInput = ref<HTMLInputElement | null>(null);

function onUploadClick() {
  // 点击 Vant Uploader 时触发原生文件选择
  fileInput.value?.click();
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = input.files;
  if (!files) return;
  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    if (f.size > 10 * 1024 * 1024) {
      showFailToast('图片不能超过10MB');
      continue;
    }
    uploadFiles.value.push(f);
    // 同步更新 Vant Uploader 显示
    postFiles.value.push({ url: URL.createObjectURL(f), file: f, status: 'done', message: '' });
  }
  input.value = ''; // 允许重复选同一文件
}

async function submitPost() {
  if (!postText.value && !uploadFiles.value.length) return;
  posting.value = true;
  try {
    const form = new FormData();
    form.append('content_text', postText.value || '');
    for (const f of uploadFiles.value) {
      form.append('images', f, f.name || 'image.jpg');
    }
    const res = await client.post('/moments', form);
    showSuccessToast(res.data.message || '发布成功');
    showPost.value = false;
    postText.value = '';
    postFiles.value = [];
    uploadFiles.value = [];
    loadFeed();
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '发布失败，请重试');
  } finally { posting.value = false; }
}

async function toggleLike(m: any) {
  try {
    const res = await client.post(`/moments/${m.id}/like`);
    m.liked = res.data.liked;
    m.likeCount = res.data.likeCount;
  } catch {}
}

async function openComment(m: any) {
  currentMoment.value = m;
  showComment.value = true;
  try {
    const res = await client.get(`/moments/${m.id}/comments`);
    comments.value = res.data.list || [];
  } catch {}
}

async function submitComment() {
  if (!commentText.value || !currentMoment.value) return;
  try {
    const res = await client.post(`/moments/${currentMoment.value.id}/comments`, { content: commentText.value });
    comments.value.push(res.data);
    currentMoment.value.commentCount++;
    commentText.value = '';
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '评论失败');
  }
}

function previewImage(i: number, images: any[]) {
  showImagePreview({ images: images.map((img) => img.url || img.thumb), startPosition: i });
}
</script>

<style scoped>
.moments-page { background: #f7f8fa; min-height: 100vh; padding-bottom: 60px; }
.feed { padding: 10px 12px; }
.moment-card { background: #fff; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.mc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.mc-name { font-weight: bold; font-size: 14px; flex: 1; }
.mc-time { font-size: 12px; color: #999; }
.mc-text { font-size: 14px; line-height: 1.6; margin-bottom: 6px; }
.mc-images { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
.mc-actions { display: flex; gap: 20px; font-size: 13px; color: #666; }
.mc-actions span { display: flex; align-items: center; gap: 4px; }
.post-area { padding: 20px; }
.post-area h3 { text-align: center; margin-bottom: 16px; }
.upload-row { margin: 12px 0; }
.comment-area { padding: 20px; display: flex; flex-direction: column; height: 100%; }
.comment-list { flex: 1; overflow-y: auto; }
.comment-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
.comment-input-row { display: flex; align-items: center; gap: 8px; padding-top: 10px; }
</style>
