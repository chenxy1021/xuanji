#!/bin/sh
# 从 engine/cli.py 与 engine/app/ 重新打包 engine/xuanji.pyz，保持源码与单文件包一致。
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENGINE="$DIR/../engine"

python3 - "$ENGINE" <<'PY'
import pathlib, sys, zipfile

engine = pathlib.Path(sys.argv[1]).resolve()
out = engine / "xuanji.pyz"
tmp = engine / "xuanji.pyz.tmp"

with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(engine / "cli.py", "__main__.py")
    app_dir = engine / "app"
    for path in sorted(app_dir.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo") or path.name == ".DS_Store":
            continue
        zf.write(path, path.relative_to(engine).as_posix())

tmp.replace(out)
print(f"✓ 已重建 {out}（{out.stat().st_size:,} 字节）")
PY
