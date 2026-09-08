# GW2 Rally Tracker

公会每晚集结的出勤打卡与职业/职责统计工具。界面采用《激战2》式深色金边风格；职业图标目前为 SVG 占位纹章，可按 `profession key` 替换为官方资源。

## 一键部署

```bash
docker-compose build
docker-compose up -d
```

若机器上是较旧的 `docker-compose`（1.x），文件需带 `version` 字段；本仓库已使用 `version: "2.4"`。新版可用 `docker compose up -d`（中间有空格）。

浏览器打开 [http://localhost:8080](http://localhost:8080)。

SQLite 文件挂载在宿主机 `./data/rally.db`，容器重启不会丢数据。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_PATH=..\data\rally.db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

Vite 会把 `/api` 代理到 `8000` 端口。

## 数据模型

| 表 | 作用 |
| --- | --- |
| `professions` | 核心九职业 + 精英特化（含即将推出）。`armor` / `family_key` / `spec_kind` |
| `roles` | 职责：坦 / DPS / 辅助（key = tank/dps/support） |
| `checkins` | 每日打卡。`duty` 为 VARCHAR：`Tank` / `DPS` / `Support`。同一昵称同一天可有多条职业+职责组合 |
| `weekly_slots` | 周常空闲：昵称 + 星期(0=周一) + 职业 + 职责 |

启动时 `migrate_schema()` 会给旧库加 `duty` 字段、把原 `heal` 并入辅助，并重建打卡唯一约束。

## 主要 API

- `GET /api/professions` `GET /api/roles`
- `POST /api/checkins` 新增一条职业+职责打卡（相同组合幂等）
- `GET /api/checkins?rally_date=YYYY-MM-DD`
- `DELETE /api/checkins/{id}`
- `GET /api/stats/overview?days=7|30`（含 `by_role` / `by_day_role`）
- `GET /api/stats/day?rally_date=` 含 `by_role_detail` 供职责下钻
- `GET /api/weekly?nickname=` 成员周常
- `PUT /api/weekly` 覆盖保存周常空闲
- `GET /api/weekly/forecast` 团长周常总表

## 替换职业图标

前端 `src/icons.js` 按职业 `key` 提供占位 SVG。把对应条目换成图片 URL 或 SVG 文件即可，不必改后端。
