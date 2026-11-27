/**
 * 紫微斗数命盘 HTML 渲染器（玄机 · 玄夜星金版）
 * ────────────────────────────────────────────────────────────────
 * 视觉体系：深空玄黑底 + 鎏金细线 + 星座/罗盘装饰 + 玻璃质感交互侧栏。
 * 布局结构：桌面双栏工作台（左 4×4 传统十二宫命盘 + 右固定玻璃详批侧栏，
 * 含「宫位详批 / 大限流年 / 格局总览」三页签，支持点击宫位联动高亮三方四正、
 * 点击大限或流年四化快速定位宫位）；内置「宣纸印本」浅色切换与 A4 打印排版。
 * 纯字符串拼接，零外部依赖，单文件可离线浏览。
 */

const STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

/** 地支 → 宫位在 4×4 棋盘中的 [行, 列]（行 1 在上，列 1 在左） */
const GRID_POS = {
  5: [1, 1], 6: [1, 2], 7: [1, 3], 8: [1, 4],
  4: [2, 1], 9: [2, 4],
  3: [3, 1], 10: [3, 4],
  2: [4, 1], 1: [4, 2], 0: [4, 3], 11: [4, 4],
};

/** 地支 → 盘面方位标注 */
const DIRECTIONS = {
  0: '正北方', 1: '北偏东', 2: '东偏北', 3: '正东方',
  4: '东偏南', 5: '南偏东', 6: '正南方', 7: '南偏西',
  8: '西偏南', 9: '正西方', 10: '西偏北', 11: '北偏西',
};

const SIHUA_CLASS = { 禄: 'lu', 权: 'quan', 科: 'ke', 忌: 'ji' };
const LEVEL_LABEL = { excellent: '上格', good: '吉格', neutral: '平格', caution: '留意' };

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const starToneClass = (raw, type) => {
  if (type === 'sha') return 'tone-sha';
  if (type === 'lucky') return 'tone-lucky';
  if (type === 'minor') return 'tone-minor';
  if (raw === '庙' || raw === '旺') return 'tone-bright';
  if (raw === '陷' || raw === '不' || raw === '闲') return 'tone-dim';
  return 'tone-mid';
};

/**
 * 四化标记：朝上小箭头 + 禄/权/科/忌 字，箭头与字同色（currentColor）。
 */
const SIHUA_ARROW = '<svg class="sha" viewBox="0 0 9 11" aria-hidden="true">'
  + '<path d="M4.5 10.2V2M4.5 2L1.5 5M4.5 2l3 3"/></svg>';

/** 顶部与中宫装饰用星盘罗盘徽章（实线几何，不使用虚线） */
const ASTROLABE_EMBLEM = `<svg class="emblem" viewBox="0 0 64 64" aria-hidden="true">
  <circle cx="32" cy="32" r="29" fill="none" stroke="currentColor" stroke-width="1" opacity=".55"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="currentColor" stroke-width=".8" opacity=".35"/>
  <circle cx="32" cy="32" r="10" fill="none" stroke="currentColor" stroke-width="1" opacity=".65"/>
  <path d="M32 3v9M32 52v9M3 32h9M52 32h9M11.5 11.5l6.4 6.4M46.1 46.1l6.4 6.4M52.5 11.5l-6.4 6.4M17.9 46.1l-6.4 6.4" stroke="currentColor" stroke-width=".9" opacity=".5"/>
  <polygon points="32,14 35,29 50,32 35,35 32,50 29,35 14,32 29,29" fill="currentColor" opacity=".82"/>
  <circle cx="32" cy="32" r="3.2" fill="var(--bg)"/>
</svg>`;

const starHtml = (star, isMajor) => {
  const tone = starToneClass(star.brightnessRaw, isMajor ? 'major' : star.type);
  const badge = star.siHua
    ? `<span class="sh ${SIHUA_CLASS[star.siHua] ?? ''}">${SIHUA_ARROW}${esc(star.siHua)}</span>` : '';
  return `<span class="star${isMajor ? ' major' : ''}">`
    + `<span class="nm ${tone}">${esc(star.name)}${badge}</span>`
    + `<span class="br">${esc(star.brightnessRaw ?? '')}</span>`
    + '</span>';
};

function palaceCell(ctx, branch) {
  const { palaceMap, mingBranch, shenBranch, dxBranch, lyBranch, meta } = ctx;
  const p = palaceMap[branch];
  if (!p) return '';
  const [row, col] = GRID_POS[branch];
  const isMing = branch === mingBranch;
  const isShen = branch === shenBranch;
  const isDx = branch === dxBranch;
  const isLy = branch === lyBranch;

  const majors = p.stars.filter((s) => s.type === 'major');
  const rest = p.stars.filter((s) => s.type !== 'major');

  const cls = ['cell'];
  if (isMing) cls.push('ming');
  if (isDx) cls.push('dx');
  if (isLy) cls.push('ly');

  const tags = [
    isMing ? '<span class="tag ming">命</span>' : '',
    isShen ? '<span class="tag shen">身</span>' : '',
    isLy ? '<span class="tag ly">流</span>' : '',
  ].filter(Boolean).join('');

  const borrow = p.isEmpty && p.borrowedStars && p.borrowedStars.length
    ? `<span class="borrow">借${esc(p.borrowedStars.join(''))}</span>` : '';
  const starBlock = majors.length
    ? `<div class="stars major-row">${majors.map((s) => starHtml(s, true)).join('')}</div>`
    : `<div class="stars major-row"><span class="empty">空宫</span>${borrow}</div>`;
  const restBlock = rest.length
    ? `<div class="stars minor-row">${rest.map((s) => starHtml(s, false)).join('')}</div>`
    : '';

  const s = meta.shen[branch] ?? {};
  const shenLine = [s.changsheng, s.boshi, s.suiqian, s.jiangqian]
    .filter(Boolean).map((t) => `<span>${esc(t)}</span>`).join('');

  const edge = `${col === 4 ? 'border-right:none;' : ''}${row === 4 ? 'border-bottom:none;' : ''}`;
  return `<div class="${cls.join(' ')}" data-branch="${branch}" role="button" tabindex="0" aria-label="${esc(p.name)}（${esc(STEMS[p.stem])}${esc(BRANCHES[branch])}）" style="grid-row:${row};grid-column:${col};${edge}">
    <div class="dxage">${p.daXianAge ? `${p.daXianAge[0]}–${p.daXianAge[1]}` : ''}</div>
    ${starBlock}
    ${restBlock}
    <div class="shier">${shenLine}</div>
    <div class="gz">
      <div class="ganzhi">${esc(STEMS[p.stem])}${esc(BRANCHES[branch])}</div>
      <div class="pname">${esc(p.name)}${tags}</div>
    </div>
  </div>`;
}

