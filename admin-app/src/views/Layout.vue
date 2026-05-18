<template>
  <div class="admin-layout">
    <aside class="admin-aside">
      <div class="aside-title">管理后台</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon><span>仪表盘</span></el-menu-item>
        <el-menu-item index="/review"><el-icon><PictureFilled /></el-icon><span>审核</span></el-menu-item>
        <el-menu-item index="/moments"><el-icon><Edit /></el-icon><span>动态管理</span></el-menu-item>
        <el-menu-item index="/vip-plans"><el-icon><Money /></el-icon><span>套餐设置</span></el-menu-item>
        <el-menu-item index="/alipay-bills"><el-icon><List /></el-icon><span>支付宝账单</span></el-menu-item>
        <el-menu-item index="/cards"><el-icon><Goods /></el-icon><span>发卡管理</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><UserFilled /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/chats"><el-icon><ChatDotSquare /></el-icon><span>聊天监控</span></el-menu-item>
        <el-menu-item index="/reports"><el-icon><WarningFilled /></el-icon><span>举报处理</span></el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon><span>系统配置</span></el-menu-item>
      </el-menu>
      <div class="aside-logout">
        <el-button link @click="logout" class="logout-btn">
          <el-icon><SwitchButton /></el-icon><span class="logout-text">退出登录</span>
        </el-button>
      </div>
    </aside>
    <main class="admin-main"><router-view /></main>
  </div>
</template>
<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
function logout() { auth.logout() }
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }
.admin-aside {
  width: 220px;
  flex-shrink: 0;
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--card-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 50;
  overflow-y: auto;
}
.aside-title {
  padding: 20px;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  flex-shrink: 0;
}
.aside-logout {
  margin-top: auto;
  padding: 12px 20px 16px;
  flex-shrink: 0;
}
.admin-main {
  flex: 1;
  margin-left: 220px;
  background: var(--bg);
  min-height: 100vh;
}

@media (max-width: 768px) {
  .admin-aside { width: 180px; }
  .admin-main { margin-left: 180px; }
}
@media (max-width: 480px) {
  .admin-aside { width: 56px; overflow: hidden; }
  .admin-aside .aside-title { font-size: 12px; padding: 14px 4px; }
  .admin-aside .el-menu-item span,
  .admin-aside .logout-text { display: none; }
  .admin-aside .aside-logout { display: flex; justify-content: center; padding: 8px 0 12px; }
  .admin-main { margin-left: 56px; }
}
.logout-btn { color: var(--text-secondary); font-size: 14px; display: flex; align-items: center; gap: 6px; }
</style>
