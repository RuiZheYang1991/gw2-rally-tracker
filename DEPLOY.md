# GCP 雲端部署與更新（Caddy + DuckDNS）

本文件對應目前實際在用的方案：**Google Cloud Ubuntu 22.04 虛擬機 + Docker Compose + Caddy HTTPS + DuckDNS**。

- 倉庫：https://github.com/RuiZheYang1991/gw2-rally-tracker
- 公網網址：`https://gw2rally.duckdns.org`
- 專案目錄（範例）：`/home/d80924gw2/gw2-rally-tracker`
- 打卡資料：主機上的 `./data/rally.db`（掛進容器，重啟不會丟）

`.env` 含 DuckDNS token，**不要提交 git、不要貼到聊天或截圖。**

---

## 一、第一次部署

### 1. GCP 防火牆

在 VPC 防火牆新增入站規則（目標這台 VM 或整個網路）：

| 通訊埠 | 用途 |
| --- | --- |
| TCP 22 | SSH |
| TCP 80、443 | 網站與 Let’s Encrypt 驗證（來源 `0.0.0.0/0`） |

在控制台記下 VM 的**外部 IPv4**。到 [DuckDNS](https://www.duckdns.org) 把 `gw2rally` 的 A 記錄改成這個 IP（不要再用家裡寬頻 IP）。

### 2. SSH 進去，安裝 Docker

```bash
sudo apt-get update
sudo apt-get install -y git docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
```

若沒有 `docker-compose-v2` 套件：

```bash
sudo apt-get install -y docker-compose
```

**登出再 SSH 進來一次**，之後才不用每次 `sudo docker`。

確認：

```bash
docker --version
docker compose version || docker-compose --version
```

若主機有開 `ufw`：

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 複製程式與設定環境變數

```bash
cd ~
git clone https://github.com/RuiZheYang1991/gw2-rally-tracker.git
cd gw2-rally-tracker
cp .env.example .env
nano .env
```

`.env` 內容（token 自己填，不要提交）：

```env
DOMAIN=gw2rally.duckdns.org
ACME_EMAIL=d80924gw2@gmail.com
DUCKDNS_SUBDOMAIN=gw2rally
DUCKDNS_TOKEN=
```

注意：

- 只能寫 `KEY=value`，**不要**寫 `export LANG=...`（那是給終端機用的）。
- `DOMAIN` 必須是完整網域 `gw2rally.duckdns.org`，不能只寫 `gw2rally`。

若要沿用舊機器的打卡資料：

```bash
mkdir -p data
# 把舊的 rally.db 拷到 ./data/rally.db
```

### 4. 啟動（含 Caddy）

```bash
cd ~/gw2-rally-tracker
chmod +x update.sh
export LANG=C.UTF-8 LC_ALL=C.UTF-8
./update.sh
```

有 `.env` 且填了 `DOMAIN` 時，`update.sh` 會一併啟動 Caddy；`DUCKDNS_TOKEN` 非空才會啟動 DuckDNS。

約 1～2 分鐘後檢查：

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml ps
docker compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml logs --tail=50 caddy
```

成功時應看到：

- `backend`：`Up` 且 `healthy`
- `caddy`：`0.0.0.0:80`、`0.0.0.0:443`
- 日誌：`certificate obtained successfully`（網域 `gw2rally.duckdns.org`）

團員請用 **https://gw2rally.duckdns.org**。主機上的 `:8080` 只是前端容器的備援埠，不是正式入口。

DNS 核對（兩個 IP 應相同）：

```bash
dig +short gw2rally.duckdns.org
curl -4 ifconfig.me
```

---

## 二、之後更新程式

在雲主機專案目錄：

```bash
cd ~/gw2-rally-tracker
export LANG=C.UTF-8 LC_ALL=C.UTF-8
./update.sh
```

腳本會：`git pull --ff-only` → 依 `.env` 帶上 Caddy／DuckDNS → `docker compose up -d --build`。

後端每次啟動會跑資料庫遷移，**不必**手寫 SQL。

| 情況 | 指令 |
| --- | --- |
| 一般程式／樣式更新 | `./update.sh` |
| 前端圖示、CSS 仍是舊的（映像快取） | `./update.sh --no-cache` |
| 瀏覽器還看到舊頁 | **Ctrl+F5** 強制重整 |

更新後可用：

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml ps
```

---

## 三、可忽略的警告

這些**不代表部署失敗**：

1. **`Running pip as the 'root' user`**  
   發生在 Docker **映像建置**裡，不是弄壞 Ubuntu 的 `apt`。不必在主機執行 `pip install --upgrade pip`。

2. **`the attribute version is obsolete`**  
   Compose V2 不再讀 compose 檔裡的 `version:`，不影響啟動。

3. **Caddy `stapling OCSP` / `no OCSP server`**  
   Let’s Encrypt 新憑證常見，HTTPS 仍可用。憑證由 Caddy 自動續期，不必 cron。

---

## 四、常見問題

| 現象 | 處理 |
| --- | --- |
| `KeyError: 'ContainerConfig'` / `ERROR: for backend  'ContainerConfig'` | 這是 **docker-compose 1.29.2 + 新版 Docker** 的已知 bug，前端其實已經編好。先裝 V2，再刪舊容器啟動（資料在 `./data/rally.db`，不會丟）：`sudo apt-get install -y docker-compose-v2` 然後 `docker rm -f $(docker ps -aq --filter name=gw2-rally-tracker_backend) $(docker ps -aq --filter name=gw2-rally-tracker_frontend)`，再 `docker compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml up -d` |
| Let’s Encrypt timeout / Connection refused | GCP 防火牆沒放行 80、443；或 DuckDNS 還指著舊 IP |
| `Couldn't connect to Docker daemon` | `sudo systemctl start docker`；使用者加入 `docker` 組後重新登入 |
| 開網域沒反應、`:8080` 卻可以 | 應用在跑，但 443 沒通；查防火牆與 `caddy` 日誌 |
| 家用寬頻 4G 進不去 | 住宅線路常擋入站 80/443，請用雲主機，不要在家裡硬開 port |
| `.env` 報 `environment variable name 'export LANG'` | `.env` 裡誤貼了 shell 的 `export`，刪掉即可 |

看 Caddy 日誌：

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.duckdns.yml logs --tail=80 caddy
```

---

## 五、本機開發（不經 Caddy）

不走雲端時，只起應用即可：

```bash
docker compose up -d --build
```

瀏覽器：http://localhost:8080
