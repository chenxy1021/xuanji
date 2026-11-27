# 被 paipan.sh / selftest.sh 引用：探测可用的 Node 运行时，结果放进 $NODE。
#
# 为什么需要这一层：技能要装到别人的电脑上跑，而 node 未必在 PATH 里。
# WorkBuddy 客户端会在 ~/.workbuddy/binaries/node/versions/ 下自带一份运行时，
# 优先用它，用户就不用自己装 Node。也可用 ZIWEI_NODE 显式指定。

is_node() {
  [ -n "${1:-}" ] && [ -e "$1" ] && "$1" -e 'process.exit(0)' >/dev/null 2>&1
}

find_node() {
  if is_node "${ZIWEI_NODE:-}"; then
    echo "$ZIWEI_NODE"; return 0
  fi
  if command -v node >/dev/null 2>&1 && is_node "$(command -v node)"; then
    command -v node; return 0
  fi
  for root in \
      "${HOME:-}/.workbuddy/binaries/node/versions" \
      "${USERPROFILE:-}/.workbuddy/binaries/node/versions" \
      "${LOCALAPPDATA:-}/Programs/nodejs" \
      "/usr/local/bin" \
      "/opt/homebrew/bin" \
      "/usr/bin"; do
    [ -d "$root" ] || continue
    # macOS/Linux: versions/<ver>/bin/node；Windows: versions/<ver>/node.exe
    for cand in "$root"/*/bin/node "$root"/*/node.exe "$root"/node "$root"/node.exe; do
      [ -e "$cand" ] || continue
      if is_node "$cand"; then echo "$cand"; return 0; fi
    done
  done
  return 1
}

NODE=$(find_node 2>/dev/null || true)

if [ -z "${NODE:-}" ]; then
  cat >&2 <<'EOF'
✗ 没找到可用的 Node 运行时，排盘无法进行（也不会凭空编一张盘）。

按顺序找过：
  1. 环境变量 $ZIWEI_NODE
  2. PATH 里的 node
  3. WorkBuddy 自带的 ~/.workbuddy/binaries/node/versions/*/bin/node（Windows 为 node.exe）
  4. 常见安装位置：/usr/local/bin、/opt/homebrew/bin、%LOCALAPPDATA%\Programs\nodejs

怎么办（任选一条）：
  · 把 WorkBuddy 客户端完全退出再打开，让平台重新准备运行时，然后重试；
  · 自己装 Node 18+：https://nodejs.org/ （装完重开终端）；
  · 已经装了但不在 PATH：export ZIWEI_NODE=/实际/路径/node 后再跑。

不要手写星曜位置、不要凭生日推测盘面 —— 错盘比没盘更糟。
EOF
  exit 127
fi

export NODE
