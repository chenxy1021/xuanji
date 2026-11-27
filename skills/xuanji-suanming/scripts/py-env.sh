# 被 paipan.sh 引用：找一个 Python 3.13 运行时，结果放进 $PY。
#
# 技能内的 engine/pylibs.zip 已带齐全部计算库（含原生扩展），
# 所以这里只需要匹配 ABI 的解释器，不需要用户 pip install。
# 查找顺序：$XUANJI_PY → WorkBuddy 自带 Python → PATH 里的 python3 → 项目 venv。

is_py313() {
  [ -n "${1:-}" ] && [ -x "$1" ] && \
    "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)' \
    >/dev/null 2>&1
}

find_py() {
  if is_py313 "${XUANJI_PY:-}"; then
    echo "$XUANJI_PY"; return 0
  fi
  for root in \
      "${HOME:-}/.workbuddy/binaries/python/versions" \
      "${USERPROFILE:-}/.workbuddy/binaries/python/versions"; do
    [ -d "$root" ] || continue
    for cand in "$root"/*/bin/python3 "$root"/*/python.exe; do
      if is_py313 "$cand"; then echo "$cand"; return 0; fi
    done
  done
  for name in python3.13 python3 python; do
    if command -v "$name" >/dev/null 2>&1 && is_py313 "$(command -v "$name")"; then
      command -v "$name"; return 0
    fi
  done
  for cand in \
      "$DIR/../../../backend/.venv/bin/python" \
      "$DIR/../../../backend/.venv/bin/python3"; do
    if is_py313 "$cand"; then echo "$cand"; return 0; fi
  done
  return 1
}

PY=$(find_py 2>/dev/null || true)

if [ -z "${PY:-}" ]; then
  cat >&2 <<'EOF'
✗ 没找到可用的 Python 3.13 运行时（紫微排盘不需要 Python）。

技能已经自带全部计算库，缺的只是一个 3.13 解释器。按顺序找过：
  1. 环境变量 $XUANJI_PY
  2. WorkBuddy 自带的 ~/.workbuddy/binaries/python/versions/*/
  3. PATH 里的 python3.13 / python3 / python

怎么办：
  · 把 WorkBuddy 客户端完全退出再打开，让平台重新准备运行时，然后重试；
  · 或指定现成的解释器：export XUANJI_PY=/实际/路径/python3.13
  · 只排紫微：sh scripts/paipan.sh --system ziwei ... （走内置 Node，不需要 Python）
EOF
  exit 127
fi

export PY
