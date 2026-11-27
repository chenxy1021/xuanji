#!/bin/sh
# 自检启动器：同样自己找 Node，然后跑 selftest.mjs。
#
#   sh scripts/selftest.sh

set -u
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$DIR/node-env.sh"

exec "$NODE" "$DIR/selftest.mjs" "$@"
