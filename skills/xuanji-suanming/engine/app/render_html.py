"""玄机 · 多体系命盘 HTML 渲染器（玄夜星金版）。

为非紫微的 10 个体系（八字、奇门、占星、紫微/八字合盘、六爻、梅花、塔罗、
孔明神卦、MBTI）生成与紫微命盘同一套「深空玄黑 + 鎏金细线 + 星座罗盘 +
玻璃质感面板」的单文件 HTML；支持切换「宣纸印本」浅色模式与 A4 打印，零外部依赖。
"""

from __future__ import annotations

import html
import math
from typing import Any

from app.core.types import ChartEnvelope

STEM_ELEMENT = {
    "甲": "mu", "乙": "mu",
    "丙": "huo", "丁": "huo",
    "戊": "tu", "己": "tu",
    "庚": "jin", "辛": "jin",
    "壬": "shui", "癸": "shui",
}
BRANCH_ELEMENT = {
    "寅": "mu", "卯": "mu",
    "巳": "huo", "午": "huo",
    "辰": "tu", "戌": "tu", "丑": "tu", "未": "tu",
    "申": "jin", "酉": "jin",
    "亥": "shui", "子": "shui",
}
ELEMENT_CLASS = {"木": "mu", "火": "huo", "土": "tu", "金": "jin", "水": "shui"}

SYSTEM_TITLES = {
    "bazi": ("四柱八字命盘", "四柱 · 十神 · 大运流年"),
    "qimen": ("奇门终身局", "拆补转盘 · 三宫用神 · 洛书九宫"),
    "astrology": ("西方占星本命盘", "黄道星轮 · 普拉西度宫位 · 相位"),
    "bazi_hepan": ("八字合盘", "双人四柱 · 冲合互补 · 参考分"),
    "ziwei_hepan": ("紫微合盘", "命迁夫宫呼应 · 星曜互动 · 参考分"),
    "liuyao": ("六爻纳甲卦盘", "本卦 · 互卦 · 变卦 · 六亲世应"),
    "meihua": ("梅花易数卦盘", "体用生克 · 本互变三卦"),
    "tarot": ("塔罗牌阵", "牌面 · 正逆位 · 关键词"),
    "kongming": ("孔明神卦签文", "三字取签 · 卦爻 · 签诗"),
    "mbti": ("MBTI 性格画像", "四维倾向 · 优势与盲点"),
}

ASTROLABE_EMBLEM = """<svg class="emblem" viewBox="0 0 64 64" aria-hidden="true">
  <circle cx="32" cy="32" r="29" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="currentColor" stroke-width=".8" opacity=".35"/>
  <circle cx="32" cy="32" r="10" fill="none" stroke="currentColor" stroke-width="1" opacity=".65"/>
  <path d="M32 3v9M32 52v9M3 32h9M52 32h9M11.5 11.5l6.4 6.4M46.1 46.1l6.4 6.4M52.5 11.5l-6.4 6.4M17.9 46.1l-6.4 6.4" stroke="currentColor" stroke-width=".9" opacity=".5"/>
  <polygon points="32,14 35,29 50,32 35,35 32,50 29,35 14,32 29,29" fill="currentColor" opacity=".84"/>
  <circle cx="32" cy="32" r="3.2" fill="var(--bg)"/>
</svg>"""

CORNERS = '<i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>'


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def el_cls(char_or_el: str | None) -> str:
    if not char_or_el:
        return ""
    s = str(char_or_el).strip()
    if s in ELEMENT_CLASS:
        return f"el-{ELEMENT_CLASS[s]}"
    if s in STEM_ELEMENT:
        return f"el-{STEM_ELEMENT[s]}"
    if s in BRANCH_ELEMENT:
        return f"el-{BRANCH_ELEMENT[s]}"
    return ""


def section_head(num: str, title: str, right: str = "") -> str:
    r_html = f'<span class="sec-count">{esc(right)}</span>' if right else ""
    return f'<div class="sec-hd"><span class="sec-num">{esc(num)}</span><h2>{esc(title)}</h2>{r_html}</div>'


# ─── 1. 四柱八字 ─────────────────────────────────────────────────

