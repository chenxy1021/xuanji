#!/usr/bin/env bash
# 一键隔离冒烟：临时 SQLite 库 + 临时 AI 配置 + 8001 后端 + 5183 前端，跑完整 scripts/smoke.mjs。
# 不碰真实的 8000/5173；结束（含 Ctrl-C / 失败）时自动清理子进程与临时库。
#
#   bash scripts/smoke-isolated.sh
#   SMOKE_BE_PORT=8011 SMOKE_FE_PORT=5213 bash scripts/smoke-isolated.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BE_PORT="${SMOKE_BE_PORT:-8001}"
FE_PORT="${SMOKE_FE_PORT:-5183}"
UVICORN="${UVICORN:-$ROOT/backend/.venv/bin/uvicorn}"

fail() {
  echo "✖ $*" >&2
  exit 1
}

[[ -x "$UVICORN" ]] || fail "找不到 $UVICORN；用 UVICORN=/path/to/uvicorn 指定"
command -v node >/dev/null || fail "找不到 node"
[[ -d "$ROOT/frontend/node_modules" ]] || fail "frontend/node_modules 不存在，先 cd frontend && npm install"

busy() {
  # lsof 不可用时退回 /dev/tcp 探测
  if command -v lsof >/dev/null; then
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
  fi
}

for port in "$BE_PORT" "$FE_PORT"; do
  busy "$port" && fail "端口 $port 已被占用：临时冒烟要独占端口（可用 SMOKE_BE_PORT / SMOKE_FE_PORT 改）。真实 8000/5173 不应被使用。"
done
[[ "$BE_PORT" != "$FE_PORT" ]] || fail "后端与前端端口不能相同"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/smoke-iso.XXXXXX")" || fail "创建临时目录失败"
DB="$TMP_DIR/smoke.db"
# AI 配置也隔离：用例 22 会 PUT/DELETE /settings/llm，不能落到真实 backend/.local/llm.json
LLM_CONFIG="$TMP_DIR/llm.json"
BE_LOG="$TMP_DIR/backend.log"
FE_LOG="$TMP_DIR/vite.log"
BE_PID=""
FE_PID=""

cleanup() {
  local code=$?
  for pid in "$BE_PID" "$FE_PID"; do
    [[ -n "$pid" ]] || continue
    kill "$pid" 2>/dev/null
  done
  # 给 uvicorn/vite 一点时间自己退出，再补一刀
  sleep 0.5
  for pid in "$BE_PID" "$FE_PID"; do
    [[ -n "$pid" ]] || continue
    kill -9 "$pid" 2>/dev/null
  done
  rm -rf "$TMP_DIR"
  exit "$code"
}
trap cleanup EXIT INT TERM

wait_http() {
  local url="$1" name="$2" log="$3" pid="$4"
  for _ in $(seq 1 100); do
    if curl -fsS -o /dev/null --max-time 2 "$url"; then return 0; fi
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "--- $name 日志 ---" >&2
      tail -30 "$log" >&2
      fail "$name 进程已退出"
    fi
    sleep 0.3
  done
  echo "--- $name 日志 ---" >&2
  tail -30 "$log" >&2
  fail "等待 $name 就绪超时：$url"
}

echo "临时库 $DB"
echo "后端 :$BE_PORT   前端 :$FE_PORT"

(
  cd "$ROOT/backend" || exit 1
  SM_DB_PATH="$DB" SM_LLM_CONFIG_PATH="$LLM_CONFIG" exec "$UVICORN" app.main:app --port "$BE_PORT" --host 127.0.0.1
) >"$BE_LOG" 2>&1 &
BE_PID=$!

(
  cd "$ROOT/frontend" || exit 1
  SM_API_TARGET="http://127.0.0.1:$BE_PORT" exec ./node_modules/.bin/vite --port "$FE_PORT" --strictPort
) >"$FE_LOG" 2>&1 &
FE_PID=$!

wait_http "http://127.0.0.1:$BE_PORT/health" "后端" "$BE_LOG" "$BE_PID"
wait_http "http://localhost:$FE_PORT/" "前端" "$FE_LOG" "$FE_PID"

SMOKE_BASE="http://localhost:$FE_PORT" \
SMOKE_API="http://127.0.0.1:$BE_PORT" \
SMOKE_DB="$DB" \
SM_LLM_CONFIG_PATH="$LLM_CONFIG" \
node "$ROOT/scripts/smoke.mjs"
