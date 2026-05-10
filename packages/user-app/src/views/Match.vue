<template>
  <div class="match-page">
    <van-nav-bar title="匹配交友" fixed placeholder />

    <div class="match-content">
      <!-- 未在匹配中 -->
      <div class="match-setup" v-if="!status.isMatching && !status.isMatched">
        <van-cell-group inset>
          <van-field name="scope" label="匹配范围">
            <template #input>
              <van-radio-group v-model="scope" direction="horizontal">
                <van-radio name="city">同城</van-radio>
                <van-radio name="province">同省</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field name="gender" label="期望性别">
            <template #input>
              <van-radio-group v-model="preferGender" direction="horizontal">
                <van-radio name="male">男</van-radio>
                <van-radio name="female">女</van-radio>
              </van-radio-group>
            </template>
          </van-field>
        </van-cell-group>
        <div class="match-btn-area">
          <van-button block type="primary" @click="startMatch" :loading="matching" size="large">开始匹配</van-button>
          <p class="hint">选择匹配范围和性别后开始</p>
        </div>
      </div>

      <!-- 匹配中 -->
      <div class="match-waiting" v-if="status.isMatching">
        <van-loading size="60" />
        <h3>正在为你匹配...</h3>
        <p>已等待 {{ waitTime }}，匹配成功后会通知你</p>
        <p class="match-info">范围：{{ scope === 'city' ? '同城' : '同省' }}</p>
        <van-button type="default" @click="cancelMatch" :loading="cancelling">取消匹配</van-button>
      </div>

      <!-- 已匹配 -->
      <div class="match-done" v-if="status.isMatched && status.matchedUser">
        <van-image round width="80" height="80" :src="status.matchedUser.avatarUrl || ''" />
        <h3>配对成功!</h3>
        <p>{{ status.matchedUser.nickname || status.matchedUser.username }}</p>
        <van-button type="primary" block @click="$router.push('/chat')">去聊天</van-button>
        <van-button type="default" block @click="closeMatch" style="margin-top:10px">重新匹配</van-button>
      </div>
    </div>

    <van-tabbar v-model="active">
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="search" to="/match">匹配</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/chat">聊天</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted, computed } from 'vue';
import { showFailToast, showSuccessToast } from 'vant';
import client from '../api/client';

const active = ref(1);
const scope = ref('city');
const preferGender = ref('');
const matching = ref(false);
const cancelling = ref(false);
const status = reactive({ isMatching: false, isMatched: false, matchedUser: null as any, expiresAt: null as string | null });
const waitTime = ref('0秒');
let pollTimer: any = null;
let waitTimer: any = null;
let matchStartedAt: number = 0;

onMounted(loadStatus);

async function loadStatus() {
  try {
    const res = await client.get('/match/status');
    Object.assign(status, res.data);
    if (status.isMatching) startPolling();
  } catch {}
}

onUnmounted(() => { stopPolling(); });

function startPolling() {
  stopPolling();
  matchStartedAt = Date.now();
  updateWaitTime();
  waitTimer = setInterval(updateWaitTime, 1000);
  pollTimer = setInterval(async () => {
    try {
      const res = await client.get('/match/status');
      Object.assign(status, res.data);
      if (!res.data.isMatching) stopPolling();
    } catch {}
  }, 8000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  if (waitTimer) { clearInterval(waitTimer); waitTimer = null; }
}

function updateWaitTime() {
  const elapsed = Math.floor((Date.now() - matchStartedAt) / 1000);
  const min = Math.floor(elapsed / 60);
  const sec = elapsed % 60;
  waitTime.value = min > 0 ? `${min}分${sec}秒` : `${sec}秒`;
}

async function startMatch() {
  matching.value = true;
  try {
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        await doMatch(pos.coords.latitude, pos.coords.longitude);
      },
      async () => {
        // GPS 失败，尝试用已保存的定位
        const me = await client.get('/auth/me');
        if (me.data.location) {
          try {
            const geoRes = await client.get('/geocode/search', { params: { q: me.data.location } });
            if (geoRes.data.lat) {
              await doMatch(geoRes.data.lat, geoRes.data.lng);
              return;
            }
          } catch {}
        }
        showFailToast('无法获取定位，请先在个人资料中设置所在地');
        matching.value = false;
      },
      { enableHighAccuracy: false, timeout: 8000 },
    );
  } catch (e: any) {
    showFailToast('匹配失败');
    matching.value = false;
  }
}

async function doMatch(lat: number, lng: number) {
  try {
    const gender = (await client.get('/auth/me')).data.gender;
    const res = await client.post('/match/start', {
      scope: scope.value,
      latitude: lat,
      longitude: lng,
      preferGender: preferGender.value || (gender === 'male' ? 'female' : 'male'),
    });
    if (res.data.matched) {
      Object.assign(status, { isMatched: true, isMatching: false, matchedUser: res.data.matchedUser });
    } else {
      status.isMatching = true;
      matchStartedAt = Date.now();
      startPolling();
    }
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '匹配失败');
  } finally { matching.value = false; }
}

async function cancelMatch() {
  cancelling.value = true;
  try {
    await client.post('/match/cancel');
    status.isMatching = false;
    stopPolling();
    showSuccessToast('已取消');
  } catch {} finally { cancelling.value = false; }
}

async function closeMatch() {
  await cancelMatch();
  status.isMatched = false;
  status.matchedUser = null;
}
</script>

<style scoped>
.match-page { background: #f7f8fa; min-height: 100vh; padding-bottom: 60px; }
.match-content { padding: 20px; text-align: center; padding-top: 60px; }
.match-btn-area { margin-top: 30px; padding: 0 16px; }
.hint { color: #999; font-size: 13px; margin-top: 10px; }
.match-waiting { padding-top: 60px; }
.match-waiting h3 { margin-top: 20px; }
.match-waiting p { color: #999; margin: 10px 0 20px; }
.match-info { color: #1989fa !important; font-size: 13px; }
.match-done { padding-top: 40px; }
.match-done h3 { color: #1989fa; margin: 12px 0 4px; }
</style>
