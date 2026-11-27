# 十一个体系：输入、命令与产物

统一入口是 `scripts/paipan.sh`。默认 `--system ziwei`；不写 `--system` 时也走紫微。
所有命令的 `--out` 指向**用户工作区**，不要写进技能目录。

```bash
SKILL_DIR=$(dirname "$(dirname "$(find "$HOME/.workbuddy" "$PWD" -maxdepth 9 \
  -name paipan.sh -path '*ziwei-paipan*' 2>/dev/null | head -1)")")
```

## 总表

| `--system` | 名称 | 需要生辰 | 需要第二人 | 产物 |
|---|---|---|---|---|
| `ziwei` | 紫微斗数 | 是 | 否 | HTML 命盘 + JSON |
| `bazi` | 四柱八字 | 是 | 否 | HTML 报告 + JSON + Markdown |
| `astrology` | 西方占星 | 是（要准确时刻） | 否 | HTML 报告 + JSON + Markdown |
| `qimen` | 奇门终身局 | 是（要准确时刻） | 否 | HTML 报告 + JSON + Markdown |
| `ziwei_hepan` | 紫微合盘 | 是 | 是 | HTML 报告 + JSON + Markdown |
| `bazi_hepan` | 八字合盘 | 是 | 是 | HTML 报告 + JSON + Markdown |
| `liuyao` | 六爻纳甲 | 否 | 否 | HTML 报告 + JSON + Markdown |
| `meihua` | 梅花易数 | 否 | 否 | HTML 报告 + JSON + Markdown |
| `tarot` | 塔罗牌 | 否 | 否 | HTML 报告 + JSON + Markdown |
| `kongming` | 孔明神卦 | 否 | 否 | HTML 报告 + JSON + Markdown |
| `mbti` | MBTI 测试 | 否 | 否 | HTML 报告 + JSON + Markdown |

## 生辰参数（ziwei / bazi / astrology / qimen / 两种合盘）

| 参数 | 说明 |
|---|---|
| `--solar YYYY-MM-DD` | 公历生日，与 `--lunar` 二选一 |
| `--lunar YYYY-MM-DD` | 农历生日；闰月加 `--leap` |
| `--time HH:MM` | 出生钟表时间，24 小时制 |
| `--shichen 子..亥` | 只知道时辰时用，与 `--time` 二选一 |
| `--gender male\|female` | 必填（也接受 男/女） |
| `--city 长沙` | 从 107 个主要城市里查经纬度，做真太阳时校正 |
| `--longitude 112.9 --latitude 28.2` | 城市不在库里时直接给坐标 |
| `--timezone 8` | 当地标准时相对 UTC 的偏移，默认 8 |
| `--name 张三` | 产物文件名与盘面标题 |

合盘的第二人换前缀：`--second-solar`、`--second-time`、`--second-gender`、
`--second-city`、`--second-longitude`、`--second-latitude`、`--second-leap`。

紫微额外支持：`--year 2026`（流年）、`--school QS|XD1|ZZ|XD2`（亮度流派）、
`--leap-policy split|next-month|prev-month|origin-month`、`--json-only`、`--quiet`。

```bash
sh "$SKILL_DIR/scripts/paipan.sh" --name 张三 --gender male \
  --solar 1994-10-21 --time 08:45 --city 长沙 --out "$PWD/charts"

sh "$SKILL_DIR/scripts/paipan.sh" --system bazi --name 张三 --gender male \
  --solar 1994-10-21 --time 08:45 --city 长沙 --out "$PWD/charts"

sh "$SKILL_DIR/scripts/paipan.sh" --system ziwei_hepan --name 张三 --gender male \
  --solar 1994-10-21 --time 08:45 --city 长沙 \
  --second-name 李四 --second-gender female \
  --second-solar 1996-03-08 --second-time 20:30 --second-city 杭州 \
  --out "$PWD/charts"
```

## 六爻

三种起卦方式，`--method` 不写时按 `coins`：

| 方式 | 参数 | 说明 |
|---|---|---|
| 铜钱 | `--method coins --lines 7,8,9,6,7,8` | 六个 6/7/8/9，自下而上；6 老阴、7 少阳、8 少阴、9 老阳 |
| 时间 | `--method time --date 2026-11-24 --hour 18` | 不写日期按今天 |
| 数字 | `--method number --numbers 37,18` | 两个正整数 |

加 `--question "这份工作要不要接"`。起卦时刻会写进结果；未给时间就按当前时刻。
**空亡本期未计算**，断卦时不要假装算过。

## 梅花易数

| 方式 | 参数 |
|---|---|
| 时间 | `--method time --date 2026-11-24 --hour 18` |
| 数字 | `--method number --numbers 37,18` |

不能起卦的时间（如半夜不方便）就改用数字；同一件事不要反复起卦。

## 塔罗

`--spread three`（过去/现在/未来）；`--question` 写具体问题；
`--seed` 只用于复现同一组牌，正常抽牌不要传。

## 孔明神卦

`--characters 佑咱统`（三个汉字，必填）+ `--question`。
简体按常用繁体折算笔画；一次只问一件事。

## MBTI

先打印题库，再收集 32 个 1–5 的答案：

```bash
sh "$SKILL_DIR/scripts/paipan.sh" --questions
sh "$SKILL_DIR/scripts/paipan.sh" --system mbti --name 张三 \
  --answers 3,4,2,3,5,3,3,2,4,3,3,3,2,4,5,3,3,2,3,4,3,3,3,2,4,3,5,3,3,4,2,3 \
  --out "$PWD/charts"
```

## 产物约定

- 紫微：`<姓名>-<生日>-紫微命盘.html` 与 `.json`。HTML 给用户看（纸墨朱砂版式，支持夜读深墨切换、点击宫位联动高亮三方四正、流年四化与格局总览），JSON 是解读的唯一事实源。
- 其余 10 个体系：`<姓名>-<今天>-<system>.html`、`.json` 与同名 `.md`（加 `--json-only` 只出 JSON，加 `--quiet` 只打印主输出路径）。
- JSON 是统一的 `ChartEnvelope`：`system / engine_version / input / chart / text / warnings`。
- Markdown 就是 `text` 字段，已经排好表格；**解读时先读 JSON 或 Markdown，再动笔**。

## 常见失败

| 输出 | 原因 | 处理 |
|---|---|---|
| `城市库里没有「九江」` | 城市库只有 107 个主要城市 | 改用 `--longitude/--latitude`，或换最近的大城市并说明 |
| `没找到 Python 3.13 运行时` | 非紫微体系要匹配自带计算库的 ABI | 退出 WorkBuddy 重开；或 `export XUANJI_PY=/路径/python3.13` |
| `引擎组件没加载起来` | 缓存损坏或运行时不匹配 | 删除 `~/.cache/ziwei-paipan` 后重试；仍不行重装技能 |
| `缺 Python 依赖 swisseph` | 占星要 `pyswisseph` | 按提示安装 |
| `缺 Python 依赖 qimen_rs` | 奇门要 `qimen-rs` | 按提示安装 |
| `日期格式应为 YYYY-MM-DD` | 输入格式错 | 让用户核对，不要自行顺延 |
| `--solar 与 --lunar 必须二选一` | 历法没确认 | 先问清农历还是公历 |
| `需要回答全部 32 道题` | MBTI 答案数量不对 | 重新收集，别补默认值 |