/** 方位三角 */
const ARROW = { l: '<i class="arw l"></i>', r: '<i class="arw r"></i>', u: '<i class="arw u"></i>' };

function gutters() {
  const top = [1, 2, 3, 4].map((c) => {
    const b = Object.keys(GRID_POS).find((k) => GRID_POS[k][0] === 1 && GRID_POS[k][1] === c);
    return b !== undefined && c > 1 && c < 4 ? `<span>${DIRECTIONS[b]}</span>` : '<span></span>';
  }).join('');
  const bottom = [1, 2, 3, 4].map((c) => {
    const b = Object.keys(GRID_POS).find((k) => GRID_POS[k][0] === 4 && GRID_POS[k][1] === c);
    return b !== undefined && c > 1 && c < 4 ? `<span>${ARROW.u}${DIRECTIONS[b]}</span>` : '<span></span>';
  }).join('');
  const side = (col) => [1, 2, 3, 4].map((r) => {
    const b = Object.keys(GRID_POS).find((k) => GRID_POS[k][1] === col && GRID_POS[k][0] === r);
    if (b === undefined) return '<span></span>';
    const arrow = col === 1 ? ARROW.l : ARROW.r;
    return `<span class="v">${arrow}${DIRECTIONS[b]}</span>`;
  }).join('');

  return `<div class="gut gut-top">${top}</div>
    <div class="gut gut-left">${side(1)}</div>
    <div class="gut gut-right">${side(4)}</div>
    <div class="gut gut-bottom">${bottom}</div>`;
}

/** 中宫信息区 */
function centerPanel(ctx) {
  const { chart, title, liunian } = ctx;
  const li = chart.lunarInfo;
  const lunarText = `${li.lunarYear}年${li.isLeapMonth ? '闰' : ''}${li.lunarMonth}月${li.lunarDay}日`;
  const dx = chart.currentDaXianIndex >= 0 ? chart.daXians[chart.currentDaXianIndex] : null;

  const pillars = (label, arr) => (arr && arr.length === 4 ? `
    <div class="pillar-block">
      <div class="pillar-label">${esc(label)}</div>
      <div class="pillar-grid">
        ${['年', '月', '日', '时'].map((k, i) => `<div class="pg"><i>${k}</i><b>${esc(arr[i])}</b></div>`).join('')}
      </div>
    </div>` : '');

  const extra = ctx.meta;

  const lyHtml = liunian ? `
    <div class="c-ly">
      <div class="c-ly-hd">
        <span>流年 ${esc(liunian.year)} · ${esc(liunian.ganZhi)}</span>
        <span class="c-ly-sub">入${esc(liunian.palace ?? '')}（${esc(liunian.branch ?? '')}） · 虚岁 ${esc(liunian.nominalAge ?? '')}</span>
      </div>
      <div class="c-ly-sh">
        ${(liunian.siHua || []).map((item) => {
          const bIdx = item.branch ? BRANCHES.indexOf(item.branch) : -1;
          return `<button type="button" class="ly-item" data-jump="${bIdx}"><em class="sh ${SIHUA_CLASS[item.hua] ?? ''}">${SIHUA_ARROW}${esc(item.hua)}</em><span>${esc(item.star)}</span><i class="ly-pal">${esc(item.palace ?? '')}</i></button>`;
        }).join('')}
      </div>
    </div>` : '';

  return `<div class="center">
    <div class="center-halo" aria-hidden="true">${ASTROLABE_EMBLEM}</div>
    <div class="c-head">
      <div class="c-name">${esc(title)}</div>
      <div class="c-sub">${esc(chart.yinYangGender ?? '')} · ${esc(chart.wuxingJuName)} · 虚岁 ${esc(chart.currentAge ?? '')}</div>
    </div>

    <div class="c-meta">
      <div><i>命主</i><b>${esc(chart.mingZhu ?? '')}</b></div>
      <div><i>身主</i><b>${esc(chart.shenZhu ?? '')}</b></div>
      <div><i>命宫</i><b>${esc(BRANCHES[chart.mingGongBranch])}</b></div>
      <div><i>身宫</i><b>${esc(BRANCHES[chart.shenGongBranch])}</b></div>
    </div>

    <div class="c-pillars">
      ${pillars('节气四柱', li.fourPillars)}
      ${pillars('非节气四柱', li.fourPillarsLunar)}
    </div>

    <div class="c-times">
      <div><i>真太阳时</i><span>${esc(extra.trueSolarText)}</span></div>
      <div><i>钟表时间</i><span>${esc(extra.clockText)}</span></div>
      <div><i>农历</i><span>${esc(lunarText)}</span></div>
      ${extra.birthplace ? `<div><i>出生地</i><span>${esc(extra.birthplace)}</span></div>` : ''}
      ${extra.longitudeNote ? `<div><i>经度修正</i><span>${esc(extra.longitudeNote)}</span></div>` : ''}
    </div>

    ${dx ? `<button type="button" class="c-dx" data-jump="${dx.palaceBranch}"><span class="k">当前大限</span><span class="v">${dx.startAge}–${dx.endAge} 岁 · ${esc(dx.palaceName)}</span></button>` : ''}
    ${lyHtml}

    <div class="c-legend">
      <span><em class="sh lu">${SIHUA_ARROW}禄</em>化禄</span>
      <span><em class="sh quan">${SIHUA_ARROW}权</em>化权</span>
      <span><em class="sh ke">${SIHUA_ARROW}科</em>化科</span>
      <span><em class="sh ji">${SIHUA_ARROW}忌</em>化忌</span>
    </div>
  </div>`;
}