def render_bazi(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or {}
    order = [("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")]
    cards = []
    for key, label in order:
        p = pillars.get(key) or {}
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        is_day = key == "day"
        cards.append(f"""
        <div class="bz-col{' is-day' if is_day else ''}">
          <div class="bz-label">{label}{' · 日主' if is_day else ''}</div>
          <div class="bz-shishen">{esc(p.get('shishen', ''))}</div>
          <div class="bz-gz">
            <span class="bz-char {el_cls(gan)}">{esc(gan)}</span>
            <span class="bz-char {el_cls(zhi)}">{esc(zhi)}</span>
          </div>
          <div class="bz-canggan">{esc(p.get('canggan', '—'))}</div>
        </div>""")

    meta_items = [
        ("性别", chart.get("gender")),
        ("公历", chart.get("solar_date")),
        ("农历", chart.get("lunar_date")),
        ("时辰", chart.get("shichen")),
        ("节气", chart.get("jie")),
        ("起运", chart.get("qiyun")),
        ("顺逆", "顺行" if chart.get("forward") else "逆行"),
    ]
    tst = chart.get("true_solar_time")
    if isinstance(tst, dict) and tst.get("true_solar_time"):
        meta_items.append(("真太阳时", f"{tst.get('true_solar_time')}（修正 {tst.get('total_correction_minutes', 0):+.1f} 分）"))

    meta_html = "".join(
        f'<div class="kv"><i>{esc(k)}</i><b>{esc(v)}</b></div>'
        for k, v in meta_items if v not in (None, "", "无")
    )

    dayun = chart.get("dayun") or []
    dy_html = "".join(
        f'<div class="dy-card"><div class="dy-idx">{esc(d.get("index"))}</div>'
        f'<div class="dy-gz">{esc(d.get("ganzhi"))}</div>'
        f'<div class="dy-age">{esc(d.get("age_range"))}</div></div>'
        for d in dayun
    )

    liunian = chart.get("liunian") or []
    ln_html = "".join(
        f'<div class="ln-chip"><span class="ln-y">{esc(l.get("year"))}</span>'
        f'<span class="ln-g">{esc(l.get("ganzhi"))}</span></div>'
        for l in liunian
    )

    shensha = chart.get("shensha") or []
    ss_html = ""
    if shensha:
        items = "".join(f'<li>{esc(str(s).lstrip("- ").strip())}</li>' for s in shensha)
        ss_html = f'<section class="sec">{CORNERS}{section_head("04", "神煞参考", f"共 {len(shensha)} 项")}<ul class="plain-list">{items}</ul></section>'

    return f"""
    <section class="sec">
      {CORNERS}
      {section_head("01", "四柱命盘", f"{chart.get('gender', '')} · {chart.get('lunar_date', '')}")}
      <div class="bz-grid">{"".join(cards)}</div>
      <div class="kv-grid">{meta_html}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "大运排盘", f"起运 {chart.get('qiyun', '')}")}
      <div class="dy-strip">{dy_html}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("03", "近年流年", f"共 {len(liunian)} 年")}
      <div class="ln-grid">{ln_html}</div>
    </section>
    {ss_html}"""


# ─── 2. 奇门终身局 ───────────────────────────────────────────────

def render_qimen(chart: dict[str, Any]) -> str:
    fp = chart.get("four_pillars") or {}
    fp_str = " ".join(fp.get(k, "") for k in ("year", "month", "day", "hour"))
    xun = chart.get("xun") or {}
    leaders = chart.get("leaders") or {}
    horse = chart.get("horse") or {}
    lifelong = chart.get("lifelong") or {}

    meta_items = [
        ("局数", f"{chart.get('ju_text', '')}（{chart.get('yuan', '')}）"),
        ("四柱", fp_str),
        ("农历", chart.get("lunar_date")),
        ("节气", f"{chart.get('solar_term', '')} → {chart.get('next_solar_term', '')}"),
        ("旬首", f"{xun.get('head', '')}（隐干 {xun.get('hidden_stem', '')} · 空亡 {'/'.join(xun.get('void_branches') or [])}）"),
        ("值符 / 值使", f"{leaders.get('star', '')}（{leaders.get('star_palace', '')}宫） / {leaders.get('door', '')}（{leaders.get('door_palace', '')}宫）"),
        ("驿马", f"{horse.get('branch', '')}（{horse.get('palace', '')}宫）"),
    ]
    meta_html = "".join(
        f'<div class="kv"><i>{esc(k)}</i><b>{esc(v)}</b></div>'
        for k, v in meta_items if v
    )

    anchor_tags: dict[int, list[str]] = {}
    for a in lifelong.get("anchors") or []:
        pno = (a.get("palace") or {}).get("number")
        if pno is not None:
            anchor_tags.setdefault(pno, []).append(a.get("label", "").replace("宫", ""))

    grid_items = chart.get("grid") or chart.get("palaces") or []
    cells = []
    for p in grid_items:
        pno = p.get("number")
        is_center = pno == 5
        tags = anchor_tags.get(pno, [])
        tag_html = "".join(f'<span class="tag gold">{esc(t)}</span>' for t in tags)
        if p.get("is_horse"):
            tag_html += '<span class="tag">马</span>'
        if p.get("void_branches"):
            tag_html += '<span class="tag accent">空</span>'
        heaven = " ".join(p.get("heaven_stems") or [])
        stars = " ".join(p.get("stars") or [])
        earth = p.get("earth_stem") or ""
        hosted = p.get("hosted_earth_stem")
        earth_str = f"{earth}（寄{hosted}）" if hosted else earth
        cells.append(f"""
        <div class="qm-cell{' is-center' if is_center else ''}{' is-anchor' if tags else ''}">
          <div class="qm-top">
            <span class="qm-deity">{esc(p.get('deity') or ('中宫' if is_center else ''))}</span>
            <span class="qm-tags">{tag_html}</span>
          </div>
          <div class="qm-mid">
            <div class="qm-star">{esc(stars)}</div>
            <div class="qm-door">{esc(p.get('door') or '')}</div>
          </div>
          <div class="qm-stems">
            <span>天 {esc(heaven or '—')}</span>
            <span>地 {esc(earth_str or '—')}</span>
          </div>
          <div class="qm-foot">
            <span>{esc(p.get('trigram', ''))}{esc(pno)}宫 · {esc(p.get('direction', ''))}</span>
            <span class="{el_cls(p.get('element'))}">{esc(p.get('element', ''))}</span>
          </div>
        </div>""")

    anchors_html = ""
    anchors = lifelong.get("anchors") or []
    if anchors:
        rows = []
        for a in anchors:
            rel = a.get("relation") or {}
            readings = "".join(f"<li>{esc(r)}</li>" for r in (a.get("readings") or []))
            rows.append(f"""
            <div class="anchor-card">
              <div class="anchor-hd">
                <span class="anchor-title">{esc(a.get('label'))} · {esc(a.get('ganzhi'))}</span>
                <span class="tag gold">{esc(rel.get('name', ''))}</span>
                <span class="anchor-role">{esc(a.get('role', ''))}</span>
              </div>
              <div class="anchor-sum">{esc(a.get('summary', ''))}</div>
              {f'<ul class="plain-list compact">{readings}</ul>' if readings else ''}
            </div>""")
        anchors_html = f'<section class="sec">{CORNERS}{section_head("03", "三宫用神", lifelong.get("note", ""))}<div class="anchor-list">{"".join(rows)}</div></section>'

    return f"""
    <section class="sec">
      {CORNERS}
      {section_head("01", "局势总览", chart.get("datetime", ""))}
      <div class="kv-grid">{meta_html}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "洛书九宫", "上南下北 · 左东右西")}
      <div class="qm-grid">{"".join(cells)}</div>
    </section>
    {anchors_html}"""


# ─── 3. 西方占星（含 SVG 黄道星轮） ──────────────────────────────

ZODIAC_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
PLANET_SHORT = {
    "太阳": "☉", "月亮": "☽", "水星": "☿", "金星": "♀", "火星": "♂",
    "木星": "♃", "土星": "♄", "天王星": "♅", "海王星": "♆", "冥王星": "♇",
}


def _natal_wheel_svg(planets: list[dict[str, Any]]) -> str:
    cx, cy = 160, 160
    r_outer, r_sign, r_inner = 148, 120, 86
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="var(--gold-strong)" stroke-width="1.2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_sign}" fill="none" stroke="var(--gold-line)" stroke-width="1"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="none" stroke="var(--line)" stroke-width="1"/>',
        f'<circle cx="{cx}" cy="{cy}" r="28" fill="none" stroke="var(--gold-line)" stroke-width=".8"/>',
    ]
    for i in range(12):
        deg = i * 30 - 90
        rad = math.radians(deg)
        x1, y1 = cx + r_inner * math.cos(rad), cy + r_inner * math.sin(rad)
        x2, y2 = cx + r_outer * math.cos(rad), cy + r_outer * math.sin(rad)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="var(--line)" stroke-width=".8"/>')
        mid = math.radians(deg + 15)
        gx, gy = cx + ((r_outer + r_sign) / 2) * math.cos(mid), cy + ((r_outer + r_sign) / 2) * math.sin(mid)
        parts.append(f'<text x="{gx:.1f}" y="{gy + 4:.1f}" text-anchor="middle" class="wheel-sign">{ZODIAC_GLYPHS[i]}</text>')

    # 绘制行星位置（错开重叠角度）
    placed: list[float] = []
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)):
            continue
        adj = float(lon)
        for prev in placed:
            if abs((adj - prev + 180) % 360 - 180) < 9:
                adj += 9
        placed.append(adj)
        rad = math.radians(adj - 90)
        r_p = (r_sign + r_inner) / 2
        px, py = cx + r_p * math.cos(rad), cy + r_p * math.sin(rad)
        glyph = PLANET_SHORT.get(p.get("name", ""), "•")
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9.5" fill="var(--surface-solid)" stroke="var(--gold)" stroke-width="1"/>')
        parts.append(f'<text x="{px:.1f}" y="{py + 3.5:.1f}" text-anchor="middle" class="wheel-planet">{esc(glyph)}</text>')

    parts.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" class="wheel-center">星 盘</text>')
    return f'<svg class="natal-wheel" viewBox="0 0 320 320" aria-label="黄道本命星轮">{"".join(parts)}</svg>'


