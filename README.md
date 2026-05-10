# 佳友 (JiaYou) - 社交交友平台

在线交友平台，支持匹配、聊天、动态分享、VIP 会员等功能。

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Fastify + Prisma + Socket.IO + TypeScript |
| 用户端 | Vue 3 + Vite + Element Plus |
| 管理端 | Vue 3 + Vite + Element Plus |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 缓存 | Redis |
| 存储 | 本地文件系统 / MinIO（生产） |

## 快速开始

```bash
# 安装依赖
pnpm install

# 初始化数据库
pnpm db:migrate
pnpm db:generate

# 启动后端（默认 http://localhost:3000）
pnpm dev

# 启动用户端（默认 http://localhost:5173）
pnpm dev:user

# 启动管理端（默认 http://localhost:5174）
pnpm dev:admin
```

## Docker 部署

```bash
docker-compose up -d
```

包含服务：PostgreSQL、Redis、MinIO、Caddy 反向代理。

## 功能

- 用户注册/登录
- 个人资料与头像
- 匹配系统
- 即时聊天（Socket.IO）
- 动态广场
- VIP 会员与卡密充值
- 举报与审核
- 敏感词过滤
- 管理后台

## 环境变量

参考 `.env.example` 文件，主要配置项：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 数据库连接地址 |
| `JWT_SECRET` | JWT 密钥 |
| `SMTP_HOST` | 邮件服务器 |
| `SMTP_USER` | 邮箱账号 |
| `SMTP_PASS` | 邮箱授权码 |