/** 右侧玻璃侧栏：宫位详批 / 大限流年 / 格局总览 */
function sidePanel(ctx) {
  const { chart, liunian, patterns } = ctx;
  const dxList = (chart.daXians || []).map((d, i) => {
    const isCur = i === chart.currentDaXianIndex;
    return `<button type="button" class="dx-item${isCur ? ' is-cur' : ''}" data-jump="${d.palaceBranch}">
      <span class="dx-range">${d.startAge}–${d.endAge} 岁</span>
      <span class="dx-pal">${esc(d.palaceName)}（${esc(BRANCHES[d.palaceBranch])}）</span>
      ${isCur ? '<span class="tag dx-tag">当前</span>' : ''}
    </button>`;
  }).join('');

  const patRows = (patterns && patterns.length)
    ? patterns.map((p) => {
        const lvl = p.level || 'neutral';
        const label = LEVEL_LABEL[lvl] || lvl;
        const palaces = Array.isArray(p.palaces) ? p.palaces.join(' / ') : '';
        return `<div class="pat-row">
          <div class="pat-head">
            <span class="pat-name">${esc(p.name)}</span>
            <span class="pat-lvl lvl-${esc(lvl)}">${esc(label)}</span>
            ${palaces ? `<span class="pat-pal">${esc(palaces)}</span>` : ''}
          </div>
          ${p.description ? `<div class="pat-desc">${esc(p.description)}</div>` : ''}
        </div>`;
      }).join('')
    : '<div class="empty-tip">本盘未触发特殊格局，按命宫主星与三方四正直接论断。</div>';

  const lyCard = liunian ? `
    <div class="side-block">
      <div class="side-k">流年焦点 · ${esc(liunian.year)} ${esc(liunian.ganZhi)}</div>
      <div class="ly-summary">流年命宫入 <b>${esc(liunian.palace ?? '')}（${esc(liunian.branch ?? '')}）</b> · 虚岁 ${esc(liunian.nominalAge ?? '')}</div>
      <div class="ly-grid">
        ${(liunian.siHua || []).map((it) => {
          const bIdx = it.branch ? BRANCHES.indexOf(it.branch) : -1;
          return `<button type="button" class="ly-card" data-jump="${bIdx}">
            <span class="sh ${SIHUA_CLASS[it.hua] ?? ''}">${SIHUA_ARROW}${esc(it.hua)}</span>
            <b>${esc(it.star)}</b>
            <i>${esc(it.palace ?? '')}</i>
          </button>`;
        }).join('')}
      </div>
    </div>` : '';

  return `<aside class="side-panel">
    <div class="tabs" role="tablist">
      <button type="button" class="tab active" data-tab="inspect" role="tab" aria-selected="true">宫位详批</button>
      <button type="button" class="tab" data-tab="timeline" role="tab" aria-selected="false">大限流年</button>
      <button type="button" class="tab" data-tab="patterns" role="tab" aria-selected="false">格局（${patterns?.length ?? 0}）</button>
    </div>

    <div class="tab-pane active" data-pane="inspect">
      <div id="inspect-bar" class="inspect-card">
        <div class="inspect-top">
          <div>
            <div class="inspect-title" id="inspect-title">命宫详览</div>
            <div class="inspect-sub" id="inspect-sub">点击左侧任意宫位，联动高亮三方四正</div>
          </div>
          <button type="button" class="inspect-clear" id="inspect-clear" style="display:none">复位</button>
        </div>
        <div class="trine-chips" id="trine-chips"></div>
        <div class="star-groups" id="star-groups"></div>
        <div class="inspect-kv" id="inspect-kv"></div>
      </div>
    </div>

    <div class="tab-pane" data-pane="timeline">
      ${lyCard}
      <div class="side-block">
        <div class="side-k">十二大限（点击定位宫位）</div>
        <div class="dx-list">${dxList}</div>
      </div>
    </div>

    <div class="tab-pane" data-pane="patterns">
      <div class="sec patterns-sec">
        <div class="side-k">识别到的格局 · 共 ${patterns?.length ?? 0} 项</div>
        <div class="pat-list">${patRows}</div>
      </div>
    </div>
  </aside>`;
}

/** 交互数据 JSON */
function buildInteractiveData(ctx) {
  const { palaceMap, meta, mingBranch } = ctx;
  const palaces = {};
  for (let b = 0; b < 12; b++) {
    const p = palaceMap[b];
    if (!p) continue;
    const s = meta.shen[b] ?? {};
    const xx = (meta.xiaoxian?.[b] ?? []).slice(0, 8);
    const fmt = (st) => `${st.name}${st.brightnessRaw ?? ''}${st.siHua ? `[${st.siHua}]` : ''}`;
    palaces[b] = {
      branch: BRANCHES[b],
      branchIdx: b,
      ganzhi: `${STEMS[p.stem]}${BRANCHES[b]}`,
      name: p.name,
      isMing: p.isMingGong,
      isShen: p.isShenGong,
      daXian: p.daXianAge ? `${p.daXianAge[0]}–${p.daXianAge[1]} 岁` : '—',
      xiaoXian: xx.length ? `${xx.join('、')} 岁` : '—',
      majors: p.stars.filter((st) => st.type === 'major').map(fmt),
      lucky: p.stars.filter((st) => st.type === 'lucky').map(fmt),
      sha: p.stars.filter((st) => st.type === 'sha').map(fmt),
      minor: p.stars.filter((st) => st.type === 'minor').map(fmt),
      borrow: p.isEmpty && p.borrowedStars?.length ? `空宫借${p.borrowedFromName ?? '对宫'}（${p.borrowedStars.join('、')}）` : '',
      shier: [s.changsheng, s.boshi, s.suiqian, s.jiangqian].filter(Boolean).join(' · '),
    };
  }
  return JSON.stringify({ mingBranch, palaces }).replace(/</g, '\\u003c');
}

