# 智慧团建·一键学 飞书 Bot

这是一个面向团支部日常工作的飞书智能助手 Bot 原型，覆盖学习材料推送、资料检索、FAQ 问答、活动报名、任务查询和团务统计。

详细使用说明见：[docs/使用说明手册.md](docs/使用说明手册.md)

## 功能范围

- 接收飞书群聊或单聊中的 `@Bot` 消息
- 支持 `帮助`、`搜索`、`本周学习`、`活动报名`、`我的任务`、`周报` 等指令
- 从本地 SQLite 资料库检索学习资料和 FAQ
- 记录团员交互、活动报名和任务状态
- 定时向指定飞书群推送学习材料
- 预留飞书云文档资料同步接口

## 项目结构

```text
app/
  main.py                 # FastAPI 入口
  config.py               # 环境变量配置
  database.py             # SQLite 初始化与访问
  scheduler.py            # 定时任务
  feishu/
    client.py             # 飞书开放平台 API 客户端
    events.py             # 飞书事件解析
  modules/
    command_router.py     # 指令路由
    material_service.py   # 学习资料
    qa_service.py         # FAQ 问答
    activity_service.py   # 活动报名
    report_service.py     # 周报统计
    task_service.py       # 个人任务
scripts/
  init_db.py              # 初始化数据库
  seed_demo.py            # 写入演示资料
tests/
  test_command_router.py
```

## 快速启动

1. 创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. 复制配置文件：

```bash
copy .env.example .env
```

3. 修改 `.env` 中的飞书应用信息：

```text
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_VERIFICATION_TOKEN=xxx
FEISHU_DEFAULT_CHAT_ID=oc_xxx
```

4. 初始化数据库并写入演示数据：

```bash
python scripts/init_db.py
python scripts/seed_demo.py
```

5. 启动服务：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

6. 将公网 HTTPS 地址配置到飞书开放平台事件订阅：

```text
https://你的域名/feishu/events
```

本地开发可以用 ngrok、cpolar 或飞书可访问的测试网关转发到本机 `8000` 端口。

## 本机演示运行

项目提供了一键演示脚本，会启动本地 FastAPI 服务，并启动公网隧道。

```powershell
.\scripts\start_demo.ps1
```

脚本会输出飞书事件订阅地址，形如：

```text
https://xxxx.trycloudflare.com/feishu/events
```

将这个地址填入飞书开放平台的事件订阅请求地址。停止演示服务：

```powershell
.\scripts\stop_demo.ps1
```

如果你有 ngrok 固定域名，可以用固定隧道启动：

```powershell
.\scripts\start_demo.ps1 -Tunnel ngrok -NgrokDomain your-fixed-domain.ngrok-free.app
```

然后在飞书开放平台填写：

```text
https://your-fixed-domain.ngrok-free.app/feishu/events
```

注意：Cloudflare quick tunnel 每次启动可能生成不同域名；固定域名需要 ngrok/cpolar/Cloudflare 等服务的账号配置。

## 飞书开放平台配置

在飞书开放平台创建企业自建应用后，建议开启：

- 机器人能力
- 事件订阅：接收消息 `im.message.receive_v1`
- 权限：发送消息、读取用户基础信息、读取群信息
- 如需云文档同步，再添加云文档读取/搜索权限

Bot 进群后，可在群内使用：

```text
@Bot 帮助
@Bot 搜索 团课
@Bot 本周学习
@Bot 活动报名 春季团课
@Bot 我的任务
@Bot 完成任务 1
@Bot 完成任务 青年大学习
@Bot 周报
```

## 常用接口

- `GET /healthz`：健康检查
- `POST /feishu/events`：飞书事件回调
- `POST /admin/push/weekly?token=...`：手动触发学习材料推送
- `GET /admin/report?token=...`：查看团务周报
- `POST /admin/sync/bitable?token=...`：从飞书多维表格同步资料和任务
- `POST /admin/remind/tasks?token=...&days=3`：提醒未来 N 天内截止的未完成任务

## 飞书多维表格同步

可以用飞书多维表格作为资料和任务后台。先在 `.env` 中配置：

```text
FEISHU_BITABLE_APP_TOKEN=多维表格 app_token
FEISHU_BITABLE_WIKI_TOKEN=wiki 链接中的 token，可用于自动解析 app_token
FEISHU_BITABLE_MATERIALS_TABLE_ID=资料表 table_id
FEISHU_BITABLE_TASKS_TABLE_ID=任务表 table_id
```

如果多维表格链接形如 `https://xxx.feishu.cn/wiki/MGMN...?table=tbl...`，
可以填写 `FEISHU_BITABLE_WIKI_TOKEN=MGMN...`，但应用需要开通知识库节点读取权限。

资料表建议列名：

```text
标题
分类
关键词
摘要
链接
发布时间
是否本周推荐
```

任务表建议列名：

```text
用户ID
任务标题
状态
截止时间
```

其中 `用户ID` 填飞书用户的 `open_id`，Bot 会用它匹配“我的任务”。

手动同步：

```powershell
.\.venv\Scripts\python.exe scripts\sync_bitable.py
```

或在服务启动后调用：

```text
POST http://127.0.0.1:8000/admin/sync/bitable?token=change-me
```

也可以让管理员在飞书里发送：

```text
同步数据
```

管理员由 `.env` 中的 `ADMIN_USER_IDS` 控制，多个 open_id 用英文逗号分隔。
如果希望定时自动同步：

```text
BITABLE_AUTO_SYNC_ENABLED=true
BITABLE_AUTO_SYNC_INTERVAL_MINUTES=10
```

任务提醒可以手动触发：

```text
POST http://127.0.0.1:8000/admin/remind/tasks?token=change-me&days=3
```

如果要每天自动提醒，在 `.env` 中开启：

```text
TASK_REMINDER_ENABLED=true
TASK_REMINDER_CRON_HOUR=9
TASK_REMINDER_CRON_MINUTE=0
TASK_REMINDER_LOOKAHEAD_DAYS=3
```

## 后续扩展

- 接入飞书云文档，自动同步资料库
- 接入大模型和向量数据库，升级为知识库问答
- 使用飞书交互卡片完成报名、签到和反馈收集
- 将 SQLite 替换为 PostgreSQL
- 增加管理员后台页面
