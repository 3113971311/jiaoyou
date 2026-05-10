<template>
  <div v-if="$route.path.startsWith('/admin')"><router-view /></div>
  <div v-else-if="$route.path !== '/login'" class="app">
    <nav class="navbar">
      <router-link to="/" class="logo">交友聊天</router-link>
      <div class="nav-links">
        <router-link to="/moments">动态</router-link>
        <router-link to="/match">匹配</router-link>
        <router-link to="/chat">聊天</router-link>
        <router-link to="/vip">VIP</router-link>
        <router-link to="/profile">{{ store.user?.nickname || store.user?.username || '我的' }}</router-link>
      </div>
    </nav>
    <router-view class="fade-in-up" />
  </div>
  <router-view v-else />
</template>

<script setup>
import { useAuthStore } from './stores/auth'
const store = useAuthStore()
</script>
