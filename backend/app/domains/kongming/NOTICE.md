# 孔明神卦数据说明

## 起卦法

诸葛神数（托名诸葛亮，又称孔明神卦）：心中默念所问之事，写下三个汉字；
每字取康熙笔画，十画以上只取个位（十画、二十画记作 0）；三字依次作百、十、个位；
超过 384 反复减 384；得 0 取第 384 签。

## 数据

- `data/kangxi.json.gz`
  - `strokes`：Unicode Unihan 数据库的 `kRSUnicode`（康熙部首序号 + 余画）与
    `kTotalStrokes` 合成，部首画数取自 Kangxi Radicals 区（U+2F00–U+2FD5）的
    `kTotalStrokes`。用于计算康熙笔画。
  - `trad`：Unihan `kTraditionalVariant` 的首选映射，用于把简体输入折算成常用繁体。
  - 来源：https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip
  - 许可：Unicode License v3（https://www.unicode.org/license.txt）。
- `data/lots.json.gz`：384 签的签号、签级、宫、卦、变卦、爻与签文。
  - 签文为传统通行本，属公版；页面文字取自卜易居《诸葛神算》公开页面
    （https://www.buyiju.com/zhuge/），仅收录签级、卦爻与四句签文，
    不收录该站的现代解签文字。
  - 本项目自撰的断语在 `constants.py`，与上述站点无关。

## 文本整理

- 兼容区汉字（U+F900–U+FAFF）按 NFKC 归一（如「郎」→「郎」）。
- 个别签文在通行本中就有异文或讹字（如第 368 签「君君九日」），本项目按原样保留，
  不擅自改写；解读层会以整体文意为准。

## 已知约定

- 简繁折算无法兼顾语境（如「干」可能对应「乾/幹」），一律取 Unihan 首选繁体；
  页面会同时显示「原字 → 折算字」，便于复核。
- 同一事不宜反复起卦；结果仅供文化娱乐参考。
