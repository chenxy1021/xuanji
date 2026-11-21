#!/usr/bin/env bash
# 把本机网站挂成 Cloudflare 临时 HTTPS 地址，并设为 Telegram 机器人底部菜单按钮（Mini App）。
#
#   bash scripts/telegram-miniapp.sh               # 起隧道 + 设置菜单按钮，前台常驻，Ctrl-C 结束
#   bash scripts/telegram-miniapp.sh --dry-run     # 不调 Telegram，只打印将发送的 JSON（仍起隧道）
#   bash scripts/telegram-miniapp.sh --no-menu     # 只起隧道，不动菜单按钮
#
# 可调环境变量：
#   SM_MINIAPP_TEXT        菜单按钮文案，默认「玄机算命」
#   SM_TUNNEL_PORT         隧道指向的本机端口，默认 5173（前端 dev server）
#   SM_MINIAPP_API_PORT    后端端口，默认 8000（只用于健康检查）
#   SM_BOT_USERNAME        提示里展示的机器人用户名，默认 cxy_muse_bot
#   SM_TUNNEL_HOLD_SECONDS 常驻秒数后自动退出；不设则一直挂着（自动化测试用）
#   CLOUDFLARED            cloudflared 路径，默认 /opt/homebrew/bin/cloudflared
#
# token 只从 backend/.local/telegram.json（0600）或 SM_TELEGRAM_BOT_TOKEN 读取，
# 全程只在 python 进程内使用，不进命令行参数、不进日志、不打印。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLOUDFLARED="${CLOUDFLARED:-/opt/homebrew/bin/cloudflared}"
PORT="${SM_TUNNEL_PORT:-5173}"
API_PORT="${SM_MINIAPP_API_PORT:-8000}"
TEXT="${SM_MINIAPP_TEXT:-玄机算命}"
BOT_USERNAME="${SM_BOT_USERNAME:-cxy_muse_bot}"
CONFIG_FILE="${SM_TELEGRAM_CONFIG:-$ROOT/backend/.local/telegram.json}"
HOLD="${SM_TUNNEL_HOLD_SECONDS:-0}"

DRY_RUN=0
NO_MENU=0
CF_PID=""
LOG=""

fail() {
  echo "✖ $*" >&2
  exit 1
}

usage() {
  # 打印文件头的注释块，遇到第一行非注释就停
  awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "${BASH_SOURCE[0]}"
  exit 0
}

cleanup() {
  local code=$?
  trap - EXIT INT TERM
  if [[ -n "$CF_PID" ]] && kill -0 "$CF_PID" 2>/dev/null; then
    kill "$CF_PID" 2>/dev/null
    for _ in $(seq 1 15); do
      kill -0 "$CF_PID" 2>/dev/null || break
      sleep 0.2
    done
    kill -9 "$CF_PID" 2>/dev/null
  fi
  [[ -n "$LOG" && -f "$LOG" ]] && rm -f "$LOG"
  exit "$code"
}
trap cleanup EXIT INT TERM

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-menu) NO_MENU=1 ;;
    -h | --help) usage ;;
    *) fail "不认识的参数：$arg（可用 --dry-run / --no-menu / --help）" ;;
  esac
done

# 1) 前置检查：cloudflared 与本机服务 ----------------
[[ -x "$CLOUDFLARED" ]] || fail "找不到 $CLOUDFLARED；用 CLOUDFLARED=/path/to/cloudflared 指定（brew install cloudflared）"
command -v curl >/dev/null || fail "找不到 curl"
command -v python3 >/dev/null || fail "找不到 python3（读取 token 与调用 Telegram 都用它）"

probe() { # url 名字 提示
  local url="$1" name="$2" hint="$3" code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 "$url" 2>/dev/null)"
  [[ "$code" == "200" ]] || fail "$name 不可访问（$url → ${code:-无响应}）。$hint"
}

probe "http://127.0.0.1:$PORT/" "前端 :$PORT" "先启动前端：cd frontend && npm run dev（本脚本不负责拉起服务）"
probe "http://127.0.0.1:$API_PORT/api/v1/meta" "后端 :$API_PORT" "先启动后端：cd backend && uv run uvicorn app.main:app --port $API_PORT"