def render_astrology(chart: dict[str, Any]) -> str:
    sun = chart.get("sun") or {}
    moon = chart.get("moon") or {}
    rising = chart.get("rising") or {}
    mc = chart.get("mc") or {}

    big4 = [
        ("太阳 Sun", sun.get("sign"), f"{sun.get('degree_in_sign', '')}° · {sun.get('element', '')}{sun.get('mode', '')}"),
        ("月亮 Moon", moon.get("sign"), f"{moon.get('degree_in_sign', '')}° · {moon.get('element', '')}{moon.get('mode', '')}"),
        ("上升 ASC", rising.get("sign"), f"{rising.get('degree_in_sign', '')}°"),
        ("中天 MC", mc.get("sign"), f"{mc.get('degree_in_sign', '')}°"),
    ]
    big4_html = "".join(
        f'<div class="stat-box"><div class="stat-k">{esc(k)}</div>'
        f'<div class="stat-v">{esc(v or "—")}</div>'
        f'<div class="stat-s">{esc(s)}</div></div>'
        for k, v, s in big4
    )

    planets = chart.get("planets") or []
    p_rows = "".join(
        f"<tr><td><b>{esc(p.get('name'))}</b>{' <span class=\"tag accent\">逆</span>' if p.get('retrograde') else ''}</td>"
        f"<td>{esc(p.get('sign'))}</td>"
        f"<td class=\"num\">{esc(p.get('degree_in_sign'))}°</td>"
        f"<td class=\"num\">第 {esc(p.get('house'))} 宫</td></tr>"
        for p in planets
    )

    balance = chart.get("balance") or {}
    bal_parts = []
    for group_title, mapping in [("四元素分布", balance.get("elements") or {}), ("三模式分布", balance.get("modes") or {})]:
        total = sum(mapping.values()) or 1
        bars = "".join(
            f'<div class="bar-row"><span class="bar-k">{esc(k)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{round(v / total * 100)}%"></div></div>'
            f'<span class="bar-v">{esc(v)}</span></div>'
            for k, v in mapping.items()
        )
        bal_parts.append(f'<div class="bal-box"><div class="sub-hd">{group_title}</div>{bars}</div>')

    aspects = chart.get("aspects") or []
    a_rows = "".join(
        f"<tr><td>{esc(a.get('a'))}</td><td><b class=\"gold-text\">{esc(a.get('type'))}</b></td><td>{esc(a.get('b'))}</td>"
        f"<td class=\"num\">{esc(a.get('angle'))}°</td><td class=\"num\">±{esc(a.get('orb'))}°</td></tr>"
        for a in aspects
    )

    return f"""
    <section class="sec">
      {CORNERS}
      {section_head("01", "星轮与核心四轴", f"{chart.get('local_time', '')} · {chart.get('place', '')}")}
      <div class="astro-hero">
        {_natal_wheel_svg(planets)}
        <div class="stat-grid two-by-two">{big4_html}</div>
      </div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "行星落座与宫位", f"{chart.get('zodiac', '')} · {chart.get('house_system', '')}")}
      <table class="data-table">
        <thead><tr><th>星体</th><th>星座</th><th class="num">度数</th><th class="num">宫位</th></tr></thead>
        <tbody>{p_rows}</tbody>
      </table>
      <div class="bal-grid">{"".join(bal_parts)}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("03", "主要相位", f"共 {len(aspects)} 组")}
      <table class="data-table">
        <thead><tr><th>星体 A</th><th>相位</th><th>星体 B</th><th class="num">角度</th><th class="num">容许度</th></tr></thead>
        <tbody>{a_rows}</tbody>
      </table>
    </section>"""


# ─── 4 & 5. 八字合盘 / 紫微合盘（含星金环形分盘） ────────────────

def _score_ring_svg(score: int) -> str:
    pct = min(max(int(score), 0), 100)
    r = 46
    c = 2 * math.pi * r
    offset = c * (1 - pct / 100)
    return f"""<svg class="score-ring" viewBox="0 0 116 116" aria-hidden="true">
      <circle cx="58" cy="58" r="{r}" fill="none" stroke="var(--line)" stroke-width="6"/>
      <circle cx="58" cy="58" r="{r}" fill="none" stroke="var(--gold)" stroke-width="6"
        stroke-linecap="round" stroke-dasharray="{c:.1f}" stroke-dashoffset="{offset:.1f}"
        transform="rotate(-90 58 58)"/>
      <text x="58" y="63" text-anchor="middle" class="ring-num">{pct}</text>
      <text x="58" y="79" text-anchor="middle" class="ring-sub">/ 100</text>
    </svg>"""


def render_hepan(system: str, chart: dict[str, Any]) -> str:
    score = chart.get("score", 0)
    level = chart.get("level", "")
    a = chart.get("a") or {}
    b = chart.get("b") or {}

    def person_card(label: str, d: dict[str, Any]) -> str:
        if system == "bazi_hepan":
            pillars = d.get("pillars") or {}
            p_parts = []
            for k in ("year", "month", "day", "hour"):
                v = pillars.get(k)
                if isinstance(v, dict):
                    p_parts.append(f"{v.get('gan', '')}{v.get('zhi', '')}")
                elif v:
                    p_parts.append(str(v))
            p_str = " ".join(p_parts)
            rows = [
                ("性别 / 生肖", f"{d.get('gender', '')} · 属{d.get('zodiac', '')}"),
                ("公历", d.get("solar_date")),
                ("四柱", p_str),
                ("日主", f"{d.get('day_master', '')}（{d.get('day_master_element', '')}）"),
                ("夫妻宫", d.get("spouse_palace")),
            ]
        else:
            rows = [
                ("性别 / 五行局", f"{d.get('gender', '')} · {d.get('bureau', '')}"),
                ("公历", d.get("solar_date")),
                ("命宫", f"{d.get('ming_branch', '')}宫 · {'、'.join(d.get('ming_stars') or ['空宫'])}"),
                ("夫妻宫", f"{d.get('spouse_branch', '')}宫 · {'、'.join(d.get('spouse_stars') or ['空宫'])}"),
                ("身宫", f"{d.get('shen_branch', '')}宫"),
            ]
        kv = "".join(f'<div class="kv-line"><i>{esc(k)}</i><span>{esc(v)}</span></div>' for k, v in rows if v)
        return f'<div class="person-card"><div class="sub-hd">{esc(label)}</div>{kv}</div>'

    matches = chart.get("matches") or []
    effect_map = {"positive": ("呼应", "good"), "negative": ("张力", "accent"), "neutral": ("中性", "neutral")}
    m_rows = []
    for m in matches:
        eff_label, eff_cls = effect_map.get(m.get("effect", ""), (m.get("effect", ""), "neutral"))
        m_rows.append(
            f"<tr><td>{esc(m.get('scope'))}</td><td><b>{esc(m.get('kind'))}</b></td>"
            f"<td><span class=\"tag {eff_cls}\">{esc(eff_label)}</span></td>"
            f"<td>{esc(m.get('detail'))}</td></tr>"
        )

    advice = chart.get("advice") or []
    adv_html = "".join(f"<li>{esc(x)}</li>" for x in advice)
    disclaimer = chart.get("disclaimer", "")

    return f"""
    <section class="sec">
      {CORNERS}
      {section_head("01", "合盘参考分", level)}
      <div class="score-hero">
        {_score_ring_svg(score)}
        <div class="score-right">
          <div class="score-lvl">{esc(level)}</div>
          <div class="score-note">{esc(disclaimer)}</div>
        </div>
      </div>
      <div class="two-col">
        {person_card("甲方", a)}
        {person_card("乙方", b)}
      </div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "互动呼应明细", f"共 {len(matches)} 项")}
      <table class="data-table">
        <thead><tr><th>维度</th><th>关系</th><th>性质</th><th>说明</th></tr></thead>
        <tbody>{"".join(m_rows) or '<tr><td colspan="4" class="muted">无显著冲合记录</td></tr>'}</tbody>
      </table>
    </section>
    {f'<section class="sec">{CORNERS}{section_head("03", "观察要点")}<ul class="plain-list">{adv_html}</ul></section>' if advice else ''}"""


