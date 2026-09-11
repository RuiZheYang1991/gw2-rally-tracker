# GW2 Rally Tracker

公会每晚集结的 **出勤打卡、职责统计、周常预测** 工具。界面为《激战 2》式深色金边风格。

职业包含核心九职业与精英特化（特化作为独立选项，排在对应核心之后）。图标目前为 SVG 占位纹章，可按 `key` 自行替换。

仓库：[https://github.com/RuiZheYang1991/gw2-rally-tracker](https://github.com/RuiZheYang1991/gw2-rally-tracker)

- 团员 / 会长怎么用网页：[USER.md](USER.md)
- 云主机怎么部署：[DEPLOY.md](DEPLOY.md)

## 在线试用

公开站点：[https://gw2rally.duckdns.org](https://gw2rally.duckdns.org/)

想先看界面和统计，不必自己建公会。登录页填写：

| | |
| --- | --- |
| 公会名称 | `demo` |
| 密码 | `demo` |

里面已有若干天的示例打卡和周常，可翻「今晚打卡 / 出勤统计 / 周常总表」。这是给大家参观的公共账本，请勿写入真实团务；自己出团请另建公会（名称尚未存在时，第一次进入即注册）。

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

浏览器打开 [http://localhost:8080](http://localhost:8080)。第一次打开会进入登录页：填写**公会名称 + 密码**。该名称尚未存在时，这次进入就会创建公会并设置密码；之后团员用同一组信息即可打卡。各公会的打卡数据互相隔离。

SQLite 挂载在宿主机 `./data/rally.db`，容器重启不会丢数据。

### 虚拟机上更新代码和数据库

`git pull` **不会**自动重建 Docker 镜像。后端容器**每次启动**都会跑 `migrate_schema()`，给旧的 `rally.db` 加表、加字段（本版本会加上 `guilds` / `guild_sessions`，以及打卡表上的 `guild_id`）。**不需要**手工执行 SQL。

在虚拟机项目目录：

```bash
chmod +x update.sh   # 只需第一次
./update.sh
```

或 `make update`。等价于 `git pull` + `docker-compose up -d --build`。

启动成功后，旧库里已有的打卡会归到公会 **「原有数据」**。用这个名称进入时，第一次填写的密码即成为该公会密码。

若前端仍是旧页面，再跑 `./update.sh --no-cache`，浏览器 **Ctrl+F5**。

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

启动时 `migrate_schema()` 会自动给旧库加字段、迁移职责（原 `heal` 并入辅助）、重建打卡唯一约束，并在 schema 4 增加公会登录表。

| 表 | 作用 |
| --- | --- |
| `guilds` | 公会。`name_norm` 唯一；`password_hash` 为空表示尚未设密（首次进入时写入） |
| `guild_sessions` | 登录令牌 |
| `professions` | 核心 + 特化。`armor` / `family_key` / `spec_kind`（core / elite / upcoming） |
| `roles` | 坦 / DPS / 辅助（`tank` / `dps` / `support`） |
| `checkins` | 每日打卡（按 `guild_id` 隔离）。唯一约束为公会 + 昵称 + 日期 + 职业 + 职责 |
| `weekly_slots` | 周常空闲（按 `guild_id` 隔离） |

人数由打卡记录聚合，不单独存「人数」字段。

## API

- `GET /api/health`
- `POST /api/auth/login`　`GET /api/auth/me`　`POST /api/auth/password`　`POST /api/auth/logout`
- `GET /api/professions`　`GET /api/roles`
- `POST /api/checkins` 新增一条职业+职责（相同组合幂等；需登录）
- `GET /api/checkins?rally_date=YYYY-MM-DD`
- `DELETE /api/checkins/{id}`
- `GET /api/stats/overview?days=7\|30`
- `GET /api/stats/day?rally_date=` 含 `by_role_detail` 供职责下钻
- `GET /api/weekly?nickname=`　`PUT /api/weekly`
- `GET /api/weekly/forecast`

## 职业图标

彩色高清图标来自 [GW2 Wiki: Profession icons](https://wiki.guildwars2.com/wiki/Guild_Wars_2_Wiki:Profession_icons)，保存在 `frontend/public/img/professions/{key}.png`（优先 highres）。版权归属 ArenaNet / Wiki 授权条款，仅供本工具展示。

重新下载：

```bash
python scripts/download_profession_icons.py
```

若 PNG 缺失，界面会回退到 `frontend/src/icons.js` 的占位 SVG。

## 目录结构

```
backend/          FastAPI
frontend/          Vue 3
data/              SQLite 挂载目录
docker-compose.yml
docker-compose.https.yml   Caddy + Let's Encrypt
docker-compose.duckdns.yml DuckDNS 动态解析
```

## 公网 HTTPS（云主机 + Caddy）

适合租用的云虚拟机：安全组放行 **80、443**，DuckDNS 指到该机公网 IP。Caddy 向 Let's Encrypt 申请证书并自动续期。

**完整步骤（GCP Ubuntu 22.04 首次部署 + 之后更新）见 [DEPLOY.md](DEPLOY.md)。**

1. 打开 [https://www.duckdns.org](https://www.duckdns.org)，子域名为 `gw2rally`（即 `gw2rally.duckdns.org`）。token 只写进服务器 `.env`，不要提交 git。
2. 云厂商安全组 / 防火墙放行 TCP **80、443**（来源 0.0.0.0/0）。
3. 在项目目录：

```bash
cp .env.example .env
# 编辑 .env：填入 DUCKDNS_TOKEN
docker-compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml up -d --build
```

浏览器访问 `https://gw2rally.duckdns.org`。之后更新用 `./update.sh`（若已有 `.env` 且填写了 `DOMAIN`，脚本会一并带上 Caddy 与 DuckDNS）。

家用宽带若入站 80/443 被运营商拦截，请改用云主机，不要在家里硬开端口。
