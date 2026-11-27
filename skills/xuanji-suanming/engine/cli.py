#!/usr/bin/env python3
"""多体系排盘 CLI：统一 11 个体系的输入，输出 JSON + Markdown。

不依赖项目后端服务，只需要 backend/.venv 里的几个计算库。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load_vendored_libs() -> None:
    """把 engine/pylibs.tar.xz 解到缓存目录并加入 sys.path。

    原生扩展（pydantic_core / swisseph / qimen_rs）不能直接从 zip 里 import，
    所以第一次运行时解压；之后按文件大小和修改时间复用缓存。
    """
    import os
    import tarfile
    import tempfile
    import zipfile

    engine = Path(sys.argv[0]).resolve().parent
    archive = engine / "pylibs.tar.xz"
    if not archive.is_file():
        archive = engine / "pylibs.zip"
    if not archive.is_file():
        return
    stat = archive.stat()
    cache = Path(os.environ.get("XUANJI_CACHE") or (Path.home() / ".cache" / "ziwei-paipan"))
    target = cache / f"pylibs-{stat.st_size}-{int(stat.st_mtime)}"
    if not (target / ".ready").is_file():
        cache.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="pylibs-", dir=cache))
        if archive.suffix == ".xz":
            with tarfile.open(archive, "r:xz") as bundle:
                bundle.extractall(tmp, filter="data")
        else:
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(tmp)
        (tmp / ".ready").touch()
        try:
            tmp.rename(target)
        except OSError:
            if not (target / ".ready").is_file():
                raise
    sys.path.insert(0, str(target))


load_vendored_libs()

from app.domains import get_domain, list_specs  # noqa: E402
from app.domains.shared.cities import find_city  # noqa: E402
from app.core.types import BirthInput, Place  # noqa: E402
from app.render_html import render_envelope_html  # noqa: E402

SYSTEM_ALIASES = {
    "紫微": "ziwei",
    "紫微斗数": "ziwei",
    "八字": "bazi",
    "四柱": "bazi",
    "占星": "astrology",
    "星盘": "astrology",
    "奇门": "qimen",
    "八字合盘": "bazi_hepan",
    "紫微合盘": "ziwei_hepan",
    "六爻": "liuyao",
    "塔罗": "tarot",
    "梅花": "meihua",
    "梅花易数": "meihua",
    "孔明": "kongming",
    "孔明神卦": "kongming",
    "mbti": "mbti",
}


def fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(2)


def parse_date(raw: str | None) -> tuple[int, int, int] | None:
    if not raw:
        return None
    try:
        value = datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        fail(f"日期格式应为 YYYY-MM-DD，收到：{raw}")
    return value.year, value.month, value.day


def place_from(args: argparse.Namespace, prefix: str = "") -> Place | None:
    city = getattr(args, f"{prefix}city")
    lon = getattr(args, f"{prefix}longitude")
    lat = getattr(args, f"{prefix}latitude")
    tz = getattr(args, f"{prefix}timezone")
    if city:
        hit = find_city(city)
        if hit is None:
            fail(f"城市库里没有「{city}」，请改用 --{prefix}longitude/--{prefix}latitude")
        return hit
    if lon is None and lat is None:
        return None
    flag = prefix.replace("_", "-")
    if lon is None or lat is None:
        fail(f"经纬度要同时给：--{flag}longitude 与 --{flag}latitude")
    return Place(longitude=lon, latitude=lat, timezone=tz)


def sanitize_name(raw: str | None) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", (raw or "").strip())
    cleaned = re.sub(r"\.+$", "", cleaned)
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    return cleaned or "未命名"


def parse_gender(raw: str | None, flag_name: str = "--gender") -> str:
    val = (raw or "").strip().lower()
    if val in ("male", "m", "男"):
        return "male"
    if val in ("female", "f", "女"):
        return "female"
    fail(f"{flag_name} 只能是 male/female 或 男/女，收到：{raw}")


def birth_from(args: argparse.Namespace, prefix: str = "") -> BirthInput:
    solar = getattr(args, f"{prefix}solar")
    lunar = getattr(args, f"{prefix}lunar")
    if bool(solar) == bool(lunar):
        fail(f"--{prefix}solar 与 --{prefix}lunar 必须二选一")
    parsed = parse_date(solar or lunar)
    year, month, day = parsed

    raw_time = getattr(args, f"{prefix}time")
    shichen = getattr(args, f"{prefix}shichen")
    hour = minute = None
    if raw_time:
        try:
            clock = datetime.strptime(raw_time.strip(), "%H:%M")
        except ValueError:
            fail(f"时间格式应为 HH:MM，收到：{raw_time}")
        hour, minute = clock.hour, clock.minute
    if shichen and raw_time:
        fail("--time 与 --shichen 只能给一个")

    flag = f"--{prefix.replace('_', '-')}gender"
    gender = parse_gender(getattr(args, f"{prefix}gender"), flag)
    return BirthInput(
        calendar="lunar" if lunar else "solar",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        shichen=shichen,
        is_leap_month=getattr(args, f"{prefix}leap"),
        gender=gender,
        place=place_from(args, prefix),
    )


def split_numbers(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    try:
        return [int(part) for part in raw.replace("，", ",").split(",") if part.strip()]
    except ValueError:
        fail(f"数字列表格式不对：{raw}")


def build_options(args: argparse.Namespace, system: str) -> dict:
    options: dict = {}
    for key in ("question", "characters", "spread", "seed"):
        value = getattr(args, key, None)
        if value not in (None, ""):
            options[key] = value
    if args.method:
        options["method"] = args.method
    if args.lines:
        options["lines"] = split_numbers(args.lines)
    if args.numbers:
        options["numbers"] = split_numbers(args.numbers)
    if args.answers:
        options["answers"] = split_numbers(args.answers)
    if args.date:
        options["date"] = args.date
    if args.year is not None:
        options["year"] = args.year
    if args.hour is not None:
        options["hour"] = args.hour
    if args.minute is not None:
        options["minute"] = args.minute
    if system in ("bazi_hepan", "ziwei_hepan"):
        options["secondary"] = birth_from(args, "second_").model_dump(mode="json")
    return options


def main() -> None:
    parser = argparse.ArgumentParser(description="玄机 · 多体系排盘")
    parser.add_argument("--list", action="store_true", help="列出全部体系")
    parser.add_argument("--questions", action="store_true", help="打印 MBTI 的 32 道题")
    parser.add_argument("--system", default="bazi")
    parser.add_argument("--name", default="未命名")
    parser.add_argument("--gender", default="male")
    parser.add_argument("--solar")
    parser.add_argument("--lunar")
    parser.add_argument("--time")
    parser.add_argument("--shichen")
    parser.add_argument("--leap", action="store_true")
    parser.add_argument("--city")
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--timezone", type=float, default=8.0)
    parser.add_argument("--year", type=int)
    parser.add_argument("--second-name", default="对方")
    parser.add_argument("--second-gender", default="female")
    parser.add_argument("--second-solar")
    parser.add_argument("--second-lunar")
    parser.add_argument("--second-time")
    parser.add_argument("--second-shichen")
    parser.add_argument("--second-leap", action="store_true")
    parser.add_argument("--second-city")
    parser.add_argument("--second-longitude", type=float)
    parser.add_argument("--second-latitude", type=float)
    parser.add_argument("--second-timezone", type=float, default=8.0)
    parser.add_argument("--method")
    parser.add_argument("--lines", help="六爻铜钱：6 个 6/7/8/9，逗号分隔")
    parser.add_argument("--numbers", help="数字起卦：两个数逗号分隔")
    parser.add_argument("--answers", help="MBTI：32 个 1-5，逗号分隔")
    parser.add_argument("--question")
    parser.add_argument("--characters", help="孔明神卦：三个汉字")
    parser.add_argument("--spread")
    parser.add_argument("--seed")
    parser.add_argument("--date")
    parser.add_argument("--hour", type=int)
    parser.add_argument("--minute", type=int)
    parser.add_argument("--out", help="输出目录（--list 时可省略）")
    parser.add_argument("--json-only", action="store_true", help="只输出 JSON，不生成 HTML/MD")
    parser.add_argument("--quiet", action="store_true", help="只打印主输出文件路径")
    args = parser.parse_args()

    if args.list:
        for spec in list_specs():
            need = "生辰" if spec.requires_birth else "无需生辰"
            print(f"{spec.id:14} {spec.name}  ({need})")
        return
    if args.questions:
        from app.domains.mbti.constants import QUESTIONS, SCALE

        print("1=非常不同意 2=不同意 3=说不好 4=同意 5=非常同意\n")
        for index, item in enumerate(QUESTIONS, start=1):
            print(f"{index:02d}. {item['text']}（{item['dim']}）")
        return
    if not args.out:
        fail("缺少 --out 输出目录")

    system = SYSTEM_ALIASES.get(args.system.strip().lower(), args.system.strip().lower())
    domain = get_domain(system)
    birth = birth_from(args) if domain.SPEC.requires_birth else None
    options = build_options(args, system)
    envelope = domain.compute(birth, options)

    stamp = date.today().isoformat()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_name(args.name)
    stem = f"{safe_name}-{stamp}-{system}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    html_path = out_dir / f"{stem}.html"
    json_path.write_text(
        json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not args.json_only:
        md_path.write_text(envelope.text.strip() + "\n", encoding="utf-8")
        html_path.write_text(
            render_envelope_html(envelope, title=args.name.strip() or "未命名"),
            encoding="utf-8",
        )

    if args.quiet:
        print(json_path if args.json_only else html_path)
        return

    print(f"✓ {domain.SPEC.name} · {args.name}")
    for warning in envelope.warnings:
        print(f"! {warning}")
    if not args.json_only:
        print(f"HTML: {html_path}")
        print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except ModuleNotFoundError as exc:
        print(
            f"✗ 引擎组件没加载起来（{exc.name}）。\n"
            f"  试着重开 WorkBuddy 让它准备 Python 3.13 运行时；紫微排盘不需要 Python。",
            file=sys.stderr,
        )
        raise SystemExit(2)
    except Exception as exc:  # noqa: BLE001
        detail = getattr(exc, "detail", None)
        message = detail.get("message") if isinstance(detail, dict) else None
        print(f"✗ {message or exc}", file=sys.stderr)
        raise SystemExit(2)