const CSS = `
:root{
  color-scheme:dark;
  --bg:#07090f;
  --bg-glow-1:rgba(214,172,96,.12);
  --bg-glow-2:rgba(76,62,148,.16);
  --bg-glow-3:rgba(36,78,128,.14);
  --surface:rgba(13,17,28,.82);
  --surface-solid:#0f1320;
  --surface-2:rgba(20,25,40,.74);
  --surface-ming:rgba(214,169,92,.11);
  --surface-dx:rgba(150,112,230,.12);
  --ink:#f3efe6; --sub:#c2baa9; --faint:#857f74;
  --gold:#e6c47e; --gold-dim:#b59150; --gold-line:rgba(224,188,118,.28); --gold-strong:rgba(224,188,118,.58);
  --line:rgba(224,188,118,.16); --line-strong:rgba(224,188,118,.38);
  --accent:#f06a5b; --accent-soft:rgba(240,106,91,.16); --accent-line:rgba(240,106,91,.55);
  --dx-ink:#c6a4ff; --dx-line:rgba(182,140,255,.45);
  --star-bright:#f3c876; --star-mid:#df9f62; --star-dim:#8b8994;
  --star-lucky:#73c2ff; --star-sha:#d09eff; --star-minor:#8b909e;
  --sh-lu:#52d692; --sh-quan:#c6a4ff; --sh-ke:#73c2ff; --sh-ji:#f26b5e;
  --trine-bg:rgba(115,194,255,.11); --trine-line:rgba(115,194,255,.55);
  --opp-bg:rgba(240,106,91,.12); --opp-line:rgba(240,106,91,.58);
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
  --surface-ming:#fdf5e6;
  --surface-dx:#f4effc;
  --ink:#1f1d18; --sub:#544e43; --faint:#7d7668;
  --gold:#9e7428; --gold-dim:#8c6929; --gold-line:rgba(158,116,40,.28); --gold-strong:rgba(158,116,40,.6);
  --line:#e3dccd; --line-strong:#cbbca0;
  --accent:#b4402f; --accent-soft:#fbeae6; --accent-line:#d99a8e;
  --dx-ink:#6b46a8; --dx-line:#bda6e0;
  --star-bright:#b4402f; --star-mid:#9a6720; --star-dim:#8d867a;
  --star-lucky:#1f5e94; --star-sha:#6d4796; --star-minor:#7c766b;
  --sh-lu:#1e7a4c; --sh-quan:#6b46a8; --sh-ke:#1f5e94; --sh-ji:#b4402f;
  --trine-bg:#ebf3fa; --trine-line:#7ba8d4;
  --opp-bg:#faeae6; --opp-line:#d68a7d;
}
*{box-sizing:border-box;-webkit-font-smoothing:antialiased}
html,body{margin:0;padding:0;min-height:100vh;color:var(--ink);font-family:var(--font-sans);line-height:1.5;
  background-color:var(--bg);
  background-image:
    radial-gradient(ellipse 75% 55% at 18% 8%, var(--bg-glow-2), transparent 65%),
    radial-gradient(ellipse 60% 45% at 84% 12%, var(--bg-glow-1), transparent 62%),
    radial-gradient(ellipse 70% 50% at 50% 96%, var(--bg-glow-3), transparent 68%);
  background-attachment:fixed}

.page{max-width:1360px;margin:0 auto;padding:20px 24px 48px}

/* 顶部星象抬头 */
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:12px 18px;margin-bottom:20px;
  background:var(--surface);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--gold-line);border-radius:4px;position:relative}
.topbar::before,.topbar::after{content:"";position:absolute;width:10px;height:10px;border-color:var(--gold);border-style:solid;pointer-events:none}
.topbar::before{top:-1px;left:-1px;border-width:1.5px 0 0 1.5px}
.topbar::after{bottom:-1px;right:-1px;border-width:0 1.5px 1.5px 0}
.brand{display:flex;align-items:center;gap:12px}
.brand .emblem{width:36px;height:36px;color:var(--gold);flex:0 0 auto;animation:spin-slow 80s linear infinite}
@keyframes spin-slow{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.brand .emblem{animation:none}}
.brand-t{font-family:var(--font-serif);font-size:20px;font-weight:400;letter-spacing:.26em;color:var(--gold)}
.brand-sub{font-size:12px;color:var(--faint);margin-top:1px;font-variant-numeric:tabular-nums}
.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.btn{appearance:none;border:1px solid var(--gold-line);background:rgba(224,188,118,.06);color:var(--gold);
  font-family:var(--font-sans);font-size:12.5px;height:34px;padding:0 14px;border-radius:3px;cursor:pointer;
  transition:border-color 150ms ease,background-color 150ms ease,color 150ms ease}
.btn:hover{border-color:var(--gold);background:rgba(224,188,118,.14)}

/* 主工作台：左盘右栏 */
.workspace{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:20px;align-items:start}

/* 命盘外框 */
.sheet{background:var(--surface);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1px solid var(--gold-strong);border-radius:4px;padding:18px 20px 16px;position:relative;
  box-shadow:0 24px 60px rgba(0,0,0,.35)}
[data-theme="light"] .sheet{box-shadow:0 10px 30px rgba(40,30,15,.08)}
.corner{position:absolute;width:14px;height:14px;border-color:var(--gold);border-style:solid;pointer-events:none}
.corner.tl{top:-1px;left:-1px;border-width:2px 0 0 2px}
.corner.tr{top:-1px;right:-1px;border-width:2px 2px 0 0}
.corner.bl{bottom:-1px;left:-1px;border-width:0 0 2px 2px}
.corner.br{bottom:-1px;right:-1px;border-width:0 2px 2px 0}

/* 方位槽 + 棋盘 */
.board-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.board-outer{display:grid;grid-template-columns:26px 1fr 26px;grid-template-rows:20px 1fr 20px;min-width:720px}
.gut{display:grid;font-size:9.5px;color:var(--gold-dim);letter-spacing:.14em;font-family:var(--font-serif)}
.gut>span{display:flex;align-items:center;justify-content:center;gap:2px}
.gut-top{grid-row:1;grid-column:2;grid-template-columns:repeat(4,1fr)}
.gut-bottom{grid-row:3;grid-column:2;grid-template-columns:repeat(4,1fr)}
.gut-left{grid-row:2;grid-column:1;grid-template-rows:repeat(4,1fr)}
.gut-right{grid-row:2;grid-column:3;grid-template-rows:repeat(4,1fr)}
.gut .v{writing-mode:vertical-rl}
.arw{display:inline-block;width:0;height:0;border-style:solid;opacity:.75;flex:0 0 auto}
.arw.l{border-width:3px 4.5px 3px 0;border-color:transparent var(--sh-lu) transparent transparent}
.arw.r{border-width:3px 0 3px 4.5px;border-color:transparent transparent transparent var(--sh-ke)}
.arw.u{border-width:0 3px 4.5px 3px;border-color:transparent transparent var(--sh-ke) transparent}
.gut-right .arw.r{order:2}

.board{position:relative;grid-row:2;grid-column:2;display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr);
  border:1.5px solid var(--gold-strong);background:var(--surface-solid);min-height:860px;font-family:var(--font-serif)}
.cell{position:relative;border-right:1px solid var(--line);border-bottom:1px solid var(--line);
  padding:18px 8px 36px;display:flex;flex-direction:column;background:transparent;overflow:hidden;cursor:pointer;
  transition:background-color 150ms ease,box-shadow 150ms ease;outline:none}
.cell:hover{background:rgba(224,188,118,.06)}
.cell:focus-visible{box-shadow:inset 0 0 0 1.5px var(--gold)}
.cell.dx{background:var(--surface-dx)}
.cell.ming{background:var(--surface-ming);box-shadow:inset 0 0 0 1.5px var(--gold-strong)}
.cell.is-focus{background:rgba(230,196,126,.17)!important;box-shadow:inset 0 0 0 2px var(--gold)!important;z-index:2}
.cell.is-opp{background:var(--opp-bg)!important;box-shadow:inset 0 0 0 1.5px var(--opp-line)!important;z-index:1}
.cell.is-trine{background:var(--trine-bg)!important;box-shadow:inset 0 0 0 1.5px var(--trine-line)!important;z-index:1}

.dxage{position:absolute;top:5px;right:7px;font-size:10px;color:var(--faint);font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.cell.dx .dxage{color:var(--dx-ink);font-weight:600}
.stars{display:flex;flex-wrap:wrap;gap:3px 7px;align-items:flex-start}
.major-row{margin-bottom:3px}
.minor-row{margin-top:2px}
.star{display:inline-flex;flex-direction:column;align-items:center;line-height:1.1}
.star .nm{font-weight:700;white-space:nowrap}
.star .br{font-size:8.5px;color:var(--faint);margin-top:1px;height:10px;font-family:var(--font-sans)}
.star.major .nm{font-size:15px;letter-spacing:.02em}
.star:not(.major) .nm{font-size:11.5px;font-weight:600}
.tone-bright{color:var(--star-bright)}.tone-mid{color:var(--star-mid)}.tone-dim{color:var(--star-dim)}
.tone-lucky{color:var(--star-lucky)}.tone-sha{color:var(--star-sha)}.tone-minor{color:var(--star-minor)}
.empty{font-size:11.5px;color:var(--faint);font-style:italic}
.borrow{font-size:9.5px;color:var(--gold-dim);margin-left:4px;align-self:center;font-family:var(--font-sans)}

/* 四化标记：小箭头 + 字，currentColor 同色 */
.sh{display:inline-flex;align-items:center;gap:1px;font-size:8.5px;font-style:normal;font-weight:700;
  margin-left:2px;vertical-align:1.5px;line-height:1;letter-spacing:0;font-family:var(--font-sans)}
.sh .sha{width:6.5px;height:8px;flex:0 0 auto;display:block}
.sh .sha path{fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.sh.lu{color:var(--sh-lu)}.sh.quan{color:var(--sh-quan)}.sh.ke{color:var(--sh-ke)}.sh.ji{color:var(--sh-ji)}
.star.major .sh{font-size:9.5px;vertical-align:2px}
.star.major .sh .sha{width:7px;height:8.5px}

.shier{position:absolute;left:7px;bottom:5px;width:max-content;display:flex;flex-direction:column;gap:1px;
  font-size:8.5px;color:var(--faint);line-height:1.2;white-space:nowrap;font-family:var(--font-sans)}
.gz{position:absolute;right:7px;bottom:5px;text-align:right;white-space:nowrap}
.ganzhi{font-size:9.5px;color:var(--gold-dim);letter-spacing:.06em;font-family:var(--font-mono)}
.pname{font-size:13px;font-weight:700;letter-spacing:.04em;margin-top:1px;color:var(--ink);
  display:flex;align-items:center;justify-content:flex-end;gap:3px}
.tag{font-size:9px;font-weight:600;padding:0 4px;border-radius:2px;line-height:14px;font-family:var(--font-sans)}
.tag.ming{color:var(--gold);background:rgba(230,196,126,.16);border:1px solid var(--gold-strong)}
.tag.shen{color:var(--sh-ke);background:rgba(115,194,255,.14);border:1px solid rgba(115,194,255,.45)}
.tag.ly{color:var(--dx-ink);background:var(--surface-dx);border:1px solid var(--dx-line)}
.tag.dx-tag{color:var(--dx-ink);border:1px solid var(--dx-line);background:var(--surface-dx)}

/* 中宫 */
.center{position:relative;grid-row:2 / 4;grid-column:2 / 4;border-right:1px solid var(--line);border-bottom:1px solid var(--line);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:16px 14px;
  background:radial-gradient(circle at 50% 42%, rgba(230,196,126,.09), transparent 68%);overflow:hidden}
.center-halo{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;opacity:.08;color:var(--gold)}
.center-halo .emblem{width:240px;height:240px}
.c-head,.c-meta,.c-pillars,.c-times,.c-dx,.c-ly,.c-legend{position:relative;z-index:1}
.c-head{text-align:center}
.c-name{font-family:var(--font-serif);font-size:25px;letter-spacing:.22em;font-weight:400;color:var(--gold);
  max-width:100%;overflow-wrap:anywhere}
.c-sub{font-family:var(--font-sans);font-size:12px;color:var(--sub);margin-top:3px;font-variant-numeric:tabular-nums}
.c-meta{display:grid;grid-template-columns:repeat(4,auto);gap:4px 16px;font-size:11.5px;color:var(--sub);font-family:var(--font-sans);
  padding:7px 14px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.c-meta i{font-style:normal;color:var(--faint);margin-right:4px}
.c-meta b{font-weight:600;color:var(--gold)}
.c-pillars{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.pillar-block{border:1px solid var(--gold-line);border-radius:3px;padding:5px 10px 6px;background:var(--surface-2);min-width:136px}
.pillar-label{font-family:var(--font-sans);font-size:9.5px;color:var(--gold-dim);margin-bottom:3px;text-align:center;letter-spacing:.08em}
.pillar-grid{display:flex;gap:8px;justify-content:center}
.pg{display:flex;flex-direction:column;align-items:center}
.pg i{font-family:var(--font-sans);font-style:normal;font-size:9px;color:var(--faint)}
.pg b{font-family:var(--font-serif);font-size:13.5px;font-weight:600;color:var(--ink)}
.c-times{display:flex;flex-direction:column;gap:2px;font-family:var(--font-sans);font-size:11px;color:var(--sub);font-variant-numeric:tabular-nums}
.c-times>div{display:flex;align-items:baseline}
.c-times i{font-style:normal;flex:0 0 58px;color:var(--faint);text-align:right;margin-right:8px}
.c-dx{appearance:none;border:1px solid var(--dx-line);background:var(--surface-dx);border-radius:3px;padding:5px 14px;
  display:flex;align-items:center;gap:8px;font-family:var(--font-sans);cursor:pointer;transition:border-color 140ms ease}
.c-dx:hover{border-color:var(--dx-ink)}
.c-dx .k{font-size:10.5px;color:var(--faint)}
.c-dx .v{font-size:12px;color:var(--dx-ink);font-weight:600;font-variant-numeric:tabular-nums}
.c-ly{width:100%;max-width:316px;border:1px solid var(--gold-line);background:var(--surface-2);border-radius:3px;padding:7px 10px;font-family:var(--font-sans)}
.c-ly-hd{display:flex;justify-content:space-between;align-items:baseline;font-size:11px;color:var(--gold);font-weight:600;padding-bottom:4px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.c-ly-sub{font-weight:400;color:var(--faint);font-size:10px}
.c-ly-sh{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 8px;margin-top:5px}
.ly-item{appearance:none;border:1px solid transparent;background:transparent;color:var(--sub);font-family:var(--font-sans);
  font-size:11px;display:flex;align-items:center;gap:3px;padding:2px 4px;border-radius:2px;cursor:pointer;text-align:left}
.ly-item:hover{border-color:var(--gold-line);color:var(--ink)}
.ly-item .sh{margin-left:0}
.ly-pal{font-style:normal;color:var(--faint);font-size:10px;margin-left:auto}
.c-legend{display:flex;gap:12px;font-family:var(--font-sans);font-size:10.5px;color:var(--faint);align-items:center}
.c-legend span{display:inline-flex;align-items:center;gap:3px}
.c-legend .sh{font-size:9.5px;margin-left:0}

.ft{margin-top:12px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:11.5px;color:var(--faint);
  border-top:1px solid var(--line);padding-top:10px}
.ft .r{font-family:var(--font-mono);color:var(--gold-dim);font-variant-numeric:tabular-nums}

/* 右侧玻璃侧栏 */
.side-panel{position:sticky;top:20px;background:var(--surface);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1px solid var(--gold-line);border-radius:4px;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,.3)}
[data-theme="light"] .side-panel{box-shadow:0 10px 30px rgba(40,30,15,.08)}
.tabs{display:grid;grid-template-columns:repeat(3,1fr);border-bottom:1px solid var(--gold-line);background:rgba(224,188,118,.04)}
.tab{appearance:none;border:none;border-bottom:2px solid transparent;background:transparent;color:var(--faint);
  font-family:var(--font-sans);font-size:12.5px;padding:11px 6px;cursor:pointer;transition:color 140ms ease,border-color 140ms ease}
.tab:hover{color:var(--ink)}
.tab.active{color:var(--gold);border-bottom-color:var(--gold);font-weight:600}
.tab-pane{display:none;padding:16px;max-height:820px;overflow-y:auto}
.tab-pane.active{display:block}

.inspect-top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding-bottom:12px;border-bottom:1px solid var(--line)}
.inspect-title{font-family:var(--font-serif);font-size:20px;color:var(--gold);font-weight:400;letter-spacing:.06em}
.inspect-sub{font-size:12px;color:var(--faint);margin-top:2px}
.inspect-clear{appearance:none;border:1px solid var(--gold-line);background:transparent;color:var(--gold);font-size:11.5px;padding:3px 9px;border-radius:2px;cursor:pointer}
.inspect-clear:hover{border-color:var(--gold)}

.trine-chips{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin:12px 0}
.t-chip{appearance:none;border:1px solid var(--line);background:var(--surface-2);color:var(--sub);border-radius:3px;
  padding:6px 8px;font-size:12px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;font-family:var(--font-sans)}
.t-chip:hover{border-color:var(--gold-strong);color:var(--ink)}
.t-chip.role-self{border-color:var(--gold-strong);color:var(--gold)}
.t-chip.role-opp{border-color:var(--opp-line)}
.t-chip.role-trine{border-color:var(--trine-line)}
.t-chip i{font-style:normal;font-size:10px;color:var(--faint)}

.star-groups{display:flex;flex-direction:column;gap:10px;margin:12px 0}
.sg-box{border:1px solid var(--line);border-radius:3px;padding:8px 10px;background:var(--surface-2)}
.sg-k{font-size:11px;color:var(--gold-dim);margin-bottom:5px;letter-spacing:.08em}
.sg-tags{display:flex;flex-wrap:wrap;gap:5px}
.s-pill{font-size:12px;padding:2px 7px;border-radius:2px;border:1px solid var(--line);background:rgba(255,255,255,.03)}
.s-pill.major{color:var(--star-bright);border-color:var(--gold-line);font-weight:600}
.s-pill.lucky{color:var(--star-lucky);border-color:rgba(115,194,255,.35)}
.s-pill.sha{color:var(--star-sha);border-color:rgba(208,158,255,.35)}
.s-pill.minor{color:var(--sub)}

.inspect-kv{display:flex;flex-direction:column;gap:6px;padding-top:10px;border-top:1px solid var(--line);font-size:12px}
.ikv-row{display:flex;justify-content:space-between;gap:10px}
.ikv-row i{font-style:normal;color:var(--faint);flex:0 0 48px}
.ikv-row span{color:var(--sub);text-align:right;font-variant-numeric:tabular-nums}

.side-block{margin-bottom:16px}
.side-k{font-size:11.5px;color:var(--gold-dim);letter-spacing:.1em;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.ly-summary{font-size:12.5px;color:var(--sub);margin-bottom:8px}
.ly-summary b{color:var(--gold)}
.ly-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}
.ly-card{appearance:none;border:1px solid var(--line);background:var(--surface-2);border-radius:3px;padding:7px 9px;
  display:flex;align-items:center;gap:5px;color:var(--ink);font-size:12px;cursor:pointer;font-family:var(--font-sans)}
.ly-card:hover{border-color:var(--gold)}
.ly-card i{font-style:normal;margin-left:auto;font-size:11px;color:var(--faint)}
.dx-list{display:flex;flex-direction:column;gap:5px}
.dx-item{appearance:none;border:1px solid var(--line);background:var(--surface-2);color:var(--sub);border-radius:3px;
  padding:7px 10px;display:flex;align-items:center;gap:10px;font-size:12.5px;cursor:pointer;font-family:var(--font-sans);text-align:left}
.dx-item:hover{border-color:var(--gold-strong);color:var(--ink)}
.dx-item.is-cur{border-color:var(--dx-line);background:var(--surface-dx);color:var(--ink)}
.dx-range{font-family:var(--font-mono);font-size:12px;color:var(--gold);min-width:72px;font-variant-numeric:tabular-nums}
.dx-pal{flex:1}

.pat-list{display:flex;flex-direction:column;gap:10px}
.pat-row{padding:10px 11px;border:1px solid var(--line);border-radius:3px;background:var(--surface-2)}
.pat-head{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.pat-name{font-family:var(--font-serif);font-size:14.5px;color:var(--gold);font-weight:600}
.pat-lvl{font-size:10.5px;padding:1px 6px;border-radius:2px;border:1px solid var(--line)}
.lvl-excellent{color:var(--gold);border-color:var(--gold-strong);background:rgba(230,196,126,.14)}
.lvl-good{color:var(--sh-lu);border-color:rgba(82,214,146,.45);background:rgba(82,214,146,.12)}
.lvl-caution{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.pat-pal{margin-left:auto;font-size:11px;color:var(--faint)}
.pat-desc{margin-top:5px;font-size:12px;color:var(--sub);line-height:1.65}
.empty-tip{font-size:12.5px;color:var(--faint);padding:8px 0}

@media (max-width: 1120px){
  .workspace{grid-template-columns:1fr}
  .side-panel{position:static}
  .tab-pane{max-height:none}
}
@media (max-width: 760px){
  .page{padding:12px 10px 32px}
  .topbar{padding:10px 12px}
  .sheet{padding:12px 10px}
  .c-meta{grid-template-columns:repeat(2,auto)}
}
@media print{
  html,body{background:#fff!important;color:#1f1d18!important}
  .topbar,.tabs{display:none!important}
  .workspace{display:block}
  .sheet,.side-panel{box-shadow:none!important;background:#fff!important;border:1px solid #ccc!important;backdrop-filter:none}
  .tab-pane{display:block!important;max-height:none!important}
  .board-outer{min-width:0}
  .board{min-height:0;height:212mm;background:#fff!important}
  .center-halo{display:none}
  @page{size:A4 portrait;margin:6mm}
}
`;

