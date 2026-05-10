<template>
  <el-container style="min-height:100vh">
    <el-aside width="220px" style="background:var(--card-bg);backdrop-filter:blur(20px);border-right:1px solid rgba(0,0,0,0.05)">
      <div style="padding:20px;text-align:center;font-size:18px;font-weight:700;color:var(--accent)">管理后台</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon>仪表盘</el-menu-item>
        <el-menu-item index="/review"><el-icon><PictureFilled /></el-icon>图片审核</el-menu-item>
        <el-menu-item index="/cards"><el-icon><Goods /></el-icon>发卡管理</el-menu-item>
        <el-menu-item index="/users"><el-icon><UserFilled /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/chats"><el-icon><ChatDotSquare /></el-icon>聊天监控</el-menu-item>
        <el-menu-item index="/reports"><el-icon><WarningFilled /></el-icon>举报处理</el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon>系统配置</el-menu-item>
      </el-menu>
      <div style="position:absolute;bottom:20px;left:60px"><el-button link @click="logout">退出登录</el-button></div>
    </el-aside>
    <el-main style="background:var(--bg)"><router-view /></el-main>
  </el-container>
</template>
<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
function logout() { auth.logout() }
</script>
