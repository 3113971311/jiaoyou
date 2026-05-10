<template>
  <div class="admin-layout" v-if="$route.path !== '/login'">
    <el-container>
      <el-aside width="200px">
        <div class="logo">管理后台</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/"><el-icon><DataBoard /></el-icon> 仪表盘</el-menu-item>
          <el-menu-item index="/review"><el-icon><Picture /></el-icon> 图片审核</el-menu-item>
          <el-menu-item index="/cards"><el-icon><Ticket /></el-icon> 发卡管理</el-menu-item>
          <el-menu-item index="/users"><el-icon><User /></el-icon> 用户管理</el-menu-item>
          <el-menu-item index="/chats"><el-icon><ChatDotRound /></el-icon> 聊天监控</el-menu-item>
          <el-menu-item index="/reports"><el-icon><Warning /></el-icon> 举报处理</el-menu-item>
          <el-menu-item index="/sensitive"><el-icon><Filter /></el-icon> 敏感词</el-menu-item>
          <el-menu-item index="/config"><el-icon><Setting /></el-icon> 系统配置</el-menu-item>
        </el-menu>
      </el-aside>
      <el-main><router-view /></el-main>
    </el-container>
  </div>
  <router-view v-else />
</template>

<script setup lang="ts">
</script>

<style>
body { margin: 0; }
.admin-layout { min-height: 100vh; }
.logo { padding: 16px; text-align: center; font-size: 18px; font-weight: bold; color: #1989fa; }
.el-aside { background: #fff; border-right: 1px solid #eee; }
.el-main { background: #f0f2f5; min-height: 100vh; }
</style>
