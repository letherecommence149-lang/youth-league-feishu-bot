# 智慧团建一键学飞书 Bot

面向团支部日常工作的飞书智能助手，用于学习资料推送、资料检索、FAQ 问答、活动报名、个人任务查询、任务完成回写和团务统计。项目基于 FastAPI、SQLite、APScheduler 和飞书开放平台 API。

## 功能概览

- 在飞书群聊或单聊中响应 `@Bot` 消息。
- 支持成员指令：`帮助`、`我的ID`、`我的任务`、`完成任务`、`本周学习`、`搜索`、`活动报名`、`周报`。
- 支持管理员指令：`同步数据`。
- 从飞书多维表格同步学习资料和个人任务。
- 定时向指定飞书群推送本周学习资料。
- 支持任务到期提醒。
- 记录成员交互、活动报名和任务状态。

## 使用文档

项目内已提供两份说明：

- [管理员使用说明](docs/管理员使用说明.md)
- [普通成员使用说明](docs/普通成员使用说明.md)

对应 PDF：

- [管理员使用说明.pdf](docs/管理员使用说明.pdf)
- [普通成员使用说明.pdf](docs/普通成员使用说明.pdf)

PDF 由 Markdown 通过 Prince 渲染生成：

```powershell
python scripts/render_markdown_with_prince.py
```

## 项目结构

```text
app/
  main.py                 # FastAPI 入口和接口路由
  config.py               # 环境变量配置
  database.py             # SQLite 初始化与访问
  scheduler.py            # 定时任务
  feishu/
    client.py             # 飞书开放平台 API 客户端
    events.py             # 飞书事件解析与 token 校验
  modules/
    bitable_sync.py       # 飞书多维表格同步
    command_router.py     # 成员指令路由
    material_service.py   # 学习资料查询
    qa_service.py         # FAQ 问答
    activity_service.py   # 活动报名
    task_service.py       # 个人任务查询
    task_completion_service.py
    task_reminder_service.py
    push_service.py       # 周学习资料推送
    report_service.py     # 团务统计
scripts/
  init_db.py              # 初始化数据库
  seed_demo.py            # 写入演示资料
  sync_bitable.py         # 手动同步多维表格
  start_demo.ps1          # 本地演示启动脚本
  stop_demo.ps1           # 本地演示停止脚本
  render_markdown_with_prince.py
tests/
  test_*.py
docs/
  管理员使用说明.md / .pdf
  普通成员使用说明.md / .pdf
```

## 本地开发

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

复制配置文件：

```bash
cp .env.example .env
```

Windows cmd 可用：

```cmd
copy .env.example .env
```

初始化数据库：

```bash
python scripts/init_db.py
```

如需演示数据：

```bash
python scripts/seed_demo.py
```

启动服务：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```text
http://127.0.0.1:8000/healthz
```

## 服务器部署

推荐环境：

- Ubuntu 22.04
- Python 3.10+
- Git
- 2 核 2G 及以上云服务器

安装基础依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git sqlite3
```

拉取项目：

```bash
git clone https://github.com/letherecommence149-lang/youth-league-feishu-bot.git
cd youth-league-feishu-bot
```

安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

初始化并启动：

```bash
python scripts/init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## systemd 后台运行

创建服务文件：

```bash
sudo nano /etc/systemd/system/youth-bot.service
```

内容：

```ini
[Unit]
Description=Youth League Feishu Bot
After=network.target

[Service]
WorkingDirectory=/root/youth-league-feishu-bot
ExecStart=/root/youth-league-feishu-bot/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now youth-bot
sudo systemctl status youth-bot
```

常用维护命令：

```bash
sudo systemctl restart youth-bot
sudo systemctl status youth-bot
sudo journalctl -u youth-bot -f
```

## 环境变量配置

`.env` 中的核心配置：

