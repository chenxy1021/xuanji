#!/usr/bin/env node
/**
 * 紫微斗数排盘 CLI —— 生成「传统专业版式」命盘 HTML + 结构化 JSON
 *
 * 用法示例：
 *   node paipan.mjs --name 张三 --gender male --solar 1994-10-21 --time 08:45 --city 九江
 *   node paipan.mjs --gender female --solar 1990-3-8 --shichen 卯 --longitude 113.2
 *   node paipan.mjs --gender male --lunar 1994-9-17 --time 08:45 --leap-policy split
 *
 * 输出：<out>/<姓名>-<日期>-紫微命盘.html 与同名 .json（供后续解读使用）
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  generateChart,
  setBrightnessSchool,
  detectPatterns,
  getMingGongSummary,
  BRANCHES,
  STEMS,
  SHICHEN,
  JU_NAMES,
  SI_HUA_TABLE,
  SCHOOL_AX,
  boshiShenName,
  suiQianShenName,
  jiangQianShenName,
  boshiReverse,
  calculateTrueSolarTime,
  resolveZiweiDayOffset,
  shiftGregorianDate,
  formatTrueSolarClock,
  formatSignedMinutes,
  isValidGregorianDate,
  PROVINCES,
  Lunar,
} from './chart-core.mjs';
import { renderChart } from './render.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ─── 常量 ───────────────────────────────────────────────────────
const CHANGSHENG = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养'];
/** 长生起点（0 基地支）：水二局申、木三局亥、金四局巳、土五局申、火六局寅 */
const CS_START = { 2: 8, 3: 11, 4: 5, 5: 8, 6: 2 };
const SCHOOLS = ['QS', 'XD1', 'ZZ', 'XD2'];
const LEAP_POLICIES = ['split', 'next-month', 'prev-month', 'origin-month'];

// ─── 参数解析 ───────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { out._.push(a); continue; }
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) { out[key] = true; }
    else { out[key] = next; i++; }
  }
  return out;
}

const USAGE = `紫微斗数排盘（ziwei-paipan）

必填：
  --gender male|female|男|女     性别
  --solar YYYY-MM-DD            公历生日（与 --lunar 二选一）
  --lunar YYYY-M-D              农历生日（配 --leap 表示闰月）
  --time HH:MM                  出生钟表时间（24 小时制，与 --shichen 二选一）
  --shichen 子|丑|…|亥          已知时辰（不做真太阳时校正）

可选：
  --name 姓名                   中宫标题
  --city 城市                   自动查经度做真太阳时校正（如 九江、杭州）
  --longitude 116.0             直接给经度（优先于 --city）
  --leap                        农历闰月（配合 --lunar）
  --leap-policy split|next-month|prev-month|origin-month   闰月归属，默认 split
  --school QS|XD1|ZZ|XD2        星曜亮度流派，默认 QS（斗数全书）
  --year 2026                   流年（默认当前年），用于「今年怎么样」类问题
  --out 目录                    输出目录，默认 ./ziwei-charts
  --json-only                   只输出 JSON，不生成 HTML
  --quiet                       只打印文件路径

示例：
  node paipan.mjs --name 张三 --gender male --solar 1994-10-21 --time 08:45 --city 九江
`;

// ─── 城市经度查找 ────────────────────────────────────────────────
function findLongitude(cityName) {
  if (!cityName) return null;
  const target = String(cityName).trim();
  const all = [];
  for (const p of PROVINCES) {
    for (const c of p.cities) all.push({ ...c, province: p.name });
  }
  const exact = all.find((c) => c.name === target);
  if (exact) return exact;
  const strip = (s) => s.replace(/[市省区县]/g, '');
  const t = strip(target);
  return all.find((c) => strip(c.name) === t)
    ?? all.find((c) => c.name.includes(t) && t.length >= 2)
    ?? null;
}

// ─── 十二神 / 长生 / 小限 ────────────────────────────────────────
function changshengByBranch(ju, yearStem, gender) {
  const start = CS_START[ju] ?? 8;
  const reverse = boshiReverse(yearStem, gender);
  const out = new Array(12).fill('');
  for (let i = 0; i < 12; i++) {
    const b = ((reverse ? start - i : start + i) % 12 + 12) % 12;
    out[b] = CHANGSHENG[i];
  }
  return out;
}

