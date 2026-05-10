<template>
  <div class="chat-page">
    <van-nav-bar :title="otherUser?.nickname || '聊天'" fixed placeholder left-arrow @click-left="$router.back()" />

    <div class="messages" ref="msgList">
      <div class="msg-item" v-for="msg in messages" :key="msg.id" :class="{ 'msg-mine': msg.senderId === userId }">
        <div class="msg-bubble" v-if="msg.contentType === 'text'">{{ msg.content }}</div>
        <van-image v-else-if="msg.contentType === 'image'" width="160" height="160" fit="cover" radius="8" :src="msg.imageUrl" @click="showImagePreview({ images: [msg.imageUrl], startPosition: 0 })" />
      </div>
    </div>

    <div class="input-bar">
      <van-uploader :after-read="onImageSend" preview-size="0">
        <van-icon name="photo-o" size="24" />
      </van-uploader>
      <van-field v-model="inputText" placeholder="输入消息..." @keyup.enter="sendText" />
      <van-button size="small" type="primary" @click="sendText" :disabled="!inputText.trim()">发送</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showImagePreview } from 'vant';
import client from '../api/client';
import { io as socketClient } from 'socket.io-client';

const route = useRoute();
const auth = useAuthStore();
const userId = auth.user?.id;
const otherUser = ref<any>(null);
const messages = ref<any[]>([]);
const inputText = ref('');
const msgList = ref<HTMLElement | null>(null);

let socket: any;

onMounted(async () => {
  const convId = route.params.id as string;

  // 加载消息历史
  try {
    const [msgRes] = await Promise.all([
      client.get(`/conversations/${convId}/messages`),
    ]);
    messages.value = msgRes.data.list || [];
  } catch {}

  // 连接 Socket.io
  socket = socketClient({ auth: { token: localStorage.getItem('accessToken') } });
  socket.emit('chat:join', convId);
  socket.on('chat:message', (msg: any) => {
    messages.value.push(msg);
    scrollToBottom();
  });

  scrollToBottom();
});

onUnmounted(() => {
  socket?.disconnect();
});

function scrollToBottom() {
  nextTick(() => {
    if (msgList.value) msgList.value.scrollTop = msgList.value.scrollHeight;
  });
}

function sendText() {
  if (!inputText.value.trim()) return;
  socket.emit('chat:send', { conversationId: route.params.id, content: inputText.value, contentType: 'text', tempId: Date.now().toString() }, (res: any) => {
    if (res.success) {
      const idx = messages.value.findIndex((m: any) => m.id === res.tempId);
      if (idx >= 0) messages.value[idx] = res.message;
      else messages.value.push(res.message);
    }
  });
  inputText.value = '';
}

async function onImageSend(file: any) {
  // 上传图片
  const form = new FormData();
  form.append('file', file.file || file);
  try {
    const uploadRes = await client.post('/upload/chat-image', form);
    const imageUrl = uploadRes.data.url;
    socket.emit('chat:send', { conversationId: route.params.id, contentType: 'image', imageUrl, tempId: Date.now().toString() });
  } catch {}
}
</script>

<style scoped>
.chat-page { height: 100vh; display: flex; flex-direction: column; background: #f5f5f5; }
.messages { flex: 1; overflow-y: auto; padding: 10px 12px 80px; }
.msg-item { display: flex; margin-bottom: 12px; }
.msg-mine { justify-content: flex-end; }
.msg-bubble { max-width: 70%; padding: 10px 14px; background: #fff; border-radius: 12px; font-size: 14px; line-height: 1.5; }
.msg-mine .msg-bubble { background: #1989fa; color: #fff; }
.input-bar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border-top: 1px solid #eee; position: fixed; bottom: 0; left: 0; right: 0; }
.input-bar .van-field { flex: 1; background: #f5f5f5; border-radius: 20px; padding: 4px 12px; }
</style>
