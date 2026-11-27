#!/usr/bin/env node
/**
 * 技能自检（可复跑）：
 *   node scripts/selftest.mjs
 *
 * 覆盖：
 *   1. 金标准盘逐宫比对（1994-10-21 08:45 男 九江 —— 与开源仓库探针、用户提供的金标准盘一致）
 *   2. 晚子时换日
 *   3. 闰月两种归属产生不同的盘
 *   4. 非法日期 / 缺参数 / 城市不存在 → 非零退出并给中文原因
 *   5. 同输入两次运行结果一致（确定性）
 *   6. 空宫借对宫
 *   7. 农历输入与对应公历输入得到同一张盘
 *   8. 文档契约对齐：references 里写到的 JSON 字段，实际输出里必须真的存在
 *
 * 退出码：0 全通过 / 1 有失败。
 */

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.join(HERE, 'paipan.mjs');
const REFS = path.join(HERE, '..', 'references');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'ziwei-selftest-'));

let pass = 0;
let fail = 0;
const failures = [];

function ok(name, cond, detail = '') {
  if (cond) { pass++; return true; }
  fail++;
  failures.push(`${name}${detail ? ` —— ${detail}` : ''}`);
  return false;
}

function eq(name, actual, expected) {
  return ok(name, actual === expected, `期望 ${JSON.stringify(expected)}，实际 ${JSON.stringify(actual)}`);
}