function xiaoxianByBranch(yearBranch, gender) {
  const start = (SCHOOL_AX.XIAOXIAN[yearBranch + 1] ?? 12) - 1; // 子起一 → 0 基
  const dir = gender === 'male' ? 1 : -1;
  const out = Array.from({ length: 12 }, () => []);
  for (let age = 1; age <= 96; age++) {
    const b = ((start + dir * (age - 1)) % 12 + 12) % 12;
    out[b].push(age);
  }
  return out;
}

// ─── 主流程 ─────────────────────────────────────────────────────
function fail(msg) {
  console.error(`✗ ${msg}`);
  process.exit(1);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h) { console.log(USAGE); return; }

  // 性别
  const gRaw = String(args.gender ?? '');
  const gender = ['male', '男', 'm', 'M'].includes(gRaw) ? 'male'
    : ['female', '女', 'f', 'F'].includes(gRaw) ? 'female' : null;
  if (!gender) fail('请用 --gender male|female 指明性别（排盘必需，男女大限顺逆不同）');

  // 生日：公历优先
  let solarDate = null;
  if (typeof args.solar === 'string') {
    const m = args.solar.trim().match(/^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$/);
    if (!m) fail(`公历日期格式不对：${args.solar}（应为 YYYY-MM-DD）`);
    solarDate = { year: +m[1], month: +m[2], day: +m[3] };
  } else if (typeof args.lunar === 'string') {
    const m = args.lunar.trim().match(/^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$/);
    if (!m) fail(`农历日期格式不对：${args.lunar}（应为 YYYY-M-D）`);
    const ly = +m[1], lm = +m[2], ld = +m[3];
    const lunarMonth = args.leap ? -lm : lm;
    const s = Lunar.fromYmdHms(ly, lunarMonth, ld, 12, 0, 0).getSolar();
    solarDate = { year: s.getYear(), month: s.getMonth(), day: s.getDay() };
  } else {
    fail('缺少生日：--solar YYYY-MM-DD 或 --lunar YYYY-M-D');
  }
  if (!isValidGregorianDate(solarDate.year, solarDate.month, solarDate.day)) {
    fail(`这个日期不存在：${solarDate.year}-${solarDate.month}-${solarDate.day}（查一下是不是记错了）`);
  }

  // 时辰：--shichen 直接给支；--time 走真太阳时
  let branch;
  let clockText = '';
  let trueSolarText = '';
  let longitudeNote = '';
  let birthplace = '';
  let dayOffset = 0;

  if (typeof args.shichen === 'string') {
    const raw = args.shichen.trim().replace(/时$/, '');
    const idx = BRANCHES.indexOf(raw.charAt(0));
    if (idx < 0) fail(`时辰不认识：${args.shichen}（用 子丑寅卯辰巳午未申酉戌亥）`);
    branch = idx;
    const r = SHICHEN[idx].range;
    clockText = `${raw}时（${r}）`;
    trueSolarText = clockText;
  } else {
    const t = String(args.time ?? '');
    const m = t.trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!m) fail('缺少出生时间：--time 08:45（24 小时制）或 --shichen 辰');
    const hh = +m[1], mm = +m[2];
    if (hh > 23 || mm > 59) fail(`时间不合法：${t}`);

    let longitude;
    if (args.longitude !== undefined && args.longitude !== true) {
      longitude = Number(args.longitude);
      if (!Number.isFinite(longitude)) fail(`经度不合法：${args.longitude}`);
      birthplace = args.city ? String(args.city) : `东经 ${longitude}°`;
    } else if (typeof args.city === 'string') {
      const hit = findLongitude(args.city);
      if (!hit) fail(`城市库里没有「${args.city}」。可以直接给 --longitude（如 116.0），或改用 --shichen 指定时辰`);
      longitude = hit.longitude;
      birthplace = args.city;
    }

    const tst = calculateTrueSolarTime({
      year: solarDate.year, month: solarDate.month, day: solarDate.day,
      clockHour: hh, clockMinute: mm, longitude,
    });
    branch = tst.branch;
    dayOffset = resolveZiweiDayOffset(tst);
    clockText = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
    trueSolarText = longitude === undefined
      ? `${formatTrueSolarClock(tst)}（未做真太阳时校正）`
      : `${formatTrueSolarClock(tst)}`;
    if (longitude !== undefined) {
      longitudeNote = `经度 ${formatSignedMinutes(tst.longitudeCorrectionMinutes)} 分 · 均时差 ${formatSignedMinutes(tst.equationOfTimeMinutes)} 分`;
    }
  }

  // 晚子时换日
  const chartDate = shiftGregorianDate(solarDate, dayOffset);
  const name = typeof args.name === 'string' ? args.name.trim() : '';

  // 亮度流派
  const school = String(args.school ?? 'QS').toUpperCase();
  if (!SCHOOLS.includes(school)) fail(`流派只能是 ${SCHOOLS.join('/')}`);
  setBrightnessSchool(school);

  const leapPolicy = String(args['leap-policy'] ?? 'split');
  if (!LEAP_POLICIES.includes(leapPolicy)) fail(`闰月归属只能是 ${LEAP_POLICIES.join('/')}`);

  let chart;
  try {
    chart = generateChart({
      year: chartDate.year, month: chartDate.month, day: chartDate.day,
      hour: branch, gender, name,
      city: birthplace || undefined,
    }, { leapMonth: leapPolicy });
  } catch (e) {
    fail(`排盘失败：${e.message}`);
  }

  // 十二神 / 长生 / 小限
  const yearStem = chart.lunarInfo.yearStem;
  const yearBranch = chart.lunarInfo.yearBranch;
  const cs = changshengByBranch(chart.wuxingJu, yearStem, gender);
  const xx = xiaoxianByBranch(yearBranch, gender);
  const shen = {};
  for (let b = 0; b < 12; b++) {
    shen[b] = {
      changsheng: cs[b],
      boshi: boshiShenName(yearStem, gender, b),
      suiqian: suiQianShenName(yearBranch, b),
      jiangqian: jiangQianShenName(yearBranch, b),
    };
  }

  const meta = {
    shen,
    xiaoxian: xx,
    trueSolarText,
    clockText,
    birthplace,
    longitudeNote,
  };

  // ── 流年（用户问「今年怎么样」时的唯一依据，不靠模型猜）──
  const targetYear = Number.isInteger(Number(args.year)) && args.year !== true
    ? Number(args.year)
    : new Date().getFullYear();
  const lyStem = ((targetYear - 4) % 10 + 10) % 10;
  const lyBranch = ((targetYear - 4) % 12 + 12) % 12;
  const lyPalace = chart.palaces.find((p) => p.branch === lyBranch);
  const lySihuaNames = SI_HUA_TABLE[lyStem] ?? [];
  const lySihua = ['禄', '权', '科', '忌'].map((hua, i) => {
    const star = lySihuaNames[i];
    if (!star) return null;
    const host = chart.palaces.find((p) => p.stars.some((st) => st.name === star));
    return { hua, star, palace: host ? host.name : null, branch: host ? BRANCHES[host.branch] : null };
  }).filter(Boolean);
  const liunian = {
    year: targetYear,
    ganZhi: `${STEMS[lyStem]}${BRANCHES[lyBranch]}`,
    branch: BRANCHES[lyBranch],
    palace: lyPalace ? lyPalace.name : null,
    palaceStars: lyPalace ? lyPalace.stars.filter((st) => st.type === 'major').map((st) => st.name) : [],
    siHua: lySihua,
    nominalAge: targetYear - solarDate.year + 1,
  };

  // 结构化结果（供解读使用）
  const patterns = detectPatterns(chart);
  const summary = getMingGongSummary(chart);
  const result = {
    input: {
      name, gender: gender === 'male' ? '男' : '女',
      solarDate, chartDate, hourBranch: branch,
      shichen: BRANCHES[branch] + '时', clockText, trueSolarText,
      birthplace, longitudeNote, brightnessSchool: school, leapMonthPolicy: leapPolicy,
      lateZiShifted: dayOffset !== 0,
    },
    lunar: {
      text: `${chart.lunarInfo.lunarYear}年${chart.lunarInfo.isLeapMonth ? '闰' : ''}${chart.lunarInfo.lunarMonth}月${chart.lunarInfo.lunarDay}日`,
      yearGanZhi: `${STEMS[yearStem]}${BRANCHES[yearBranch]}`,
      fourPillars: chart.lunarInfo.fourPillars,
      fourPillarsLunar: chart.lunarInfo.fourPillarsLunar,
    },
    core: {
      yinYangGender: chart.yinYangGender,
      wuxingJu: chart.wuxingJuName,
      mingGong: BRANCHES[chart.mingGongBranch],
      shenGong: BRANCHES[chart.shenGongBranch],
      mingZhu: chart.mingZhu,
      shenZhu: chart.shenZhu,
      ziweiPos: BRANCHES[chart.ziweiPos],
      currentAge: chart.currentAge,
      currentDaXian: chart.currentDaXianIndex >= 0 ? chart.daXians[chart.currentDaXianIndex] : null,
      mingKeywords: summary.keywords,
      mingNature: summary.nature,
    },
    liunian,
    daXians: chart.daXians.map((d) => ({
      range: `${d.startAge}-${d.endAge}`,
      palace: d.palaceName,
      branch: BRANCHES[d.palaceBranch],
      current: chart.currentDaXianIndex >= 0 && chart.daXians[chart.currentDaXianIndex] === d,
    })),
    palaces: chart.palaces
      .slice()
      .sort((a, b) => a.branch - b.branch)
      .map((p) => ({
        branch: BRANCHES[p.branch],
        ganzhi: `${STEMS[p.stem]}${BRANCHES[p.branch]}`,
        name: p.name,
        isMing: p.isMingGong,
        isShen: p.isShenGong,
        empty: p.isEmpty,
        borrowFrom: p.borrowedFromName ?? null,
        borrowStars: p.borrowedStars ?? null,
        daXian: p.daXianAge ? `${p.daXianAge[0]}-${p.daXianAge[1]}` : null,
        xiaoXian: xx[p.branch],
        shier: shen[p.branch],
        stars: p.stars.map((s) => ({
          name: s.name,
          type: s.type,
          brightness: s.brightnessRaw ?? null,
          siHua: s.siHua ?? null,
        })),
      })),
    patterns: patterns.map((p) => ({
      name: p.name,
      level: p.level,
      palaces: p.palaces,
      description: p.description,
      conditions: p.conditions ?? null,
      source: p.source ?? null,
    })),
  };

  // 输出
  const outDir = path.resolve(typeof args.out === 'string' ? args.out : 'ziwei-charts');
  fs.mkdirSync(outDir, { recursive: true });

  const safeName = (name || '命盘').replace(/[\\/:*?"<>|]/g, '').replace(/\.+$/, '').replace(/\.{2,}/g, '.');
  const stamp = `${solarDate.year}${String(solarDate.month).padStart(2, '0')}${String(solarDate.day).padStart(2, '0')}`;
  const base = `${safeName}-${stamp}-紫微命盘`;

  const jsonPath = path.join(outDir, `${base}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf8');

  let htmlPath = null;
  if (!args['json-only']) {
    const html = renderChart({
      chart,
      meta,
      liunian,
      patterns: result.patterns,
      title: name || '紫微斗数命盘',
      footerNote: `${solarDate.year}-${solarDate.month}-${solarDate.day} ${BRANCHES[branch]}时 · 由 ziwei-paipan 本地推演，未联网`,
    });
    htmlPath = path.join(outDir, `${base}.html`);
    fs.writeFileSync(htmlPath, html, 'utf8');
  }

  if (args.quiet) {
    console.log(htmlPath ?? jsonPath);
    return;
  }

  // 终端摘要（模型据此判断是否成功）
  const lines = [];
  lines.push(`✓ 排盘完成：${name || '（未填姓名）'} · ${gender === 'male' ? '男' : '女'} · ${result.lunar.text} · ${BRANCHES[branch]}时`);
  lines.push(`  四柱（节气） ${(result.lunar.fourPillars || []).join(' ')}    非节气 ${(result.lunar.fourPillarsLunar || []).join(' ')}`);
  lines.push(`  ${result.core.yinYangGender} · ${result.core.wuxingJu} · 命宫${result.core.mingGong} · 身宫${result.core.shenGong} · 命主${result.core.mingZhu} · 身主${result.core.shenZhu} · 虚岁${result.core.currentAge}`);
  if (result.input.lateZiShifted) lines.push('  注：出生时间落在晚子时，已按「子时换日」归到次日排盘');
  lines.push('  十二宫：');
  for (const p of result.palaces) {
    const stars = p.stars.map((s) => `${s.name}${s.brightness ?? ''}${s.siHua ? `[${s.siHua}]` : ''}`).join(' ');
    lines.push(`   ${p.ganzhi} ${p.name}${p.isMing ? '(命)' : ''}${p.isShen ? '(身)' : ''}${p.empty ? '(空宫)' : ''}${p.daXian ? ` ${p.daXian}岁` : ''}：${stars}`);
  }
  if (patterns.length) {
    lines.push(`  识别到的格局（${patterns.length}）：`);
    for (const p of patterns) lines.push(`   · ${p.name}（${p.level}）${p.palaces.join('/')}`);
  } else {
    lines.push('  识别到的格局：无（普通盘，按主星+三方四正直接论）');
  }
  lines.push('');
  if (htmlPath) lines.push(`HTML：${htmlPath}`);
  lines.push(`JSON：${jsonPath}`);
  console.log(lines.join('\n'));
}

main();
