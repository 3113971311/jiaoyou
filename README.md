# 拾光（jiaoyou）

一个带用户端和管理后台的社交交友项目，后端使用 FastAPI，前端使用 Vue 3 + Vite。

当前代码已经覆盖这些核心场景：

- 邮箱验证码注册、登录、刷新令牌
- 动态发布、点赞、收藏、评论
- 基于 VIP 的同城 / 同省匹配
- 私聊、图片消息、语音消息、视频消息、音视频通话记录
- 实名认证、举报、警告、黑名单、通知
- VIP 套餐、卡密生成与兑换
- 支付宝二维码付款 + 手动提交订单号 + 账单自动核验发卡
- 管理后台聊天监控、账单监控、套餐配置、系统配置

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 后端 | FastAPI, SQLAlchemy, Pydantic |
| 用户端 | Vue 3, Vue Router, Pinia, Element Plus, Axios |
| 管理后台 | Vue 3, Vue Router, Pinia, Element Plus, Axios |
| 数据库 | SQLite（默认） / 其他 `DATABASE_URL` 支持的数据库 |
| 认证 | JWT Access Token + Refresh Token |
| 文件上传 | FastAPI StaticFiles + 本地存储 |
| 邮件 | SMTP |
| 地理定位 | 高德地图 Web 服务 API + IP 定位兜底 |
| 支付核验 | 对接外部支付宝账单监测服务 |

## 当前功能

### 用户端

- 邮箱验证码注册、登录、找回密码、修改密码
- 个人资料、头像、性别、生日、简介、定位
- 动态流、详情页、评论、点赞、收藏
- 关注 / 粉丝列表
- VIP 购买页
  - 套餐价格来自数据库
  - 支持每个账号、每个套餐的首次充值折扣
  - 套餐支持标准收款码和首充折扣收款码
  - 用户付款后手动提交支付宝订单号
  - 后端轮询账单并自动发卡到邮箱
- 卡密兑换 VIP
- 匹配功能
  - 仅 VIP 可用
  - 支持同城 / 同省
  - 高德反查位置
- 聊天功能
  - 文本 / 图片 / 语音 / 视频消息
  - 删除单条消息
  - 删除整段会话并断联
  - 音频通话 / 视频通话记录
- 通知、反馈、实名认证

### 管理后台

- 数据概览 Dashboard
- 用户管理
  - 编辑资料
  - 调整 VIP 剩余天数
  - 封禁 / 删除 / 警告
- 动态审核与内容管理
- 举报处理
- 聊天监控
  - 查看所有会话
  - 查看消息内容
  - 播放语音 / 视频消息
  - 查看通话记录与录音 / 录像
- 卡密批次管理
- VIP 套餐管理
  - 配置价格、排序、启停
  - 上传收款码
  - 配置首充折扣与首充专用收款码
- 支付宝账单管理
  - 收入 / 支出 / 全部筛选
  - 批量修改发卡状态
  - 作废可疑账单
  - 查看原始账单 JSON
  - 查看支付宝登录状态
  - 自动登录 / 掉线提醒 / 手动重登
- 系统配置
  - 站点名称 / 副标题 / 公告 / Banner
  - SMTP
  - 高德地图 Key
  - 支付宝账单监测登录账号 / 密码

### 支付与发卡链路

当前项目已移除站内“支付宝 / 微信支付参数配置”模式，改为下面这条链路：

1. 后台配置 VIP 套餐、价格和收款二维码
2. 用户创建订单，页面展示对应套餐二维码
3. 用户付款后手动提交支付宝订单号
4. 后端按“订单号 + 实际应付金额”核验账单
5. 轮询频率为每 3 秒一次，最长 1 分钟
6. 匹配成功后自动生成卡密并发送到用户邮箱
7. 抓取到的账单直接入库，并在管理后台可查

额外规则：

- 同一账号每分钟最多创建 1 笔充值订单
- 同一账号每小时最多成功 1 笔充值
- 首充折扣按“每个账号、每个套餐、仅首次成功支付”计算

## 目录结构

```text
jiaoyou/
├─ backend/                    FastAPI 后端
│  ├─ routers/                 业务路由
│  ├─ utils/                   邮件、卡密、上传、支付宝监测桥接
│  ├─ main.py                  应用入口
│  ├─ models.py                数据模型与轻量迁移
│  ├─ schemas.py               请求 / 响应模型
│  ├─ config.py                环境变量与运行配置
│  ├─ database.py              数据库连接
│  ├─ auth.py                  JWT 工具与鉴权依赖
│  └─ requirements.txt         Python 依赖
├─ user-app/                   用户端 Vue 应用
│  ├─ src/router/              用户端路由
│  ├─ src/views/               用户页面
│  └─ package.json
├─ admin-app/                  管理后台 Vue 应用
│  ├─ src/router/              后台路由
│  ├─ src/views/               后台页面
│  └─ package.json
├─ data/storage/               上传文件目录（运行时生成）
├─ .env.example                环境变量模板
├─ Caddyfile                   旧的反向代理示例，生产前需按当前端口重新检查
└─ README.md
```

## 默认端口与运行组件

本地开发默认使用下面这些端口：

- 后端 API：`127.0.0.1:3002`
- 用户端：`127.0.0.1:5173`
- 管理后台：`127.0.0.1:5174`
- 支付宝账单监测服务：`127.0.0.1:3031`

数据与文件位置：

- 默认 SQLite：`backend/social.db`
- 上传目录：`data/storage/public/`

## 环境要求

- Python `3.10+`
- Node.js `20+`
- npm

## 环境变量

复制模板：

```powershell
Copy-Item .env.example .env
```