# 2) 起 cloudflared quick tunnel，解析公网地址 --------------------------
LOG="$(mktemp "${TMPDIR:-/tmp}/cloudflared.XXXXXXXX")" || fail "创建临时日志失败"
echo "启动 cloudflared（→ http://127.0.0.1:$PORT），日志 $LOG"

"$CLOUDFLARED" tunnel --url "http://127.0.0.1:$PORT" --no-autoupdate >"$LOG" 2>&1 &
CF_PID=$!

URL=""
for _ in $(seq 1 60); do # 最多等 30 秒
  URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1)"
  [[ -n "$URL" ]] && break
  if ! kill -0 "$CF_PID" 2>/dev/null; then
    echo "--- cloudflared 日志尾部 ---" >&2
    tail -20 "$LOG" >&2
    fail "cloudflared 启动后立即退出"
  fi
  sleep 0.5
done

if [[ -z "$URL" ]]; then
  echo "--- cloudflared 日志尾部 ---" >&2
  tail -20 "$LOG" >&2
  fail "30 秒内没解析到 trycloudflare.com 地址"
fi

echo "公网地址 $URL"

# 3) 经隧道回访：DNS 生效要几秒，重试到 200 -------------------------
# 刚打印出的域名往往还解析不到，系统会缓存这次 NXDOMAIN，所以要等一下再探、多探几轮。
sleep 4

wait_http() { # url 名字 → 打印状态码
  local url="$1" code=""
  for _ in $(seq 1 30); do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$url" 2>/dev/null)"
    [[ "$code" == "200" ]] && break
    sleep 2
  done
  echo "$code"
}

ROOT_CODE="$(wait_http "$URL/")"
API_CODE="$(wait_http "$URL/api/v1/meta")"
echo "回访结果：/ → ${ROOT_CODE:-无响应}，/api/v1/meta → ${API_CODE:-无响应}"

HOST_BLOCKED=0
if [[ "$ROOT_CODE" != "200" ]]; then
  if curl -s --max-time 8 "$URL/" 2>/dev/null | grep -q "Blocked request"; then
    HOST_BLOCKED=1
    cat >&2 <<EOF
⚠ 前端 dev server 拒绝了隧道域名（Vite 的 host 校验）。
  仓库里 frontend/vite.config.ts 原本有 allowedHosts: ['.trycloudflare.com']，
  如果它被删了或换了域名，请补回这一行并重启前端。
  本脚本不改前端代码，只做提示；长期可用建议上固定域名（见 README「Telegram Mini App」）。
EOF
  else
    echo "⚠ 隧道已建立但回访不是 200：先确认本机 $PORT 正常，再重试（quick tunnel 首次解析可能要十几秒）。" >&2
  fi
fi

HEALTHY=0
[[ "$ROOT_CODE" == "200" && "$API_CODE" == "200" ]] && HEALTHY=1

