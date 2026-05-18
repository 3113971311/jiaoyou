# 拾光 (Shiguang) — 社交平台

在线社交平台，支持匹配交友、即时聊天、动态分享、VIP 会员、实名认证、发卡充值等功能。

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Python FastAPI + SQLAlchemy |
| 用户端 | Vue 3 + Vite + Element Plus |
| 管理端 | Vue 3 + Vite + Element Plus |
| 数据库 | SQLite |
| 认证 | JWT |
| 支付 | 支付宝 PC 网页支付 |
| 定位 | 高德地图 IP 定位 + GPS |
| 邮件 | SMTP |

## 项目结构

```
├── backend/              # Python FastAPI 后端
│   ├── routers/          # API 路由
│   │   ├── auth.py       # 登录/注册/Token
│   │   ├── users.py      # 用户管理
│   │   ├── moments.py    # 动态/点赞/收藏/评论
│   │   ├── match.py      # 匹配/定位
│   │   ├── chat.py       # 聊天
│   │   ├── payment.py    # 支付宝支付
│   │   ├── cards.py      # 卡密管理
│   │   ├── moderation.py # 图片审核
│   │   ├── verify.py     # 实名认证审核
│   │   ├── reports.py    # 举报处理
│   │   ├── dashboard.py  # 数据面板
│   │   ├── site_config.py# 系统配置
│   │   ├── follow.py     # 关注/粉丝
│   │   ├── notifications.py
│   │   └── feedback.py   # 问题反馈
│   ├── utils/            # 工具
│   │   ├── mailer.py     # 邮件发送
│   │   └── card_code.py  # 卡密生成
│   ├── models.py         # 数据库模型
│   ├── schemas.py        # 请求/响应模型
│   ├── auth.py           # JWT 认证
│   ├── config.py         # 配置
│   └── database.py       # 数据库连接
├── user-app/             # Vue 3 用户端
│   └── src/views/        # 页面组件
├── admin-app/            # Vue 3 管理端
│   └── src/views/        # 管理页面
├── data/storage/         # 上传文件
└── .env.example          # 环境变量模板
```

## 功能概要

### 用户端
- 动态发布/浏览/点赞/收藏/评论
- 匹配交友（同城/同省，GPS + 高德定位）
- 即时聊天（文字 + 图片）
- VIP 会员（支付宝购买卡密）
- 实名认证（手持身份证拍照，管理员审核）
- 关注/粉丝
- 通知系统
- 问题反馈

### 管理后台
- 仪表盘（数据概览）
- 审核（图片审核 + 实名审核）
- 动态管理（编辑/删除/审核动态）
- 用户管理（详情/封禁/删除/实名信息）
- 发卡管理（生成/导出/删除卡密批次）
- 聊天监控
- 举报处理
- 系统配置（站点设置/前端展示/邮件/高德Key）

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

管理后台 → 系统配置中配置高德地图 Key。

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
# 后端（http://localhost:3002）
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 3002 --reload

# 用户端（http://localhost:5173）
cd user-app
npx vite --port 5173

# 管理端（http://localhost:5174）
cd admin-app
npx vite --port 5174
```

启动后访问：
- 用户端：http://localhost:5173
- 管理端：http://localhost:5174
- API 文档：http://localhost:3002/docs

## 默认账号

管理后台默认管理员：`admin` / `admin123456`