```env
APP_NAME=智慧团建一键学Bot
APP_ENV=production
DATABASE_PATH=./data/bot.sqlite3
ADMIN_TOKEN=change-me
ADMIN_USER_IDS=

FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_VERIFICATION_TOKEN=
FEISHU_ENCRYPT_KEY=
FEISHU_DEFAULT_CHAT_ID=

FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_WIKI_TOKEN=
FEISHU_BITABLE_MATERIALS_TABLE_ID=
FEISHU_BITABLE_TASKS_TABLE_ID=

WEEKLY_PUSH_ENABLED=true
WEEKLY_PUSH_CRON_DAY_OF_WEEK=mon
WEEKLY_PUSH_CRON_HOUR=8
WEEKLY_PUSH_CRON_MINUTE=30

TASK_REMINDER_ENABLED=false
TASK_REMINDER_CRON_HOUR=9
TASK_REMINDER_CRON_MINUTE=0
TASK_REMINDER_LOOKAHEAD_DAYS=3

BITABLE_AUTO_SYNC_ENABLED=true
BITABLE_AUTO_SYNC_INTERVAL_MINUTES=10
```

说明：

- `ADMIN_TOKEN` 用于管理接口鉴权。
- `ADMIN_USER_IDS` 控制谁能在飞书中执行 `同步数据`。
- `FEISHU_DEFAULT_CHAT_ID` 是定时推送的目标群。
- `FEISHU_BITABLE_*` 用于同步飞书多维表格。
- 修改 `.env` 后需要重启服务。

## 飞书开放平台配置

在飞书开放平台创建企业自建应用后，建议开启：

- 机器人能力。
- 事件订阅：`im.message.receive_v1`。
- 权限：发送消息、接收消息、读取用户基础信息、读取群信息。
- 如需同步多维表格，开通多维表格读取/写入相关权限，并将多维表格授权给应用。

事件订阅请求地址：

```text
http://服务器公网IP:8000/feishu/events
```

如已配置域名和 HTTPS：

```text
https://你的域名/feishu/events
```

当前项目默认使用 `Verification Token` 校验。没有额外解密逻辑时，不建议开启事件加密。

## 飞书多维表格同步

学习资料表建议字段：

```text
标题
分类
关键词
摘要
链接
发布日期
是否本周推荐
```

个人任务表建议字段：

```text
用户ID
任务标题
状态
截止日期
```

`FEISHU_BITABLE_MATERIALS_TABLE_ID` 和 `FEISHU_BITABLE_TASKS_TABLE_ID` 只填写 `tbl...`，不要带 `&view=...`。

手动同步：

```bash
python scripts/sync_bitable.py
```

或调用接口：

```bash
curl -X POST "http://127.0.0.1:8000/admin/sync/bitable?token=你的ADMIN_TOKEN"
```

管理员也可以在飞书中发送：

```text
同步数据
```

## 定时推送和立即推送

定时推送由 `WEEKLY_PUSH_*` 控制，时区为 `Asia/Shanghai`。

立即推送：

```bash
curl -X POST "http://127.0.0.1:8000/admin/sync/bitable?token=你的ADMIN_TOKEN"
curl -X POST "http://127.0.0.1:8000/admin/push/weekly?token=你的ADMIN_TOKEN"
```

如果推送中出现 `example.com`，说明演示数据仍在本地数据库中，可删除：

```bash
sqlite3 data/bot.sqlite3 "DELETE FROM materials WHERE url LIKE '%example.com%';"
```

## 常用接口

- `GET /healthz`：健康检查。
- `POST /feishu/events`：飞书事件回调。
- `POST /admin/push/weekly?token=...`：手动触发本周学习资料推送。
- `GET /admin/report?token=...`：查看团务周报。
- `POST /admin/sync/bitable?token=...`：同步飞书多维表格。
- `POST /admin/remind/tasks?token=...&days=3`：提醒未来 N 天内截止的未完成任务。

## 成员指令

```text
@Bot 帮助
@Bot 我的ID
@Bot 我的任务
@Bot 完成任务 1
@Bot 完成任务 青年大学习
@Bot 本周学习
@Bot 搜索 团课
@Bot 活动报名 春季团课
@Bot 周报
```

## 测试

运行测试：

```bash
pytest
```

## 安全提醒

- `.env` 已被 `.gitignore` 忽略，不要提交真实密钥。
- `data/`、`logs/`、`.venv/` 不应提交到仓库。
- 如果曾经在聊天、截图或公开页面暴露过飞书 Token，建议在飞书开放平台重新生成。

