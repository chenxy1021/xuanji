#!/bin/sh
# 多体系排盘启动器：
#   --system ziwei（默认）走内置 Node，额外产出 HTML 命盘；
#   其余 10 个体系走 engine/xuanji.pyz，输出 JSON + Markdown。
#
#   sh scripts/paipan.sh --system bazi --name 张三 --gender male \
#     --solar 1994-10-21 --time 08:45 --city 九江 --out ./charts

set -u
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

SYSTEM=ziwei
prev=
for arg in "$@"; do
  if [ "$prev" = "--system" ]; then SYSTEM=$arg; fi
  case "$arg" in
    --system=*) SYSTEM=${arg#--system=} ;;
    --list|--questions) SYSTEM=list ;;
  esac
  prev=$arg
done

case "$SYSTEM" in
  ziwei|紫微|紫微斗数)
    . "$DIR/node-env.sh"
    exec "$NODE" "$DIR/paipan.mjs" "$@"
    ;;
esac

. "$DIR/py-env.sh"
exec "$PY" "$DIR/../engine/xuanji.pyz" "$@"
