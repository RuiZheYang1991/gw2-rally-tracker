# GW2 Rally Tracker

公会每晚集结的 **出勤打卡、职责统计、周常预测** 工具。界面为《激战 2》式深色金边风格。

职业包含核心九职业与精英特化（特化作为独立选项，排在对应核心之后）。图标目前为 SVG 占位纹章，可按 `key` 自行替换。

仓库：[https://github.com/RuiZheYang1991/gw2-rally-tracker](https://github.com/RuiZheYang1991/gw2-rally-tracker)

## 功能

| 页面 | 说明 |
| --- | --- |
| 今晚打卡 | 填写昵称，选择职业（核心/特化）+ 职责（坦 / DPS / 辅助）。同一人同一天可登记多条不同组合 |
| 出勤统计 | 近 7 / 30 天折线；按日查看职责饼图、柱状图；点击职责下钻到职业构成 |
| 周常设置 | 勾选通常能出团的星期，每天指定一套主要职业 + 职责 |
| 周常总表 | 团长看板：周一至周日预计人数柱状图；按坦/DPS/辅助分块，缺人用红色虚线标「空缺」 |

## 技术栈

- 后端：Python FastAPI + SQLite + SQLAlchemy
- 前端：Vue 3 + Vite + Chart.js
- 部署：Docker Compose；Nginx 托管前端并反向代理 `/api`

## 一键部署

需要已安装并启动 Docker 引擎。

```bash
git clone https://github.com/RuiZheYang1991/gw2-rally-tracker.git
cd gw2-rally-tracker
docker-compose build
docker-compose up -d
```

旧版 `docker-compose` 1.x 请使用本仓库的 `version: "2.4"` 文件。Compose V2 可用：

```bash
docker compose up -d
```

浏览器打开 [http://localhost:8080](http://localhost:8080)。

SQLite 挂载在宿主机 `./data/rally.db`，容器重启不会丢数据。

常见问题：

- `Couldn't connect to Docker daemon`：先 `sudo systemctl start docker`，或把当前用户加入 `docker` 组后重新登录。
- `Unsupported config option for services: 'frontend'`：compose 过旧且缺少 `version` 字段，请拉取最新 `docker-compose.yml`。

## 本地开发

后端（建议 Python 3.10+）：

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
# Windows
set DATABASE_PATH=..\data\rally.db
# Linux
export DATABASE_PATH=../data/rally.db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

- 页面：[http://127.0.0.1:5173](http://127.0.0.1:5173)
- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Vite 将 `/api` 代理到 `8000`

`8000` 只有 JSON API，没有网页。

## 数据模型

启动时 `migrate_schema()` 会自动给旧库加字段、迁移职责（原 `heal` 并入辅助）、重建打卡唯一约束。

| 表 | 作用 |
| --- | --- |
| `professions` | 核心 + 特化。`armor` / `family_key` / `spec_kind`（core / elite / upcoming） |
| `roles` | 坦 / DPS / 辅助（`tank` / `dps` / `support`） |
| `checkins` | 每日打卡。`duty`：`Tank` / `DPS` / `Support`。唯一约束为昵称 + 日期 + 职业 + 职责 |
| `weekly_slots` | 周常空闲：昵称 + 星期（0=周一 … 6=周日）+ 职业 + 职责 |

人数由打卡记录聚合，不单独存「人数」字段。

## API

- `GET /api/health`
- `GET /api/professions`　`GET /api/roles`
- `POST /api/checkins` 新增一条职业+职责（相同组合幂等）
- `GET /api/checkins?rally_date=YYYY-MM-DD`
- `DELETE /api/checkins/{id}`
- `GET /api/stats/overview?days=7\|30`
- `GET /api/stats/day?rally_date=` 含 `by_role_detail` 供职责下钻
- `GET /api/weekly?nickname=`　`PUT /api/weekly`
- `GET /api/weekly/forecast`

## 替换职业图标

编辑 `frontend/src/icons.js`，按职业 `key` 换成官方图或 SVG，无需改后端。

## 目录结构

```
backend/          FastAPI
frontend/          Vue 3
data/              SQLite 挂载目录
docker-compose.yml
```