# ─── 6. 六爻纳甲 ─────────────────────────────────────────────────

def _hexagram_svg(binary: str, moving_positions: set[int] | None = None) -> str:
    moving_positions = moving_positions or set()
    rows = []
    for idx in range(5, -1, -1):
        y = (5 - idx) * 16 + 6
        bit = binary[idx] if idx < len(binary) else "1"
        pos = idx + 1
        is_m = pos in moving_positions
        cls = "yao-line moving" if is_m else "yao-line"
        if bit == "1":
            rows.append(f'<rect x="6" y="{y}" width="84" height="7" rx="1.5" class="{cls}"/>')
        else:
            rows.append(f'<rect x="6" y="{y}" width="36" height="7" rx="1.5" class="{cls}"/>')
            rows.append(f'<rect x="54" y="{y}" width="36" height="7" rx="1.5" class="{cls}"/>')
        if is_m:
            mark = "○" if bit == "1" else "×"
            rows.append(f'<text x="98" y="{y + 7}" class="yao-mark">{mark}</text>')
    return f'<svg class="hex-svg" viewBox="0 0 112 104" aria-hidden="true">{"".join(rows)}</svg>'


def render_liuyao(chart: dict[str, Any]) -> str:
    moving = set(chart.get("moving_lines") or [])
    ben = chart.get("ben_gua") or {}
    hu = chart.get("hu_gua") or {}
    bian = chart.get("bian_gua") or {}

    cards = []
    for title, g, show_m in [("本卦", ben, True), ("互卦", hu, False), ("变卦", bian, False)]:
        if not g:
            continue
        cards.append(f"""
        <div class="gua-card">
          <div class="gua-role">{title}</div>
          {_hexagram_svg(g.get('binary', '111111'), moving if show_m else set())}
          <div class="gua-name">{esc(g.get('full_name') or g.get('name'))}</div>
          <div class="gua-meta">{esc(g.get('palace', ''))}宫 · {esc(g.get('element', ''))} · {esc(g.get('stage', ''))}</div>
        </div>""")

    lines = list(reversed(ben.get("lines") or []))
    pos_names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    l_rows = []
    for ln in lines:
        pos = ln.get("position", 0)
        is_m = bool(ln.get("moving"))
        sy = ln.get("shi_ying") or ""
        l_rows.append(
            f"<tr class=\"{'row-moving' if is_m else ''}\">"
            f"<td>{esc(pos_names.get(pos, pos))}</td>"
            f"<td>{esc(ln.get('liushen'))}</td>"
            f"<td><b>{esc(ln.get('liuqin'))}</b></td>"
            f"<td class=\"num\">{esc(ln.get('gan_zhi'))} <span class=\"{el_cls(ln.get('wuxing'))}\">{esc(ln.get('wuxing'))}</span></td>"
            f"<td>{esc(ln.get('yinyang'))}{' <span class=\"tag accent\">动</span>' if is_m else ''}</td>"
            f"<td>{f'<span class=\"tag gold\">{esc(sy)}</span>' if sy else ''}</td></tr>"
        )

    q = chart.get("question")
    meta_html = "".join(
        f'<div class="kv"><i>{esc(k)}</i><b>{esc(v)}</b></div>'
        for k, v in [
            ("起卦方式", chart.get("method_name")),
            ("起卦时刻", chart.get("cast_at")),
            ("干支", f"{chart.get('year_gan_zhi', '')}年 {chart.get('month_gan_zhi', '')}月 {chart.get('day_gan_zhi', '')}日"),
            ("农历", chart.get("lunar_date")),
            ("动爻", "、".join(pos_names.get(m, str(m)) for m in sorted(moving)) or "静卦无动爻"),
        ] if v
    )

    return f"""
    {f'<div class="q-banner"><i>所问之事</i><span>{esc(q)}</span></div>' if q else ''}
    <section class="sec">
      {CORNERS}
      {section_head("01", "卦象总览", chart.get("cast_at", ""))}
      <div class="gua-grid">{"".join(cards)}</div>
      <div class="kv-grid">{meta_html}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "本卦六爻排盘", f"世在{pos_names.get(ben.get('shi_line'), '')} · 应在{pos_names.get(ben.get('ying_line'), '')}")}
      <table class="data-table">
        <thead><tr><th>爻位</th><th>六神</th><th>六亲</th><th>纳甲五行</th><th>阴阳</th><th>世应</th></tr></thead>
        <tbody>{"".join(l_rows)}</tbody>
      </table>
    </section>"""


# ─── 7. 梅花易数 ─────────────────────────────────────────────────

