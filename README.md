# 拾光 (Shiguang) — 社交平台

在线社交平台，支持匹配交友、即时聊天、动态分享、VIP 会员、发卡充值等功能。

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Python FastAPI + SQLAlchemy |
| 用户端 | Vue 3 + Vite + Element Plus |
| 管理端 | Vue 3 + Vite + Element Plus |
| 数据库 | SQLite |
| 认证 | JWT |
| 邮件 | SMTP（QQ 邮箱） |

## 项目结构

```
├── backend/          # Python FastAPI 后端
│   ├── routers/      # API 路由
│   ├── utils/        # 工具函数
│   ├── models.py     # 数据模型
│   ├── schemas.py    # 请求/响应模型
│   └── config.py     # 配置
├── user-app/         # Vue 3 用户端
│   └── src/views/    # 页面组件
├── admin-app/        # Vue 3 管理端
│   └── src/views/    # 管理页面
├── data/storage/     # 上传文件
└── .env.example      # 环境变量模板
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 20+
- npm

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填写 SMTP 邮箱等信息（可选）
```

### 3. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 用户端
cd ../user-app
npm install

# 管理端
cd ../admin-app
npm install
```

### 4. 启动

```bash
# 后端（http://localhost:3001）
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 3001 --reload

# 用户端（http://localhost:5173）
cd user-app
npx vite --port 5173

# 管理端（http://localhost:5174）
cd admin-app
npx vite --port 5174
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:3001 |
| 用户端 | http://localhost:5173 |
| 管理端 | http://localhost:5174 |

### 5. 默认管理员账号

- 用户名：`admin`
- 密码：`admin123456`

## 功能

### 用户端

- 注册/登录（邮箱验证码）
- 个人资料编辑与头像上传
- 匹配交友（同城/同省）
- 即时聊天（支持文字和图片）
- 动态广场（点赞、评论、图片上传）
- 关注/粉丝
- VIP 会员（发卡平台购买、卡密兑换）
- 通知系统（悬浮横幅提醒）
- 举报与反馈
- 用户拉黑

### 管理后台

- 仪表盘（统计下钻）
- 用户管理（状态切换、编辑、创建）
- 发卡管理（卡密生成、查看、导出）
- 图片审核
- 聊天监控
- 举报处理
- 系统配置（前端展示、邮件、支付）

### 系统配置

管理后台「系统配置」支持：

- **基础设置**：网站名称、副标题
- **前端展示**：首页轮播图、系统公告、文字公告
- **邮件服务**：SMTP 配置
- **支付配置**：支付宝/微信支付参数

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | SQLite 连接地址 | `sqlite:///./social.db` |
| `JWT_SECRET` | JWT 签名密钥 | `dev-jwt-secret-key-2024` |
| `CARD_PEPPER` | 卡密哈希盐值 | `dev-card-pepper` |
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 发件邮箱 | - |
| `SMTP_PASS` | 邮箱授权码 | - |

## License

MIT
