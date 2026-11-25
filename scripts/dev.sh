#!/usr/bin/env bash
# 一键启动：后端 FastAPI（uv + uvicorn --reload）与前端 Vite。
#
#   bash scripts/dev.sh                 # 前端 5173，后端 8000
#   SM_FE_PORT=5183 SM_BE_PORT=8010 bash scripts/dev.sh
#
# Ctrl-C 会同时停掉前后端。前端会自动把 /api 代理到本次启动的后端端口。
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BE_PORT="${SM_BE_PORT:-8000}"
FE_PORT="${SM_FE_PORT:-5173}"

info() { printf '\033[2m[dev]\033[0m %s\n' "$*"; }
fail() { printf '\033[31m[dev] %s\033[0m\n' "$*" >&2; exit 1; }

# ---------- 运行环境 ----------
# PATH 上的 node 如果坏了（例如 Homebrew 的 node 与 simdjson 版本失配），
# 自动退回 fnm 的 default 版本，不依赖 shell 里是否 eval 过 fnm env。
NODE=(node)
NPM=(npm)
if ! node -v >/dev/null 2>&1; then
  if command -v fnm >/dev/null 2>&1 && fnm exec --using=default -- node -v >/dev/null 2>&1; then
    NODE=(fnm exec --using=default -- node)
    NPM=(fnm exec --using=default -- npm)
    info "PATH 上的 node 不可用，改用 fnm default（$("${NODE[@]}" -v)）"
  else
    fail "找不到可用的 node，请先安装（fnm install 22 或 brew install node）"
  fi
fi
"${NPM[@]}" -v >/dev/null 2>&1 || fail "npm 不可用"
command -v uv >/dev/null 2>&1 || fail "找不到 uv，请先安装：https://docs.astral.sh/uv/"

# 直接尝试连接，不依赖 lsof（lsof 在某些沙箱里会误报）
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1; }
if port_busy "$BE_PORT"; then
  fail "后端端口 $BE_PORT 已被占用，可换端口：SM_BE_PORT=8010 bash scripts/dev.sh"
fi
if port_busy "$FE_PORT"; then
  fail "前端端口 $FE_PORT 已被占用，可换端口：SM_FE_PORT=5183 bash scripts/dev.sh"
fi

# ---------- 依赖 ----------
if [ ! -x "$ROOT/backend/.venv/bin/python" ]; then
  info "后端缺少 .venv，先执行 uv sync"
  ( cd "$ROOT/backend" && uv sync ) || fail "uv sync 失败"
fi
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  info "前端缺少 node_modules，先执行 npm install"
  ( cd "$ROOT/frontend" && "${NPM[@]}" install ) || fail "npm install 失败"
fi

# ---------- 启停 ----------
# set -m：每个后台任务自成进程组。退出时按组结束，uvicorn 的 reload 子进程和 vite 都能带走。
set -m
BE_PID=''
FE_PID=''
running=()
stopped=0

cleanup() {
  trap - INT TERM EXIT
  stopped=1
  local pid
  for pid in "${running[@]}"; do
    kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
  done
  wait 2>/dev/null
  info "已停止前后端"
}
trap cleanup INT TERM EXIT

info "后端 → http://127.0.0.1:$BE_PORT （文档 /docs）"
( cd "$ROOT/backend" && exec uv run uvicorn app.main:app --reload --port "$BE_PORT" ) &
BE_PID=$!
running+=("$BE_PID")

info "前端 → http://127.0.0.1:$FE_PORT"
(
  cd "$ROOT/frontend" &&
  export SM_API_TARGET="http://127.0.0.1:$BE_PORT" &&
  exec "${NPM[@]}" run dev -- --host 127.0.0.1 --port "$FE_PORT"
) &
FE_PID=$!
running+=("$FE_PID")

# ---------- 等待就绪 ----------
ready=0
i=0
while [ "$i" -lt 120 ]; do
  if curl -fsS --max-time 1 "http://127.0.0.1:$BE_PORT/api/v1/meta" >/dev/null 2>&1 &&
    curl -fsS --max-time 1 "http://127.0.0.1:$FE_PORT/" >/dev/null 2>&1; then
    ready=1
    break
  fi
  kill -0 "$BE_PID" 2>/dev/null || fail "后端启动失败，见上方日志"
  kill -0 "$FE_PID" 2>/dev/null || fail "前端启动失败，见上方日志"
  sleep 0.5
  i=$((i + 1))
done

if [ "$ready" -eq 1 ]; then
  printf '\n  前端  \033[1mhttp://127.0.0.1:%s\033[0m\n' "$FE_PORT"
  printf '  后端  http://127.0.0.1:%s/docs\n\n  Ctrl-C 同时停止\n\n' "$BE_PORT"
else
  info "等待就绪超时，服务可能仍在启动，请查看上方日志"
fi

# 任一端退出就结束脚本（EXIT trap 收掉另一端）
while kill -0 "$BE_PID" 2>/dev/null && kill -0 "$FE_PID" 2>/dev/null; do
  sleep 1
done

if [ "$stopped" -eq 1 ]; then
  exit 0 # Ctrl-C / kill -TERM：正常退出
fi
info "有一端退出，正在收掉另一端"
exit 1