def render_meihua(chart: dict[str, Any]) -> str:
    ben = chart.get("ben") or {}
    hu = chart.get("hu") or {}
    bian = chart.get("bian") or {}
    ty = chart.get("ti_yong") or {}
    rel = chart.get("relation") or {}

    cards = []
    for role, g in [("本卦（起）", ben), ("互卦（中）", hu), ("变卦（终）", bian)]:
        if not g:
            continue
        cards.append(f"""
        <div class="gua-card">
          <div class="gua-role">{role}</div>
          <div class="mh-symbol">{esc(g.get('symbol', ''))}</div>
          <div class="gua-name">{esc(g.get('name', ''))}</div>
          <div class="gua-meta">上{esc(g.get('upper', ''))}（{esc(g.get('upper_element', ''))}） · 下{esc(g.get('lower', ''))}（{esc(g.get('lower_element', ''))}）</div>
          <div class="mh-yi">{esc(g.get('yixiang', ''))}</div>
        </div>""")

    ti = ty.get("ti") or {}
    yong = ty.get("yong") or {}
    q = chart.get("question")

    return f"""
    {f'<div class="q-banner"><i>所问之事</i><span>{esc(q)}</span></div>' if q else ''}
    <section class="sec">
      {CORNERS}
      {section_head("01", "三卦演变", f"动爻：{chart.get('moving_line_name', '')} · {chart.get('method_name', '')}")}
      <div class="gua-grid">{"".join(cards)}</div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "体用生克", rel.get("name", ""))}
      <div class="ty-pair">
        <div class="stat-box"><div class="stat-k">体卦（己身）</div><div class="stat-v">{esc(ti.get('trigram', ''))} · <span class="{el_cls(ti.get('element'))}">{esc(ti.get('element', ''))}</span></div><div class="stat-s">{esc(ti.get('position', ''))}</div></div>
        <div class="stat-box"><div class="stat-k">用卦（所问）</div><div class="stat-v">{esc(yong.get('trigram', ''))} · <span class="{el_cls(yong.get('element'))}">{esc(yong.get('element', ''))}</span></div><div class="stat-s">{esc(yong.get('position', ''))}</div></div>
        <div class="stat-box"><div class="stat-k">生克定性</div><div class="stat-v gold-text">{esc(rel.get('name', ''))} · {esc(rel.get('result', ''))}</div><div class="stat-s">{esc(rel.get('explain', ''))}</div></div>
      </div>
      <p class="prose">{esc(chart.get('judgement', ''))}</p>
    </section>"""


# ─── 8. 塔罗牌（双框金边牌面） ───────────────────────────────────

def render_tarot(chart: dict[str, Any]) -> str:
    cards = chart.get("cards") or []
    q = chart.get("question")
    items = []
    for idx, c in enumerate(cards, start=1):
        ori = c.get("orientation", "")
        is_rev = "逆" in str(ori)
        arc = "大阿卡纳" if c.get("arcana") == "major" else f"小阿卡纳 · {c.get('suit', '')}"
        items.append(f"""
        <div class="tarot-card{' is-rev' if is_rev else ''}">
          <div class="tarot-inner">
            <div class="tarot-pos">✦ 0{idx} · {esc(c.get('position', ''))}</div>
            <div class="tarot-emblem">{'☽' if is_rev else '☀'}</div>
            <div class="tarot-name">{esc(c.get('name', ''))}</div>
            <div class="tarot-meta">
              <span class="tag {'accent' if is_rev else 'good'}">{esc(ori)}</span>
              <span>{esc(arc)}</span>
            </div>
            <div class="tarot-kw">{esc(c.get('keywords', ''))}</div>
          </div>
        </div>""")

    return f"""
    {f'<div class="q-banner"><i>所问之事</i><span>{esc(q)}</span></div>' if q else ''}
    <section class="sec">
      {CORNERS}
      {section_head("01", f"{chart.get('spread_name', '塔罗牌阵')}", chart.get("spread_description", ""))}
      <div class="tarot-grid">{"".join(items)}</div>
    </section>"""


# ─── 9. 孔明神卦 ─────────────────────────────────────────────────

def render_kongming(chart: dict[str, Any]) -> str:
    lot = chart.get("lot") or {}
    reading = chart.get("reading") or {}
    calc = chart.get("calculation") or {}
    chars = chart.get("characters") or []
    strokes = chart.get("strokes") or []
    q = chart.get("question")

    char_boxes = "".join(
        f'<div class="km-char"><b>{esc(c)}</b><span>{esc(s)} 画</span></div>'
        for c, s in zip(chars, strokes)
    )
    kw = " · ".join(reading.get("keywords") or [])

    return f"""
    {f'<div class="q-banner"><i>所问之事</i><span>{esc(q)}</span></div>' if q else ''}
    <section class="sec">
      {CORNERS}
      {section_head("01", f"第 {lot.get('number', '')} 签 · {lot.get('fortune', '')}", f"{lot.get('hexagram', '')} · {lot.get('palace', '')}")}
      <div class="km-lot">
        <div class="km-badge">第 {esc(lot.get('number', ''))} 签 · {esc(lot.get('level', ''))}</div>
        <div class="km-poem">{esc(lot.get('poem', ''))}</div>
        <div class="km-sub">本卦 {esc(lot.get('hexagram', ''))} → 变卦 {esc(lot.get('changed', ''))} · {esc(lot.get('line', ''))}</div>
      </div>
      <div class="km-calc">
        <div class="km-chars">{char_boxes}</div>
        <div class="km-detail">{esc(calc.get('detail', ''))}</div>
      </div>
    </section>
    <section class="sec">
      {CORNERS}
      {section_head("02", "签意要点", reading.get("tone", ""))}
      {f'<div class="km-kw">关键词：{esc(kw)}</div>' if kw else ''}
      <p class="prose">{esc(reading.get('advice', ''))}</p>
      <p class="muted-note">{esc(chart.get('disclaimer', ''))}</p>
    </section>"""


# ─── 10. MBTI ────────────────────────────────────────────────────

def render_mbti(chart: dict[str, Any]) -> str:
    dims = chart.get("dimensions") or []
    dim_rows = []
    for d in dims:
        lp = int(round(d.get("left_pct", 50)))
        rp = int(round(d.get("right_pct", 50)))
        dim_rows.append(f"""
        <div class="mbti-row">
          <div class="mbti-side left{' dom' if d.get('dominant') == d.get('left') else ''}"><b>{esc(d.get('left'))}</b> {esc(d.get('left_name'))} <span class="num">{lp}%</span></div>
          <div class="mbti-bar"><div class="mbti-fill" style="width:{lp}%"></div></div>
          <div class="mbti-side right{' dom' if d.get('dominant') == d.get('right') else ''}"><span class="num">{rp}%</span> {esc(d.get('right_name'))} <b>{esc(d.get('right'))}</b></div>
        </div>""")

    strengths = "、".join(chart.get("strengths") or [])
    blinds = "、".join(chart.get("blind_spots") or [])

    return f"""
    <section class="sec">
      {CORNERS}
      {section_head("01", "性格类型画像", f"已完成 {chart.get('answered', 32)} 题")}
      <div class="mbti-hero">
        <div class="mbti-code">{esc(chart.get('type', ''))}</div>
        <div>
          <div class="mbti-name">{esc(chart.get('name', ''))}</div>
          <div class="prose">{esc(chart.get('summary', ''))}</div>
        </div>
      </div>
      <div class="mbti-dims">{"".join(dim_rows)}</div>
      <div class="kv-grid">
        <div class="kv"><i>核心优势</i><b>{esc(strengths)}</b></div>
        <div class="kv"><i>常见盲点</i><b>{esc(blinds)}</b></div>
        <div class="kv"><i>适配方向</i><b>{esc(chart.get('fit', ''))}</b></div>
      </div>
      <p class="muted-note">{esc(chart.get('disclaimer', ''))}</p>
    </section>"""


# ─── 统一玄夜星金样式 ────────────────────────────────────────────