const SCRIPT = `
(function(){
  const root = document.documentElement;
  const themeBtn = document.getElementById('theme-toggle');
  const printBtn = document.getElementById('print-btn');
  const dataEl = document.getElementById('chart-data');
  const data = dataEl ? JSON.parse(dataEl.textContent) : null;

  const setTheme = (t) => {
    root.dataset.theme = t;
    if (themeBtn) themeBtn.textContent = t === 'light' ? '玄夜星金' : '宣纸印本';
  };
  setTheme('dark');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => setTheme(root.dataset.theme === 'light' ? 'dark' : 'light'));
  }
  if (printBtn) printBtn.addEventListener('click', () => window.print());

  // 侧栏页签切换
  const tabs = Array.from(document.querySelectorAll('.tab[data-tab]'));
  const panes = Array.from(document.querySelectorAll('.tab-pane[data-pane]'));
  const switchTab = (name) => {
    tabs.forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    panes.forEach((p) => p.classList.toggle('active', p.dataset.pane === name));
  };
  tabs.forEach((t) => t.addEventListener('click', () => switchTab(t.dataset.tab)));

  if (!data) return;
  const cells = Array.from(document.querySelectorAll('.cell[data-branch]'));
  const clearBtn = document.getElementById('inspect-clear');
  const titleEl = document.getElementById('inspect-title');
  const subEl = document.getElementById('inspect-sub');
  const chipsEl = document.getElementById('trine-chips');
  const groupsEl = document.getElementById('star-groups');
  const kvEl = document.getElementById('inspect-kv');

  const escH = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));

  const renderInspector = (b, showClear) => {
    const p = data.palaces[b];
    if (!p) return;
    const opp = (b + 6) % 12;
    const t1 = (b + 4) % 12;
    const t2 = (b + 8) % 12;
    const po = data.palaces[opp], p1 = data.palaces[t1], p2 = data.palaces[t2];

    titleEl.textContent = p.ganzhi + ' · ' + p.name + (p.isMing ? '（命）' : '') + (p.isShen ? '（身）' : '');
    subEl.textContent = p.borrow || ('大限 ' + p.daXian + ' · 三方四正已联动高亮');
    clearBtn.style.display = showClear ? '' : 'none';

    const chipDefs = [
      { role: 'self', label: '本宫', item: p },
      { role: 'opp', label: '对宫', item: po },
      { role: 'trine', label: '三合', item: p1 },
      { role: 'trine', label: '三合', item: p2 },
    ];
    chipsEl.innerHTML = chipDefs.filter((x) => x.item).map((x) =>
      '<button type="button" class="t-chip role-' + x.role + '" data-jump="' + x.item.branchIdx + '">'
      + '<span>' + escH(x.item.name) + '（' + escH(x.item.branch) + '）</span><i>' + x.label + '</i></button>'
    ).join('');

    const groups = [
      { k: '主星', cls: 'major', list: p.majors },
      { k: '吉星', cls: 'lucky', list: p.lucky },
      { k: '煞星', cls: 'sha', list: p.sha },
      { k: '杂曜', cls: 'minor', list: p.minor },
    ].filter((g) => g.list && g.list.length);

    groupsEl.innerHTML = groups.length
      ? groups.map((g) =>
          '<div class="sg-box"><div class="sg-k">' + g.k + '</div><div class="sg-tags">'
          + g.list.map((s) => '<span class="s-pill ' + g.cls + '">' + escH(s) + '</span>').join('')
          + '</div></div>'
        ).join('')
      : '<div class="sg-box"><div class="sg-k">星曜</div><div class="empty-tip">' + escH(p.borrow || '本宫无主星') + '</div></div>';

    kvEl.innerHTML = [
      ['大限', p.daXian],
      ['小限', p.xiaoXian],
      ['十二神', p.shier || '—'],
    ].map(([k, v]) => '<div class="ikv-row"><i>' + k + '</i><span>' + escH(v) + '</span></div>').join('');

    chipsEl.querySelectorAll('[data-jump]').forEach((btn) => {
      btn.addEventListener('click', () => selectBranch(Number(btn.dataset.jump), true));
    });
  };

  let active = null;
  const selectBranch = (b, focusTab) => {
    if (b < 0 || b > 11) return;
    active = b;
    const opp = (b + 6) % 12;
    const t1 = (b + 4) % 12;
    const t2 = (b + 8) % 12;
    cells.forEach((el) => {
      const cb = Number(el.dataset.branch);
      el.classList.toggle('is-focus', cb === b);
      el.classList.toggle('is-opp', cb === opp);
      el.classList.toggle('is-trine', cb === t1 || cb === t2);
    });
    renderInspector(b, true);
    if (focusTab) switchTab('inspect');
  };

  const resetToMing = () => {
    active = null;
    cells.forEach((el) => el.classList.remove('is-focus', 'is-opp', 'is-trine'));
    renderInspector(data.mingBranch, false);
  };

  cells.forEach((el) => {
    const b = Number(el.dataset.branch);
    el.addEventListener('click', () => (active === b ? resetToMing() : selectBranch(b, true)));
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); active === b ? resetToMing() : selectBranch(b, true); }
    });
  });
  document.querySelectorAll('[data-jump]').forEach((btn) => {
    btn.addEventListener('click', () => selectBranch(Number(btn.dataset.jump), true));
  });
  if (clearBtn) clearBtn.addEventListener('click', resetToMing);

  // 默认在右侧展示命宫详览
  renderInspector(data.mingBranch, false);
})();
`;

