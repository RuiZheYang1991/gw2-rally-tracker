#!/usr/bin/env bash
# 虚拟机 / 服务器：拉最新代码并重建镜像后启动。
# 用法：
#   ./update.sh           # git pull + compose up --build
#   ./update.sh --no-cache  # 强制不走构建缓存（前端样式仍不对时用）
set -euo pipefail

cd "$(dirname "$0")"

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
  NO_CACHE="--no-cache"
fi

if [[ -d .git ]]; then
  echo "==> git pull"
  git pull --ff-only
else
  echo "不是 git 仓库，跳过 pull"
fi

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
else
  echo "找不到 docker-compose / docker compose" >&2
  exit 1
fi

echo "==> 重建并启动容器"
set +e
if [[ -n "$NO_CACHE" ]]; then
  "${COMPOSE[@]}" build $NO_CACHE
  "${COMPOSE[@]}" up -d
else
  "${COMPOSE[@]}" up -d --build
fi
UP_STATUS=$?
set -e
if [[ $UP_STATUS -ne 0 ]]; then
  echo "==> 启动失败，后端日志：" >&2
  "${COMPOSE[@]}" logs --tail=80 backend || true
  echo "前端依赖后端健康检查。可先执行: ${COMPOSE[*]} logs backend" >&2
  exit "$UP_STATUS"
fi

echo "==> 当前容器"
"${COMPOSE[@]}" ps
echo "完成。浏览器请强制刷新（Ctrl+F5）。页面：http://localhost:8080"