CSS = """
:root{
  color-scheme:dark;
  --bg:#07090f;
  --bg-glow-1:rgba(214,172,96,.13);
  --bg-glow-2:rgba(76,62,148,.16);
  --bg-glow-3:rgba(36,78,128,.14);
  --surface:rgba(13,17,28,.82);
  --surface-solid:#0f1320;
  --surface-2:rgba(20,25,40,.74);
  --ink:#f3efe6; --sub:#c2baa9; --faint:#857f74;
  --gold:#e6c47e; --gold-dim:#b59150; --gold-line:rgba(224,188,118,.28); --gold-strong:rgba(224,188,118,.58);
  --line:rgba(224,188,118,.16); --line-strong:rgba(224,188,118,.38);
  --accent:#f06a5b; --accent-soft:rgba(240,106,91,.16); --accent-line:rgba(240,106,91,.55);
  --good:#52d692; --good-soft:rgba(82,214,146,.14);
  --mu:#56c98d; --huo:#f07060; --tu:#e2b660; --jin:#d3dae6; --shui:#5fb2f5;
  --font-serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC",STSong,Georgia,serif;
  --font-sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
  --font-mono:"SF Mono",ui-monospace,Menlo,Consolas,monospace;
}
[data-theme="light"]{
  color-scheme:light;
  --bg:#f4f1ea;
  --bg-glow-1:rgba(180,136,62,.08);
  --bg-glow-2:rgba(120,90,60,.04);
  --bg-glow-3:rgba(60,90,120,.04);
  --surface:rgba(255,254,250,.94);
  --surface-solid:#fffefa;
  --surface-2:#f8f5ed;
  --ink:#1f1d18; --sub:#544e43; --faint:#7d7668;
  --gold:#9e7428; --gold-dim:#8c6929; --gold-line:rgba(158,116,40,.28); --gold-strong:rgba(158,116,40,.58);
  --line:#e3dccd; --line-strong:#cbbca0;
  --accent:#b4402f; --accent-soft:#fbeae6; --accent-line:#d99a8e;
  --good:#1e7a4c; --good-soft:#e5f2ea;
  --mu:#2f7350; --huo:#b4402f; --tu:#946c2b; --jin:#5b626d; --shui:#245e8a;
}
*{box-sizing:border-box;-webkit-font-smoothing:antialiased}
html,body{margin:0;padding:0;min-height:100vh;color:var(--ink);font-family:var(--font-sans);font-size:14.5px;line-height:1.7;
  background-color:var(--bg);
  background-image:
    radial-gradient(ellipse 75% 55% at 18% 8%, var(--bg-glow-2), transparent 65%),
    radial-gradient(ellipse 60% 45% at 84% 12%, var(--bg-glow-1), transparent 62%),
    radial-gradient(ellipse 70% 50% at 50% 96%, var(--bg-glow-3), transparent 68%);
  background-attachment:fixed}
.page{max-width:980px;margin:0 auto;padding:22px 22px 56px}

.topbar{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:12px 18px;margin-bottom:22px;
  background:var(--surface);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--gold-line);border-radius:4px;position:relative}
.brand{display:flex;align-items:center;gap:12px}
.brand .emblem{width:34px;height:34px;color:var(--gold);flex:0 0 auto;animation:spin-slow 80s linear infinite}
@keyframes spin-slow{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.brand .emblem{animation:none}}
.brand-t{font-family:var(--font-serif);font-size:19px;font-weight:400;letter-spacing:.24em;color:var(--gold)}
.brand-sub{font-size:12px;color:var(--faint)}
.actions{display:flex;gap:8px}
.btn{appearance:none;border:1px solid var(--gold-line);background:rgba(224,188,118,.06);color:var(--gold);
  font-family:var(--font-sans);font-size:12.5px;height:34px;padding:0 14px;border-radius:3px;cursor:pointer;
  transition:border-color 150ms ease,background-color 150ms ease}
.btn:hover{border-color:var(--gold);background:rgba(224,188,118,.15)}

.hero{margin-bottom:20px;padding:18px 22px;background:var(--surface);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--gold-line);border-radius:4px;position:relative;overflow:hidden}
.hero h1{margin:0;font-family:var(--font-serif);font-size:28px;font-weight:400;letter-spacing:.1em;color:var(--gold);line-height:1.3}
.hero-sub{margin-top:4px;font-size:13px;color:var(--sub)}

.q-banner{display:flex;align-items:baseline;gap:12px;padding:13px 18px;margin-bottom:18px;background:var(--surface);
  border:1px solid var(--gold-strong);border-left:3px solid var(--gold);border-radius:3px}
.q-banner i{font-style:normal;font-size:12px;color:var(--gold);flex:0 0 auto}
.q-banner span{font-family:var(--font-serif);font-size:17px;color:var(--ink)}

.sec{position:relative;background:var(--surface);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1px solid var(--gold-line);border-radius:4px;padding:20px 24px;margin-bottom:18px;
  box-shadow:0 18px 46px rgba(0,0,0,.28)}
[data-theme="light"] .sec{box-shadow:0 8px 24px rgba(40,30,15,.06)}
.corner{position:absolute;width:11px;height:11px;border-color:var(--gold);border-style:solid;pointer-events:none;opacity:.75}
.corner.tl{top:-1px;left:-1px;border-width:1.5px 0 0 1.5px}
.corner.tr{top:-1px;right:-1px;border-width:1.5px 1.5px 0 0}
.corner.bl{bottom:-1px;left:-1px;border-width:0 0 1.5px 1.5px}
.corner.br{bottom:-1px;right:-1px;border-width:0 1.5px 1.5px 0}

.sec-hd{display:flex;align-items:baseline;gap:10px;padding-bottom:10px;margin-bottom:16px;border-bottom:1px solid var(--gold-line)}
.sec-num{font-family:var(--font-mono);font-size:12px;color:var(--gold)}
.sec-hd h2{margin:0;font-family:var(--font-serif);font-size:18px;font-weight:400;color:var(--ink);letter-spacing:.06em}
.sec-count{margin-left:auto;font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums}
.sub-hd{font-size:12.5px;font-weight:600;color:var(--gold-dim);margin-bottom:8px;letter-spacing:.06em}

.el-mu{color:var(--mu)}.el-huo{color:var(--huo)}.el-tu{color:var(--tu)}.el-jin{color:var(--jin)}.el-shui{color:var(--shui)}
.gold-text{color:var(--gold)}
.num{font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.muted{color:var(--faint)}
.muted-note{margin:12px 0 0;font-size:12px;color:var(--faint)}
.prose{margin:12px 0 0;color:var(--sub);line-height:1.85}

.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:2px;border:1px solid var(--line-strong);color:var(--sub);line-height:1.4}
.tag.gold{color:var(--gold);border-color:var(--gold-strong);background:rgba(230,196,126,.14)}
.tag.accent{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.tag.good{color:var(--good);border-color:rgba(82,214,146,.48);background:var(--good-soft)}

.kv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px 18px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.kv{display:flex;flex-direction:column;gap:1px}
.kv i{font-style:normal;font-size:11.5px;color:var(--gold-dim)}
.kv b{font-weight:500;font-size:13.5px;color:var(--ink);font-variant-numeric:tabular-nums}

.data-table{width:100%;border-collapse:collapse;font-size:13.5px}
.data-table th{text-align:left;font-weight:500;font-size:12px;color:var(--gold-dim);padding:9px 10px;border-bottom:1px solid var(--gold-line)}
.data-table td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.data-table tr.row-moving{background:var(--accent-soft)}
.plain-list{margin:0;padding-left:18px;color:var(--sub)}
.plain-list li{margin:5px 0}
.plain-list.compact li{margin:2px 0;font-size:13px}

/* 八字 */
.bz-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.bz-col{border:1px solid var(--gold-line);border-radius:3px;padding:16px 10px;text-align:center;background:var(--surface-2)}
.bz-col.is-day{border-color:var(--gold);background:rgba(230,196,126,.11);box-shadow:inset 0 0 24px rgba(230,196,126,.08)}
.bz-label{font-size:11.5px;color:var(--gold-dim)}
.bz-shishen{font-size:12px;color:var(--sub);margin-top:4px;min-height:18px}
.bz-gz{display:flex;flex-direction:column;align-items:center;gap:4px;margin:10px 0}
.bz-char{font-family:var(--font-serif);font-size:36px;line-height:1.12;font-weight:600}
.bz-canggan{font-size:11.5px;color:var(--faint);padding-top:8px;border-top:1px solid var(--line)}
.dy-strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:9px}
.dy-card{border:1px solid var(--line);border-radius:3px;padding:10px 8px;text-align:center;background:var(--surface-2)}
.dy-idx{font-size:11px;color:var(--gold-dim)}
.dy-gz{font-family:var(--font-serif);font-size:18px;font-weight:600;color:var(--ink);margin:3px 0}
.dy-age{font-size:11px;color:var(--faint);font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.ln-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px}
.ln-chip{border:1px solid var(--line);border-radius:3px;padding:7px 9px;display:flex;justify-content:space-between;align-items:baseline;font-size:12.5px;background:var(--surface-2)}
.ln-y{font-family:var(--font-mono);color:var(--faint)}
.ln-g{font-family:var(--font-serif);font-weight:600;color:var(--gold)}

/* 奇门 */
.qm-grid{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--gold-strong);background:var(--surface-solid)}
.qm-cell{border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:12px 13px;min-height:142px;display:flex;flex-direction:column;justify-content:space-between}
.qm-cell.is-center{background:var(--surface-2)}
.qm-cell.is-anchor{background:rgba(230,196,126,.11);box-shadow:inset 0 0 0 1.5px var(--gold-strong)}
.qm-top,.qm-stems,.qm-foot{display:flex;justify-content:space-between;align-items:center;gap:6px;font-size:11.5px}
.qm-deity{color:var(--gold);font-weight:600}
.qm-tags{display:flex;gap:4px}
.qm-mid{display:flex;justify-content:space-between;align-items:baseline;margin:10px 0;font-family:var(--font-serif)}
.qm-star{font-size:15px;font-weight:600;color:var(--ink)}
.qm-door{font-size:18px;font-weight:700;color:var(--accent)}
.qm-stems{font-family:var(--font-mono);color:var(--sub)}
.qm-foot{color:var(--faint);border-top:1px solid var(--line);padding-top:6px;margin-top:6px}
.anchor-list{display:flex;flex-direction:column;gap:12px}
.anchor-card{border:1px solid var(--gold-line);border-radius:3px;padding:13px 15px;background:var(--surface-2)}
.anchor-hd{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.anchor-title{font-family:var(--font-serif);font-size:15.5px;color:var(--gold);font-weight:600}
.anchor-role{margin-left:auto;font-size:12px;color:var(--faint)}
.anchor-sum{margin-top:6px;font-size:13.5px;color:var(--ink)}

/* 占星 & 统计 */
.astro-hero{display:grid;grid-template-columns:280px 1fr;gap:20px;align-items:center}
.natal-wheel{width:100%;max-width:280px;display:block;margin:0 auto}
.wheel-sign{font-size:13px;fill:var(--gold-dim)}
.wheel-planet{font-size:11px;fill:var(--gold);font-weight:700}
.wheel-center{font-family:var(--font-serif);font-size:12px;fill:var(--gold-dim);letter-spacing:.2em}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.stat-grid.two-by-two{grid-template-columns:repeat(2,1fr)}
.stat-box{border:1px solid var(--gold-line);border-radius:3px;padding:13px 14px;background:var(--surface-2)}
.stat-k{font-size:11.5px;color:var(--gold-dim)}
.stat-v{font-family:var(--font-serif);font-size:20px;font-weight:600;color:var(--ink);margin-top:3px}
.stat-s{font-size:12px;color:var(--sub);margin-top:2px}
.bal-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.bar-row{display:grid;grid-template-columns:46px 1fr 28px;align-items:center;gap:8px;margin:6px 0;font-size:12.5px}
.bar-track{height:6px;background:var(--line);border-radius:2px;overflow:hidden}
.bar-fill{height:100%;background:var(--gold)}
.bar-v{text-align:right;font-family:var(--font-mono);color:var(--sub)}

/* 合盘 */
.score-hero{display:flex;align-items:center;gap:24px;padding-bottom:18px;margin-bottom:18px;border-bottom:1px solid var(--line)}
.score-ring{width:116px;height:116px;flex:0 0 auto}
.ring-num{font-family:var(--font-serif);font-size:30px;font-weight:600;fill:var(--gold)}
.ring-sub{font-family:var(--font-mono);font-size:10px;fill:var(--faint)}
.score-right{flex:1}
.score-lvl{font-family:var(--font-serif);font-size:22px;color:var(--gold);font-weight:400;letter-spacing:.08em}
.score-note{font-size:12.5px;color:var(--sub);margin-top:6px}
.two-col{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.person-card{border:1px solid var(--gold-line);border-radius:3px;padding:13px 15px;background:var(--surface-2)}
.kv-line{display:flex;justify-content:space-between;gap:10px;padding:5px 0;border-bottom:1px solid var(--line);font-size:13px}
.kv-line:last-child{border-bottom:none}
.kv-line i{font-style:normal;color:var(--faint)}

/* 六爻 & 梅花 */
.gua-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.gua-card{border:1px solid var(--gold-line);border-radius:3px;padding:16px 12px;text-align:center;background:var(--surface-2)}
.gua-role{font-size:11.5px;color:var(--gold-dim);margin-bottom:8px;letter-spacing:.08em}
.hex-svg{width:112px;height:104px;display:block;margin:0 auto 8px}
.yao-line{fill:var(--gold)}
.yao-line.moving{fill:var(--accent)}
.yao-mark{font-size:11px;fill:var(--accent);font-weight:700}
.gua-name{font-family:var(--font-serif);font-size:18px;color:var(--ink);font-weight:600}
.gua-meta{font-size:12px;color:var(--faint);margin-top:3px}
.mh-symbol{font-size:44px;line-height:1.1;margin:6px 0;color:var(--gold)}
.mh-yi{font-size:12px;color:var(--sub);margin-top:6px}
.ty-pair{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}

/* 塔罗 */
.tarot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.tarot-card{border:1px solid var(--gold-strong);border-radius:4px;padding:7px;background:var(--surface-2)}
.tarot-card.is-rev{border-color:var(--accent-line)}
.tarot-inner{border:1px solid var(--gold-line);border-radius:2px;padding:18px 14px;height:100%;display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px}
.tarot-pos{font-family:var(--font-mono);font-size:11px;color:var(--gold-dim);letter-spacing:.08em}
.tarot-emblem{font-size:28px;color:var(--gold);line-height:1}
.tarot-name{font-family:var(--font-serif);font-size:21px;color:var(--gold);font-weight:600}
.tarot-meta{display:flex;align-items:center;justify-content:center;gap:8px;font-size:12px;color:var(--faint)}
.tarot-kw{font-size:13px;color:var(--sub);padding-top:10px;border-top:1px solid var(--line);width:100%}

/* 孔明 */
.km-lot{border:1px solid var(--gold-strong);background:radial-gradient(circle at 50% 35%, rgba(230,196,126,.13), transparent 72%);border-radius:3px;padding:24px 20px;text-align:center}
.km-badge{display:inline-block;font-size:11.5px;color:var(--gold);border:1px solid var(--gold-line);padding:2px 12px;border-radius:2px;margin-bottom:12px;letter-spacing:.12em}
.km-poem{font-family:var(--font-serif);font-size:24px;line-height:1.85;letter-spacing:.14em;color:var(--ink)}
.km-sub{margin-top:10px;font-size:12.5px;color:var(--sub)}
.km-calc{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.km-chars{display:flex;gap:10px}
.km-char{border:1px solid var(--gold-line);border-radius:3px;padding:6px 14px;text-align:center;background:var(--surface-2)}
.km-char b{display:block;font-family:var(--font-serif);font-size:21px;color:var(--gold)}
.km-char span{font-size:11px;color:var(--faint);font-family:var(--font-mono)}
.km-detail{font-size:12.5px;color:var(--sub);font-family:var(--font-mono)}
.km-kw{font-size:13px;color:var(--gold);font-weight:500}

/* MBTI */
.mbti-hero{display:flex;align-items:center;gap:20px;padding-bottom:18px;margin-bottom:18px;border-bottom:1px solid var(--line)}
.mbti-code{font-family:var(--font-mono);font-size:38px;font-weight:700;letter-spacing:.1em;color:var(--gold);padding:8px 16px;border:1px solid var(--gold-strong);background:rgba(230,196,126,.12);border-radius:3px}
.mbti-name{font-family:var(--font-serif);font-size:22px;color:var(--ink);font-weight:600}
.mbti-dims{display:flex;flex-direction:column;gap:14px}
.mbti-row{display:grid;grid-template-columns:136px 1fr 136px;align-items:center;gap:12px;font-size:13px}
.mbti-side{color:var(--faint)}
.mbti-side.right{text-align:right}
.mbti-side.dom{color:var(--gold);font-weight:600}
.mbti-bar{height:8px;background:var(--line);border-radius:2px;overflow:hidden}
.mbti-fill{height:100%;background:var(--gold)}

.warnings{border:1px solid var(--gold-line);background:var(--surface-2);border-radius:3px;padding:10px 14px;margin-bottom:16px;font-size:12.5px;color:var(--sub)}
.warnings div{margin:2px 0}
.ft{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--faint)}

@media (max-width:740px){
  .page{padding:14px 12px 36px}
  .sec{padding:14px 14px}
  .astro-hero{grid-template-columns:1fr}
  .bz-grid,.stat-grid{grid-template-columns:repeat(2,1fr)}
  .two-col,.bal-grid,.gua-grid,.ty-pair{grid-template-columns:1fr}
  .mbti-row{grid-template-columns:1fr;gap:4px}
  .mbti-side.right{text-align:left}
  .score-hero,.mbti-hero{flex-direction:column;align-items:flex-start}
}
@media print{
  html,body{background:#fff!important;color:#1f1d18!important}
  .topbar{display:none!important}
  .page{max-width:none;padding:0}
  .sec,.hero{box-shadow:none!important;background:#fff!important;border:1px solid #ccc!important;backdrop-filter:none;break-inside:avoid}
  @page{size:A4 portrait;margin:10mm}
}
"""