主要环境变量如下：

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | 数据库连接串；为空时默认使用 `backend/social.db` |
| `JWT_SECRET` | JWT 主密钥 |
| `JWT_PREVIOUS_SECRETS` | 历史 JWT 密钥，逗号分隔，用于平滑切换 |
| `JWT_EXPIRE_MINUTES` | Access Token 有效期，当前默认 7 天 |
| `CARD_PEPPER` | 卡密哈希 Pepper |
| `CARD_PREVIOUS_PEPPERS` | 历史卡密 Pepper，逗号分隔 |
| `ENABLE_DEV_PAYMENT` | 是否开启开发态直充接口 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | 邮件发送配置 |
| `ALLOWED_CORS_ORIGINS` | 允许的前端来源 |
| `ALIPAY_MONITOR_DIR` | 外部支付宝账单监测项目目录，默认是 `D:\支付宝账单监测` |
| `ALIPAY_MONITOR_PORT` | 外部账单监测服务端口，默认 `3031` |

说明：

- 邮箱验证码、密码找回、购卡发卡邮件都依赖 SMTP。
- 高德地图 Key 不走 `.env`，而是在管理后台系统配置中保存。
- 支付宝账单监测账号密码也在管理后台系统配置中保存。

## 本地启动

### 1. 安装后端依赖

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果你不使用 Windows PowerShell，可以用你自己的虚拟环境方式，只要最终能安装 `backend/requirements.txt` 即可。

### 2. 安装前端依赖

```bash
cd user-app
npm install

cd ../admin-app
npm install
```

### 3. 启动服务

后端：

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 3002 --reload
```

用户端：

```bash
cd user-app
npm run dev
```

管理后台：

```bash
cd admin-app
npm run dev
```

启动后访问：

- 用户端：[http://127.0.0.1:5173](http://127.0.0.1:5173)
- 管理后台：[http://127.0.0.1:5174](http://127.0.0.1:5174)
- API 文档：[http://127.0.0.1:3002/docs](http://127.0.0.1:3002/docs)
- 健康检查：[http://127.0.0.1:3002/api/health](http://127.0.0.1:3002/api/health)

注意：两个前端都使用 Hash 路由，直达页面时路径通常是 `/#/...`。

## 管理员初始化

项目当前不会自动创建管理员账号。

推荐流程：

1. 先从用户端注册一个普通账号
2. 再把这个账号提升为管理员

如果你使用默认 SQLite，可以在 `backend` 目录执行：

```bash
python -c "import sqlite3; conn=sqlite3.connect('social.db'); conn.execute(\"update users set is_admin = 1 where username = 'your_username'\"); conn.commit()"
```

把 `your_username` 替换成你刚注册的用户名，然后重新登录管理后台。

## 首次后台配置建议

管理员登录后台后，建议按这个顺序配置：

### 1. 系统配置

先在“系统配置”里补齐：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `高德地图 Key`
- `支付宝账单监测登录账号`
- `支付宝账单监测登录密码`
- 站点名称、公告等展示项

### 2. 套餐设置

在“套餐设置”里为每个套餐配置：

- 套餐名称 / 天数 / 价格
- 标准收款码
- 如果启用首充折扣：
  - 首充折扣力度
  - 首充专用收款码

注意：当前代码要求每个可售套餐必须配置收款码，否则用户端会禁止下单。

### 3. 支付宝账单页

在“支付宝账单”页：

- 先点击“自动登录支付宝”
- 如果支付宝要求验证码、短信验证或其他安全验证，需要手动补一步
- 登录成功后监测窗口会保持最小化在线
- 页面会定时检测登录状态，掉线时会提示重新登录

## 外部支付宝账单监测依赖

当前项目的账单核验依赖一个独立的本地项目，默认目录是：

```text
D:\支付宝账单监测
```

后端通过 `backend/utils/alipay_monitor.py` 与它交互，会按需自动拉起该服务。

默认要求外部项目具备这些能力：

- 提供 `src/service.js`
- 提供 `/status`、`/login`、`/sync`、`/match` 接口
- 复用 Playwright 登录态
- 支持账单拉取和订单匹配

如果你没有这套外部项目，支付宝账单同步、订单核验和自动发卡链路无法工作。

## 开发检查建议

前端构建检查：

```bash
cd user-app
npm run build

cd ../admin-app
npm run build
```

后端基础检查：

```bash
cd backend
python -m py_compile main.py
```

运行中可以优先检查：

- `GET /api/health`
- 后台是否能进入“系统配置”
- 高德 Key 是否能通过 `/api/geocode/reverse` 返回位置
- 支付宝账单页的登录状态是否为“已登录”

## 已知实现特点

- 注册验证码和发送频率限制目前保存在后端内存里，重启后会丢失。
- 默认数据库是 SQLite，更适合单机部署或开发环境；生产环境建议改成外部数据库。
- `models.py` 内包含轻量的自动补列逻辑，适合当前项目的快速迭代，但不等同于正式迁移系统。
- 仓库里的 `Caddyfile` 还是较早的示例，和当前本地运行端口不完全一致，生产前需要重新核对。
- 项目已经移除了后台直接维护支付宝 / 微信支付参数的旧做法，现在线上支付链路以“二维码 + 账单核验”模式为主。

## 许可与说明

这个仓库更像一套持续迭代中的业务项目，而不是完全通用的开箱即用脚手架。接手前，建议先核对：

- 管理员账号是否已存在
- SMTP 是否可用
- 高德 Key 是否可用
- 支付宝账单监测外部项目是否就绪
- 套餐收款码是否已配齐

把这几项对齐后，项目基本就能完整跑起来。