# 4) 设置 Telegram 菜单按钮 ------------------------------------------
set_menu() { # url 文案
  SM_TELEGRAM_CONFIG="$CONFIG_FILE" python3 - "$1" "$2" <<'PY'
import json
import os
import stat
import sys
import urllib.error
import urllib.request

DEFAULT_PROXY = "http://127.0.0.1:7897"
API = "https://api.telegram.org/bot{}/{}"


def die(message, code=1):
    sys.stdout.write(message + "\n")
    raise SystemExit(code)


def load():
    """token/proxy 只在进程内使用，绝不打印。"""
    token = os.environ.get("SM_TELEGRAM_BOT_TOKEN", "").strip()
    proxy = os.environ.get("SM_TELEGRAM_PROXY", "").strip()
    path = os.environ.get("SM_TELEGRAM_CONFIG", "").strip()
    if path and os.path.exists(path):
        mode = stat.S_IMODE(os.stat(path).st_mode)
        if mode & 0o077:
            print("⚠ 配置文件权限是 %o（建议 chmod 600），已继续" % mode)
        try:
            with open(path, encoding="utf-8") as fh:
                config = json.load(fh)
        except (OSError, ValueError) as exc:
            die("✖ 读取 %s 失败：%s" % (path, type(exc).__name__))
        if not token:
            token = str(config.get("bot_token") or "").strip()
        if not proxy:
            proxy = str(config.get("proxy") or "").strip()
    elif not token:
        die("✖ 没有 token：请创建 %s（0600，含 bot_token/proxy）或设置 SM_TELEGRAM_BOT_TOKEN" % (path or "配置文件"))
    if not token:
        die("✖ 配置文件里没有 bot_token")
    return token, proxy or DEFAULT_PROXY


def post(token, proxy, method, payload):
    request = urllib.request.Request(
        API.format(token, method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    try:
        with opener.open(request, timeout=25) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:  # Telegram 业务错误仍带 JSON body
        raw = exc.read()
    except (urllib.error.URLError, OSError) as exc:
        # 只报异常类型：异常文本里含带 token 的 URL
        die("✖ 连不上 Telegram（%s）：确认代理 %s 可用后重试" % (type(exc).__name__, proxy))
    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        die("✖ Telegram 返回的不是 JSON")
    if not data.get("ok"):
        die("✖ Telegram 拒绝：%s" % (data.get("description") or "未知原因"))
    return data.get("result")


url, text = sys.argv[1], sys.argv[2]
if len(text) > 64:
    die("✖ 菜单文案最多 64 字，当前 %d" % len(text))
token, proxy = load()
post(
    token,
    proxy,
    "setChatMenuButton",
    {"menu_button": {"type": "web_app", "text": text, "web_app": {"url": url}}},
)
print('✔ 菜单按钮已设置：「%s」→ %s' % (text, url))
PY
}

MENU_SET=0
if [[ "$NO_MENU" -eq 1 ]]; then
  echo "按 --no-menu 跳过 Telegram 菜单按钮设置"
elif [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'dry-run：将发送给 setChatMenuButton 的 payload\n{"menu_button":{"type":"web_app","text":"%s","web_app":{"url":"%s"}}}\n' "$TEXT" "$URL"
else
  if [[ "$HEALTHY" -eq 0 && "$HOST_BLOCKED" -eq 1 ]]; then
    fail "菜单按钮指向一个 403 的地址没有意义：请先按上面的提示改 vite.config.ts 的 allowedHosts 并重启前端（或加 --dry-run 只看 URL）"
  fi
  if [[ "$HEALTHY" -eq 0 ]]; then
    echo "⚠ 回访不是 200，仍尝试设置菜单按钮；Mini App 打不开就先把本机服务修好再重跑。" >&2
  fi
  set_menu "$URL" "$TEXT" || fail "设置菜单按钮失败（token/代理见上面的提示）"
  MENU_SET=1
fi

# 5) 收尾说明 ------------------------------------------------------
cat <<EOF

────────────────────────────────────────
公网地址  $URL
菜单按钮  $([[ "$MENU_SET" -eq 1 ]] && echo "已设置为「$TEXT」(web_app)" || echo "未设置")
打开方式  Telegram → t.me/$BOT_USERNAME → 点底部菜单按钮
────────────────────────────────────────
注意：
  · quick tunnel 地址每次重启都会变，变了必须重跑本脚本（否则菜单按钮指向旧地址）。
  · 隧道只在本机运行：本机关机、5173/8000 停了，Mini App 就打不开。
  · 要固定地址：自有域名 + Cloudflare named tunnel，或 VPS 上部署后 HTTPS 反代。
  · 本轮没有做 Telegram 登录 / initData 校验，Mini App 内部仍是普通网页 + 账号密码。
EOF

if [[ "$HOLD" -gt 0 ]] 2>/dev/null; then
  echo "（$HOLD 秒后自动退出，由 SM_TUNNEL_HOLD_SECONDS 控制）"
  sleep "$HOLD"
else
  echo "隧道前台运行中，Ctrl-C 结束（会同时清理 cloudflared）。"
  wait "$CF_PID"
fi