export function renderChart({ chart, meta, liunian = null, patterns = [], title, footerNote }) {
  const palaceMap = {};
  for (const p of chart.palaces) palaceMap[p.branch] = p;
  const dxBranch = chart.currentDaXianIndex >= 0 ? chart.daXians[chart.currentDaXianIndex].palaceBranch : -1;
  const lyBranch = liunian && liunian.branch ? BRANCHES.indexOf(liunian.branch) : -1;

  const ctx = {
    chart, meta, liunian, patterns, palaceMap,
    mingBranch: chart.mingGongBranch,
    shenBranch: chart.shenGongBranch,
    dxBranch,
    lyBranch,
    title: title || (chart.birthInfo?.name ?? '') || '紫微斗数命盘',
  };

  const cells = Object.keys(GRID_POS).map((b) => palaceCell(ctx, Number(b))).join('');
  const interactiveJson = buildInteractiveData(ctx);

  return `<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(ctx.title)} · 紫微斗数命盘</title>
<style>${CSS}</style>
</head>
<body>
<div class="page">
  <header class="topbar">
    <div class="brand">
      ${ASTROLABE_EMBLEM}
      <div>
        <div class="brand-t">玄机 · 紫微斗数命盘</div>
        <div class="brand-sub">${esc(ctx.title)} · ${esc(chart.wuxingJuName)} · 命宫${esc(BRANCHES[chart.mingGongBranch])} · 身宫${esc(BRANCHES[chart.shenGongBranch])}</div>
      </div>
    </div>
    <div class="actions">
      <button type="button" class="btn" id="theme-toggle">宣纸印本</button>
      <button type="button" class="btn" id="print-btn">打印 / 存 PDF</button>
    </div>
  </header>

  <div class="workspace">
    <main class="sheet">
      <i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
      <div class="board-scroll">
        <div class="board-outer">
          ${gutters()}
          <div class="board">
            ${cells}
            ${centerPanel(ctx)}
          </div>
        </div>
      </div>
      <div class="ft">
        <span>${esc(footerNote ?? '本盘由 ziwei-paipan 本地推演生成，未联网、未上传任何数据')}</span>
        <span class="r">${esc(chart.wuxingJuName)} · 命宫${esc(BRANCHES[chart.mingGongBranch])}</span>
      </div>
    </main>

    ${sidePanel(ctx)}
  </div>
</div>
<script type="application/json" id="chart-data">${interactiveJson}</script>
<script>${SCRIPT}</script>
</body>
</html>`;
}