/** 跑 CLI，返回 { code, stdout, stderr, json } */
function run(args, outDir) {
  const full = [...args, '--out', outDir, '--json-only'];
  try {
    const stdout = execFileSync(process.execPath, [CLI, ...full], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const files = fs.readdirSync(outDir).filter((f) => f.endsWith('.json'));
    const json = files.length ? JSON.parse(fs.readFileSync(path.join(outDir, files[files.length - 1]), 'utf8')) : null;
    return { code: 0, stdout, stderr: '', json };
  } catch (e) {
    return { code: e.status ?? -1, stdout: e.stdout ?? '', stderr: (e.stderr ?? '') + (e.stdout ?? ''), json: null };
  }
}

const palaceOf = (json, branch) => json.palaces.find((p) => p.branch === branch);
const majorNames = (p) => p.stars.filter((s) => s.type === 'major').map((s) => s.name).sort();
const siHuaAt = (json) => {
  const out = {};
  for (const p of json.palaces) {
    for (const s of p.stars) if (s.siHua) out[`${s.name}${s.siHua}`] = p.branch;
  }
  return out;
};

// ─── 1. 金标准盘 ────────────────────────────────────────────────
{
  const dir = path.join(TMP, 'gold');
  fs.mkdirSync(dir);
  const r = run(['--name', '金标准', '--gender', 'male', '--solar', '1994-10-21', '--time', '08:45', '--city', '九江'], dir);
  ok('金标准盘：命令成功', r.code === 0, r.stderr.trim());
  const j = r.json;
  if (j) {
    eq('金标准盘：五行局', j.core.wuxingJu, '土五局');
    eq('金标准盘：阴阳男女', j.core.yinYangGender, '阳男');
    eq('金标准盘：命宫', j.core.mingGong, '午');
    eq('金标准盘：身宫', j.core.shenGong, '寅');
    eq('金标准盘：命主', j.core.mingZhu, '破军');
    eq('金标准盘：身主', j.core.shenZhu, '文昌');
    eq('金标准盘：农历', j.lunar.text, '1994年9月17日');
    eq('金标准盘：节气四柱', (j.lunar.fourPillars || []).join(''), '甲戌甲戌庚辰庚辰');

    // 十二宫名（与金标准盘一致）
    const nameExpect = { 午: '命宫', 巳: '兄弟', 辰: '夫妻', 卯: '子女', 寅: '财帛', 丑: '疾厄', 子: '迁移', 亥: '仆役', 戌: '官禄', 酉: '田宅', 申: '福德', 未: '父母' };
    for (const [b, n] of Object.entries(nameExpect)) {
      eq(`金标准盘：${b}宫宫名`, palaceOf(j, b)?.name, n);
    }

    // 主星分布
    const majorExpect = {
      午: ['廉贞', '天相'], 巳: ['巨门'], 辰: ['贪狼'], 卯: ['太阴'], 寅: ['天府', '紫微'], 丑: ['天机'],
      子: ['破军'], 亥: ['太阳'], 戌: ['武曲'], 酉: ['天同'], 申: ['七杀'], 未: ['天梁'],
    };
    for (const [b, names] of Object.entries(majorExpect)) {
      eq(`金标准盘：${b}宫主星`, JSON.stringify(majorNames(palaceOf(j, b))), JSON.stringify([...names].sort()));
    }

    // 生年四化落宫
    const canon = (o) => JSON.stringify(Object.keys(o).sort().map((k) => [k, o[k]]));
    eq('金标准盘：四化落宫', canon(siHuaAt(j)), canon({
      廉贞禄: '午', 破军权: '子', 武曲科: '戌', 太阳忌: '亥',
    }));

    eq('金标准盘：命宫大限', palaceOf(j, '午')?.daXian, '5-14');
    eq('金标准盘：真太阳时（经度校正后）', j.input.trueSolarText, '08:44');
    ok('金标准盘：识别到格局', Array.isArray(j.patterns) && j.patterns.length > 0, `patterns=${j.patterns?.length}`);
  }
}

// ─── 2. 晚子时换日 ──────────────────────────────────────────────
{
  const dir = path.join(TMP, 'latezi');
  fs.mkdirSync(dir);
  const r = run(['--gender', 'female', '--solar', '1988-7-28', '--time', '23:20', '--city', '杭州'], dir);
  ok('晚子时：命令成功', r.code === 0, r.stderr.trim());
  if (r.json) {
    eq('晚子时：标记已换日', r.json.input.lateZiShifted, true);
    eq('晚子时：排盘日进到次日', `${r.json.input.chartDate.month}-${r.json.input.chartDate.day}`, '7-29');
    eq('晚子时：时辰仍为子', r.json.input.shichen, '子时');
  }
}

// ─── 3. 闰月两种归属 ────────────────────────────────────────────
{
  const dirA = path.join(TMP, 'leapA');
  const dirB = path.join(TMP, 'leapB');
  fs.mkdirSync(dirA); fs.mkdirSync(dirB);
  const a = run(['--gender', 'male', '--lunar', '2020-4-8', '--leap', '--shichen', '午', '--leap-policy', 'split'], dirA);
  const b = run(['--gender', 'male', '--lunar', '2020-4-8', '--leap', '--shichen', '午', '--leap-policy', 'next-month'], dirB);
  ok('闰月：两种归属都成功', a.code === 0 && b.code === 0, a.stderr || b.stderr);
  if (a.json && b.json) {
    ok('闰月：split 与 next-month 排出不同的盘', a.json.core.mingGong !== b.json.core.mingGong,
      `split=${a.json.core.mingGong} next=${b.json.core.mingGong}`);
  }
}

// ─── 4. 错误输入 ────────────────────────────────────────────────
{
  const dir = path.join(TMP, 'err');
  fs.mkdirSync(dir);
  const bad = run(['--gender', 'male', '--solar', '2023-2-30', '--time', '10:00'], dir);
  ok('非法日期：非零退出', bad.code === 1, `code=${bad.code}`);
  ok('非法日期：给出中文原因', bad.stderr.includes('不存在'), bad.stderr.trim().slice(0, 80));

  const noGender = run(['--solar', '1990-1-1', '--time', '10:00'], dir);
  ok('缺性别：非零退出并提示', noGender.code === 1 && noGender.stderr.includes('性别'), noGender.stderr.trim().slice(0, 80));

  const badCity = run(['--gender', 'male', '--solar', '1990-1-1', '--time', '10:00', '--city', '火星市'], dir);
  ok('城市不存在：非零退出并给替代方案', badCity.code === 1 && badCity.stderr.includes('longitude'), badCity.stderr.trim().slice(0, 80));
}

// ─── 5. 确定性 ──────────────────────────────────────────────────
{
  const d1 = path.join(TMP, 'det1');
  const d2 = path.join(TMP, 'det2');
  fs.mkdirSync(d1); fs.mkdirSync(d2);
  const args = ['--gender', 'male', '--solar', '1979-3-15', '--time', '06:30', '--city', '西安'];
  const a = run(args, d1);
  const b = run(args, d2);
  ok('确定性：两次都成功', a.code === 0 && b.code === 0, a.stderr || b.stderr);
  if (a.json && b.json) {
    const stable = (j) => JSON.stringify({ core: j.core, palaces: j.palaces, patterns: j.patterns });
    ok('确定性：两次盘面完全一致', stable(a.json) === stable(b.json));
  }
}

// ─── 6. 空宫借对宫 ──────────────────────────────────────────────
{
  const dir = path.join(TMP, 'empty');
  fs.mkdirSync(dir);
  const r = run(['--gender', 'female', '--solar', '1988-7-28', '--time', '23:20', '--city', '杭州'], dir);
  if (r.json) {
    const empties = r.json.palaces.filter((p) => p.empty);
    ok('空宫：至少识别出一个空宫', empties.length > 0, `空宫数=${empties.length}`);
    if (empties.length) {
      eq('空宫：标注借自哪一宫', empties[0].borrowFrom, '迁移');
      eq('空宫：记下借到的对宫主星', (empties[0].borrowStars || []).slice().sort().join(''), '天同巨门');
      ok('空宫：命宫为空时仍给出宫名', typeof r.json.palaces.find((p) => p.isMing)?.name === 'string');
    }
  }
}

// ─── 7. 农历 / 公历等价 ─────────────────────────────────────────
{
  const d1 = path.join(TMP, 'lun');
  const d2 = path.join(TMP, 'sol');
  fs.mkdirSync(d1); fs.mkdirSync(d2);
  const a = run(['--gender', 'female', '--lunar', '1994-9-17', '--shichen', '辰'], d1);
  const b = run(['--gender', 'female', '--solar', '1994-10-21', '--shichen', '辰'], d2);
  ok('历法等价：两次都成功', a.code === 0 && b.code === 0, a.stderr || b.stderr);
  if (a.json && b.json) {
    ok('历法等价：农历输入与公历输入排出同一张盘', a.json.core.mingGong === b.json.core.mingGong
      && JSON.stringify(majorNames(palaceOf(a.json, a.json.core.mingGong)))
        === JSON.stringify(majorNames(palaceOf(b.json, b.json.core.mingGong))));
  }
}

// ─── 8. 文档契约对齐（H2） ──────────────────────────────────────
{
  const sample = path.join(TMP, 'gold');
  const files = fs.readdirSync(sample).filter((f) => f.endsWith('.json'));
  const j = JSON.parse(fs.readFileSync(path.join(sample, files[0]), 'utf8'));

  const has = (dotPath) => {
    const segs = dotPath.replace(/\[\]/g, '[0]').split('.');
    let cur = j;
    for (const s of segs) {
      const m = s.match(/^(\w+)\[(\d+)\]$/);
      if (m) { cur = cur?.[m[1]]?.[Number(m[2])]; }
      else cur = cur?.[s];
      if (cur === undefined || cur === null) return false;
    }
    return true;
  };

  // 从 references 里抽出被反引号包裹、形如 a[].b.c 的字段路径，逐个验证真的存在
  const docFields = new Set();
  for (const f of fs.readdirSync(REFS).filter((x) => x.endsWith('.md'))) {
    const text = fs.readFileSync(path.join(REFS, f), 'utf8');
    for (const m of text.matchAll(/`([a-zA-Z][a-zA-Z0-9_]{1,}(?:\[\])?(?:\.[a-zA-Z][a-zA-Z0-9_]*)+)`/g)) {
      const p = m[1];
      if (/\.(md|mjs|js|json|py|html)$/.test(p)) continue;      // 文件名，不是字段路径
      if (/^(scripts|references|templates)\//.test(p)) continue;  // 文件路径
      if (!/^(core|palaces|patterns|lunar|input|daXians|liunian)\./.test(p)) continue; // 只查 JSON 根键下的路径
      docFields.add(p);
    }
  }
  const missing = [...docFields].filter((p) => !has(p));
  ok('契约：文档写到的 JSON 字段全部真实存在', missing.length === 0,
    missing.length ? `缺失 ${missing.join(', ')}` : '');

  // CLI 参数与文档表格对齐：文档里出现的 --xxx 必须被 CLI 接受（--help 能跑通即说明参数解析未崩）
  const cliText = [CLI, path.join(HERE, '..', 'engine', 'cli.py')]
    .map((p) => fs.readFileSync(p, 'utf8'))
    .join('\n');
  const docArgs = new Set();
  for (const f of ['chart-data.md', 'SKILL.md']) {
    const p = f === 'SKILL.md' ? path.join(REFS, '..', f) : path.join(REFS, f);
    const text = fs.readFileSync(p, 'utf8');
    for (const m of text.matchAll(/(--[a-z][a-z-]{2,})/g)) docArgs.add(m[1]);
  }
  const undocumented = [...docArgs].filter((a) => !cliText.includes(a.slice(2)));
  ok('契约：文档里提到的 CLI 参数脚本都实现了', undocumented.length === 0,
    undocumented.length ? `未实现 ${undocumented.join(', ')}` : '');
}

// ─── 9. 盘面视觉契约（四化小箭头） ─────────────────────────────
{
  const dir = path.join(TMP, 'vis');
  fs.mkdirSync(dir);
  try {
    execFileSync(process.execPath, [CLI, '--name', '金标准', '--gender', 'male',
      '--solar', '1994-10-21', '--time', '08:45', '--city', '九江', '--out', dir],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  } catch { /* 上面的金标准用例已经报过错，这里不再重复报 */ }

  const htmlFile = fs.readdirSync(dir).find((f) => f.endsWith('.html'));
  const html = htmlFile ? fs.readFileSync(path.join(dir, htmlFile), 'utf8') : '';

  ok('盘面：生成了 HTML', Boolean(html), htmlFile ? '' : '未找到 .html 产物');

  // 四化标记 = 小箭头 SVG + 四化字，箭头用 currentColor 与字同色
  const badges = [...html.matchAll(/<span class="sh (lu|quan|ke|ji)">([\s\S]*?)<\/span>/g)];
  ok('盘面：四化标记全部带小箭头', badges.length > 0 && badges.every((m) => m[2].includes('<svg class="sha"')),
    `共 ${badges.length} 处，缺箭头的 ${badges.filter((m) => !m[2].includes('<svg class="sha"')).length} 处`);
  ok('盘面：四化标记字与箭头同色（currentColor）', /\.sh \.sha path\{[^}]*stroke:currentColor/.test(html));

  // 运限指针层已按用户要求去掉：盘面不该再有整层 SVG 覆盖或大限/流年/小限图例
  ok('盘面：不再有运限指针 SVG 层', !/class="yl"/.test(html));
  ok('盘面：不再有运限图例', !/c-ylegend/.test(html));
  ok('盘面：不再画贯穿盘面的虚线', !/stroke-dasharray/.test(html));

  // 新版 UI 交互与信息完整度校验
  ok('盘面：包含流年信息区', html.includes('class="c-ly"'));
  ok('盘面：包含格局总览区', html.includes('class="sec patterns-sec"'));
  ok('盘面：包含三方四正联动提示条与主题切换', html.includes('id="inspect-bar"') && html.includes('id="theme-toggle"'));
}

// ─── 10. 多体系 HTML 渲染与 CLI 健壮性（Python 引擎） ────────────
{
  const paipanSh = path.join(HERE, 'paipan.sh');
  const dir = path.join(TMP, 'multi');
  fs.mkdirSync(dir);

  const cases = [
    ['bazi', ['--system', 'bazi', '--name', '测试/甲', '--gender', 'Male', '--solar', '1994-10-21', '--time', '08:45', '--city', '长沙']],
    ['qimen', ['--system', 'qimen', '--name', '测试', '--gender', 'male', '--solar', '1994-10-21', '--time', '08:45', '--city', '长沙']],
    ['astrology', ['--system', 'astrology', '--name', '测试', '--gender', 'male', '--solar', '1994-10-21', '--time', '08:45', '--city', '长沙']],
    ['bazi_hepan', ['--system', 'bazi_hepan', '--name', '甲', '--gender', 'male', '--solar', '1994-10-21', '--time', '08:45', '--city', '长沙', '--second-name', '乙', '--second-gender', 'FEMALE', '--second-solar', '1996-03-08', '--second-time', '20:30', '--second-city', '杭州']],
    ['ziwei_hepan', ['--system', 'ziwei_hepan', '--name', '甲', '--gender', 'male', '--solar', '1994-10-21', '--time', '08:45', '--city', '长沙', '--second-name', '乙', '--second-gender', 'female', '--second-solar', '1996-03-08', '--second-time', '20:30', '--second-city', '杭州']],
    ['liuyao', ['--system', 'liuyao', '--name', '测试', '--method', 'coins', '--lines', '7,8,9,6,7,8', '--question', '这份工作要不要接']],
    ['meihua', ['--system', 'meihua', '--name', '测试', '--method', 'number', '--numbers', '37,18', '--question', '项目能成吗']],
    ['tarot', ['--system', 'tarot', '--name', '测试', '--spread', 'three', '--seed', 'selftest', '--question', '要不要搬家']],
    ['kongming', ['--system', 'kongming', '--name', '测试', '--characters', '佑咱统', '--question', '考试能过吗']],
    ['mbti', ['--system', 'mbti', '--name', '测试', '--answers', '3,4,2,3,5,3,3,2,4,3,3,3,2,4,5,3,3,2,3,4,3,3,3,2,4,3,5,3,3,4,2,3']],
  ];

  for (const [sys, args] of cases) {
    const sub = path.join(dir, sys);
    fs.mkdirSync(sub);
    try {
      const stdout = execFileSync('sh', [paipanSh, ...args, '--out', sub], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
      const htmlFile = fs.readdirSync(sub).find((f) => f.endsWith('.html'));
      const html = htmlFile ? fs.readFileSync(path.join(sub, htmlFile), 'utf8') : '';
      ok(`多体系(${sys})：成功产出 HTML/JSON/MD`, stdout.includes('HTML:') && html.includes('<!doctype html>') && html.includes('id="theme-toggle"'),
        htmlFile ? '' : '缺少 .html');
    } catch (e) {
      ok(`多体系(${sys})：成功产出 HTML/JSON/MD`, false, String(e.stderr || e.message).slice(0, 120));
    }
  }

  // 非法性别应报错退出，而不是静默当男排盘
  let badGenderRejected = false;
  try {
    execFileSync('sh', [paipanSh, '--system', 'bazi', '--name', '测试', '--gender', 'unknown', '--solar', '1994-10-21', '--time', '08:45', '--out', dir],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e) {
    badGenderRejected = (e.status ?? 0) !== 0 && String(e.stderr || '').includes('gender');
  }
  ok('Python CLI：非法性别明确报错退出', badGenderRejected);
}

// ─── 汇总 ───────────────────────────────────────────────────────
fs.rmSync(TMP, { recursive: true, force: true });
console.log(`\n自检结果：通过 ${pass} 项，失败 ${fail} 项`);
if (fail) {
  console.log('失败明细：');
  for (const f of failures) console.log(`  ✗ ${f}`);
  process.exit(1);
}
console.log('✓ 全部通过');
