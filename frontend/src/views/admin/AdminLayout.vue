<template>
  <el-container style="min-height:100vh">
    <el-aside width="220px" style="background:var(--card-bg);backdrop-filter:blur(20px);border-right:1px solid rgba(0,0,0,0.05)">
      <div style="padding:20px;text-align:center;font-size:18px;font-weight:700;color:var(--accent)">管理后台</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/admin"><el-icon><DataBoard /></el-icon>仪表盘</el-menu-item>
        <el-menu-item index="/admin/review"><el-icon><Picture /></el-icon>图片审核</el-menu-item>
        <el-menu-item index="/admin/cards"><el-icon><Ticket /></el-icon>发卡管理</el-menu-item>
        <el-menu-item index="/admin/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/admin/chats"><el-icon><ChatDotRound /></el-icon>聊天监控</el-menu-item>
        <el-menu-item index="/admin/reports"><el-icon><Warning /></el-icon>举报处理</el-menu-item>
        <el-menu-item index="/admin/settings"><el-icon><Setting /></el-icon>系统配置</el-menu-item>
      </el-menu>
      <div style="position:absolute;bottom:20px;left:20px">
        <el-button @click="logout" link>退出登录</el-button>
      </div>
    </el-aside>
    <el-main style="background:var(--bg)"><router-view /></el-main>
  </el-container>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
const auth = useAuthStore()
function logout() { auth.logout() }
</script>