SCRIPT = """
(function(){
  const root = document.documentElement;
  const themeBtn = document.getElementById('theme-toggle');
  const printBtn = document.getElementById('print-btn');
  const setTheme = (t) => {
    root.dataset.theme = t;
    if (themeBtn) themeBtn.textContent = t === 'light' ? '玄夜星金' : '宣纸印本';
  };
  setTheme('dark');
  if (themeBtn) themeBtn.addEventListener('click', () => setTheme(root.dataset.theme === 'light' ? 'dark' : 'light'));
  if (printBtn) printBtn.addEventListener('click', () => window.print());
})();
"""


def render_envelope_html(envelope: ChartEnvelope, *, title: str = "未命名") -> str:
    """将任意体系的 ChartEnvelope 渲染为玄夜星金单文件 HTML 报告。"""
    system = envelope.system
    chart = envelope.chart if isinstance(envelope.chart, dict) else {}
    sys_title, sys_sub = SYSTEM_TITLES.get(system, (system, "本地推演排盘"))

    if system == "bazi":
        body = render_bazi(chart)
    elif system == "qimen":
        body = render_qimen(chart)
    elif system == "astrology":
        body = render_astrology(chart)
    elif system in ("bazi_hepan", "ziwei_hepan"):
        body = render_hepan(system, chart)
    elif system == "liuyao":
        body = render_liuyao(chart)
    elif system == "meihua":
        body = render_meihua(chart)
    elif system == "tarot":
        body = render_tarot(chart)
    elif system == "kongming":
        body = render_kongming(chart)
    elif system == "mbti":
        body = render_mbti(chart)
    else:
        body = f'<section class="sec">{CORNERS}<pre>{esc(envelope.text)}</pre></section>'

    warn_html = ""
    if envelope.warnings:
        items = "".join(f"<div>· {esc(w)}</div>" for w in envelope.warnings)
        warn_html = f'<div class="warnings">{items}</div>'

    return f"""<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {esc(sys_title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
  <header class="topbar">
    <div class="brand">
      {ASTROLABE_EMBLEM}
      <div>
        <div class="brand-t">玄机 · {esc(sys_title)}</div>
        <div class="brand-sub">{esc(sys_sub)} · 本地推演</div>
      </div>
    </div>
    <div class="actions">
      <button type="button" class="btn" id="theme-toggle">宣纸印本</button>
      <button type="button" class="btn" id="print-btn">打印 / 存 PDF</button>
    </div>
  </header>

  <div class="hero">
    {CORNERS}
    <h1>{esc(title)} · {esc(sys_title)}</h1>
    <div class="hero-sub">{esc(sys_sub)}</div>
  </div>

  {warn_html}
  {body}

  <footer class="ft">
    <span>由玄机本地引擎推演生成，未联网、未上传任何数据；命理为观察框架，重大决定以本人与专业意见为准。</span>
    <span class="num">{esc(system)} · v{esc(envelope.engine_version)}</span>
  </footer>
</div>
<script>{SCRIPT}</script>
</body>
</html>"""
