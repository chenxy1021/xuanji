<script setup lang="ts">
import { marked } from 'marked'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AstrologyPanel from '@/components/chart/AstrologyPanel.vue'
import BaziChartPanel from '@/components/chart/BaziChart.vue'
import InterpretPanel from '@/components/chart/InterpretPanel.vue'
import KongmingPanel from '@/components/chart/KongmingPanel.vue'
import LiuyaoChartPanel from '@/components/chart/LiuyaoChart.vue'
import MbtiPanel from '@/components/chart/MbtiPanel.vue'
import MeihuaPanel from '@/components/chart/MeihuaPanel.vue'
import QimenPanel from '@/components/chart/QimenPanel.vue'
import SynastryChartPanel from '@/components/chart/SynastryChart.vue'
import TarotSpread from '@/components/chart/TarotSpread.vue'
import ZiweiChartPanel from '@/components/chart/ZiweiChart.vue'
import { hasBaziPillars, isAstrologyChart, isKongmingChart, isMbtiChart, isMeihuaChart, isQimenChart } from '@/api/chartKinds'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { getRecord } from '@/api/client'
import { t, useLocale } from '@/i18n'
import { systemNameById } from '@/i18n/terms'
import {
  isBaziChart,
  isLiuyaoChart,
  isSynastryChart,
  isTarotChart,
  isZiweiChart,
  type HistoryRecord,
} from '@/api/types'

const route = useRoute()
const charts = useChartsStore()
const auth = useAuthStore()

/** 标题有两类：「1990-05-15 四柱八字」与「孔明神卦 · 2026-11-20」，标题栏只留体系名 */
const heading = computed(() => {
  const raw = envelope.value?.title ?? ''
  const cleaned = raw
    .replace(/\d{4}-\d{2}-\d{2}/g, '')
    .replace(/\d{1,2}:\d{2}/g, '')
    .replace(/^[\s·,，-]+|[\s·,，-]+$/g, '')
  // 历史记录里的 title 是创建时语言写死的；按当前语言用体系 id 重新取名
  const byId = envelope.value?.system ? systemNameById(envelope.value.system) : null
  return byId ?? (cleaned || raw)
})

const routeId = computed(() => (typeof route.query.id === 'string' ? route.query.id : null))
const fetched = ref<HistoryRecord | null>(null)
const loadState = ref<'idle' | 'loading' | 'missing'>('idle')

const envelope = computed<HistoryRecord | null>(() => {
  const id = routeId.value
  if (!id) return charts.current
  return (
    charts.find(id) ??
    (!auth.isLoggedIn ? charts.findGuest(id) : null) ??
    (fetched.value?.id === id ? fetched.value : null)
  )
})

// 本地没有的 id（刷新、直链、换账号）按账号去服务端取；404/401/未登录统一显示「不存在或无权查看」
watch(
  routeId,
  async (id) => {
    fetched.value = null
    loadState.value = 'idle'
    if (!id || charts.find(id)) return
    await auth.bootstrap()
    if (!auth.isLoggedIn || id !== routeId.value) return
    loadState.value = 'loading'
    try {
      const record = await getRecord(id)
      if (id === routeId.value) fetched.value = record
    } catch {
      if (id === routeId.value) loadState.value = 'missing'
    } finally {
      if (id === routeId.value && loadState.value === 'loading') loadState.value = 'idle'
    }
  },
  { immediate: true },
)

const copyState = ref<'idle' | 'ok' | 'fail'>('idle')

async function copyText() {
  if (!envelope.value) return
  const raw = envelope.value.text
  try {
    await navigator.clipboard.writeText(masked.value ? maskBirthText(raw) : raw)
    copyState.value = 'ok'
  } catch {
    copyState.value = 'fail'
  }
  setTimeout(() => (copyState.value = 'idle'), 1500)
}

const locale = useLocale()
watch([envelope, locale], ([v]) => {
  const title = v ? systemNameById(v.system) ?? v.title : ''
  document.title = v ? t('result.pageTitleWith', { title }) : t('result.pageTitle')
}, { immediate: true })

const bazi = computed(() => (envelope.value && hasBaziPillars(envelope.value.chart) ? envelope.value.chart : null))
const astro = computed(() => (envelope.value && isAstrologyChart(envelope.value.chart) ? envelope.value.chart : null))
const ziwei = computed(() => (envelope.value && isZiweiChart(envelope.value.chart) ? envelope.value.chart : null))

/** 只有吃生辰的体系才有「隐藏生辰」；占卜/测评只给「修改信息」 */
const hasBirth = computed(() => {
  const input = envelope.value?.input as
    | { year?: unknown; datetime?: unknown; a?: { year?: unknown } }
    | undefined
  return typeof input?.year === 'number' || typeof input?.a?.year === 'number' || typeof input?.datetime === 'string'
})

const tab = ref<'analysis' | 'chat'>('analysis')
const masked = ref(false)
const boardOpen = ref(true)
// 手机上 sticky Tab 紧贴固定顶栏；切到 AI 时把 Tab 滚到顶部，避免正文从其下方穿过
watch(tab, (v) => {
  if (v !== 'chat' || window.innerWidth >= 1024) return
  requestAnimationFrame(() => document.querySelector('.result-tabs')?.scrollIntoView({ block: 'start' }))
})
const boardLabel = computed(() => heading.value)

/** text 的第一段正文（跳过标题与「输入」这类元信息段） */
const firstParagraph = computed(() => {
  const section = (envelope.value?.text ?? '')
    .split(/\n(?=## )/)
    .find((b) => /^##\s*核心论断/m.test(b))
  const body = (section ?? '').replace(/^##[^\n]*\n/, '')
  for (const line of body.split('\n')) {
    if (/^#|^\||^-|^\s*$/.test(line)) continue
    return line.replace(/\*\*/g, '').trim()
  }
  return ''
})
const tune = computed(() => {
  const line = firstParagraph.value.split(/(?<=[。！？.!?])/)[0]?.trim() ?? ''
  return masked.value ? maskBirthText(line) : line
})

// 「## 输入」这类纯元信息段不进长文；首个标题改成一级，避免与页面 h2 撞级
const textBlock = computed(() =>
  (envelope.value?.text ?? '')
    .split(/\n(?=## )/)
    .filter((b) => !/^##[^\n]*(输入|Input)/m.test(b))
    .filter((b) => !/^##[^\n]*\n-\s*(阳历|Solar)\b/m.test(b))
    .join('\n')
    .replace(/^## /, '# '),
)

/** 隐藏生辰时，长文里后端自带的日期/时刻/出生地也要一并打码，避免右栏泄露 */
function maskBirthText(raw: string) {
  const input = envelope.value?.input as
    | { year?: number; month?: number; day?: number; place?: { name?: string } | null }
    | undefined
  const place = input?.place?.name
  let out = raw
    .replace(/\d{4}-\d{1,2}-\d{1,2}/g, '••••-••-••')
    .replace(/\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日/g, '••••年••月••日')
    .replace(/\d{1,2}:\d{2}/g, '••:••')
  if (place) out = out.split(place).join('••••')
  return out
}

const textHtml = computed(() => {
  if (!textBlock.value) return ''
  const source = masked.value ? maskBirthText(textBlock.value) : textBlock.value
  return marked.parse(source, { async: false }) as string
})

const readingMeta = computed(() => {
  const n = textBlock.value.replace(/[#*|>\-\s]/g, '').length
  if (!n) return ''
  return t('result.readingMeta', { n, m: Math.max(1, Math.round(n / 350)) })
})

const WX: Record<string, 'mu' | 'huo' | 'tu' | 'jin' | 'shui'> = {
  甲: 'mu', 乙: 'mu', 寅: 'mu', 卯: 'mu',
  丙: 'huo', 丁: 'huo', 巳: 'huo', 午: 'huo',
  戊: 'tu', 己: 'tu', 辰: 'tu', 戌: 'tu', 丑: 'tu', 未: 'tu',
  庚: 'jin', 辛: 'jin', 申: 'jin', 酉: 'jin',
  壬: 'shui', 癸: 'shui', 亥: 'shui', 子: 'shui',
}
const WX_ORDER = ['mu', 'huo', 'tu', 'jin', 'shui'] as const
const WX_LABEL: Record<string, string> = { mu: '木', huo: '火', tu: '土', jin: '金', shui: '水' }

// 八字：四柱八个干支的五行计数（真实盘面数据，不是打分）
const stemDist = computed(() => {
  if (!bazi.value) return null
  const count: Record<string, number> = {}
  for (const p of Object.values(bazi.value.pillars)) {
    for (const ch of [p.gan, p.zhi]) {
      const k = WX[ch]
      if (k) count[WX_LABEL[k]] = (count[WX_LABEL[k]] ?? 0) + 1
    }
  }
  return distRows(count, WX_ORDER.map((k) => WX_LABEL[k]))
})

const KEYS = { 木: 'mu', 火: 'huo', 土: 'tu', 金: 'jin', 水: 'shui' } as const
const ELEMENT_KEYS = { 火: 'huo', 土: 'tu', 风: 'jin', 水: 'shui' } as const
const MODE_KEYS = { 基本: 'huo', 固定: 'tu', 变动: 'jin' } as const

function distRows(count: Record<string, number>, order: string[]) {
  const total = Object.values(count).reduce((a, b) => a + b, 0)
  return order.map((label) => {
    const n = count[label] ?? 0
    return { label, n, pct: total ? Math.round((n / total) * 100) : 0 }
  })
}

const metaSep = computed(() => (locale.value === 'en' ? ', ' : '，'))

/** 标题下的一句盘面摘要：只拼真实字段，不做吉凶判断 */
const summaryLine = computed(() => {
  const e = envelope.value
  if (!e) return ''
  const c = e.chart
  if (bazi.value) {
    const dayGan = bazi.value.pillars.day?.gan ?? ''
    const dayEl = WX_LABEL[WX[dayGan]] ?? ''
    const dist = stemDist.value
    const counts = dist ? dist.map((r) => `${r.label}${r.n}`).join(' ') : ''
    return [dayGan ? `${dayGan}${dayEl}日主` : '', counts].filter(Boolean).join(metaSep.value)
  }
  if (astro.value) {
    const a = astro.value
    const parts = [a.sun?.sign ? `太阳${a.sun.sign}` : '', a.moon?.sign ? `月亮${a.moon.sign}` : '', a.rising?.sign ? `上升${a.rising.sign}` : '']
    return parts.filter(Boolean).join(metaSep.value)
  }
  if (ziwei.value) {
    const ming = ziwei.value.palaces.find((p) => p.is_ming)
    const majors = ming?.stars.filter((s) => s.kind === 'major').map((s) => s.name) ?? []
    return [ming ? `命宫 ${ming.branch}` : '', ziwei.value.bureau, majors.length ? `主星 ${majors.join('、')}` : '']
      .filter(Boolean)
      .join(metaSep.value)
  }
  if (isQimenChart(c)) {
    const anchors = c.lifelong?.anchors ?? []
    return anchors.map((x) => `${x.label} ${x.ganzhi}`).join(metaSep.value)
  }
  if (isSynastryChart(c)) return `合盘 ${c.score} 分${metaSep.value}${c.level}`
  if (isTarotChart(c)) {
    const names = c.cards.slice(0, 3).map((x) => `${x.position}${x.name}`).join(metaSep.value)
    return [c.spread_name, names].filter(Boolean).join(metaSep.value)
  }
  if (isLiuyaoChart(c)) {
    const moving = c.moving_lines?.length ? `动爻 ${c.moving_lines.join('、')}` : '静卦'
    return `本卦 ${c.ben_gua.name}${metaSep.value}${moving}`
  }
  if (isMeihuaChart(c)) {
    const ben = c.ben ?? c.ben_gua
    const rel = typeof c.relation === 'string' ? c.relation : c.relation?.name
    return [ben?.name ? `本卦 ${ben.name}` : '', rel].filter(Boolean).join(metaSep.value)
  }
  if (isKongmingChart(c)) return `第 ${c.lot.number} 签${metaSep.value}${c.lot.level}${metaSep.value}${c.lot.hexagram}`
  if (isMbtiChart(c)) return `${c.type}${metaSep.value}${c.name}`
  return ''
})

const astroElements = computed(() =>
  astro.value ? distRows(astro.value.balance?.elements ?? {}, Object.keys(ELEMENT_KEYS)) : null,
)
const astroModes = computed(() =>
  astro.value ? distRows(astro.value.balance?.modes ?? {}, Object.keys(MODE_KEYS)) : null,
)
const distColor = (label: string) => `var(--color-${KEYS[label as keyof typeof KEYS] ?? ELEMENT_KEYS[label as keyof typeof ELEMENT_KEYS] ?? MODE_KEYS[label as keyof typeof MODE_KEYS] ?? 'primary'})`

interface Fact {
  label: string
  value: string
  hint?: string
}

/** 盘面要点：只取真实字段，越短越好；没有数据就少一张卡 */
const facts = computed<Fact[]>(() => {
  const e = envelope.value
  if (!e) return []
  const c = e.chart

  if (isBaziChart(c)) {
    const p = c.pillars
    const dayGan = p.day?.gan ?? ''
    const dayEl = WX_LABEL[WX[dayGan]] ?? ''
    const monthZhi = p.month?.zhi ?? ''
    const monthEl = WX_LABEL[WX[monthZhi]] ?? ''
    const counts = stemDist.value?.map((r) => `${r.label}${r.n}`).join(' ') ?? ''
    const total = stemDist.value?.reduce((a, r) => a + r.n, 0) ?? 0
    return [
      { label: t('fact.dayMaster'), value: `${dayGan}${dayEl}` || '—', hint: `${p.day?.zhi ?? ''} · ${t('fact.dayBranch')}` },
      { label: t('fact.monthBranch'), value: `${monthZhi}${monthEl}` || '—', hint: p.month?.shishen ?? '' },
      { label: t('fact.elements'), value: counts || '—', hint: t('fact.chars', { n: total }) },
      {
        label: t('fact.luckStart'),
        value: c.qiyun || '—',
        hint: c.forward ? t('fact.forward') : t('fact.backward'),
      },
    ]
  }

  if (ziwei.value) {
    const z = ziwei.value
    const ming = z.palaces.find((p) => p.is_ming)
    const majors = ming?.stars.filter((s) => s.kind === 'major').map((s) => s.name) ?? []
    const hua = ming?.stars.filter((s) => s.sihua).map((s) => `${s.name}化${s.sihua}`).join(' ') ?? ''
    const decade = z.current_decade
    return [
      {
        label: t('fact.mingPalace'),
        value: ming ? `${ming.stem}${ming.branch}` : z.ming_gong,
        hint: `${t('fact.shenPalace')} ${z.shen_gong}`,
      },
      { label: t('fact.bureau'), value: z.bureau, hint: t('fact.nominalAge', { n: z.current_age }) },
      { label: t('fact.mingStars'), value: majors.join('、') || t('fact.noMajor'), hint: hua || undefined },
      {
        label: t('fact.currentDecade'),
        value: decade ? `${decade.start_age}–${decade.end_age}` : '—',
        hint: decade?.palace ?? '',
      },
    ]
  }

  if (astro.value) {
    const a = astro.value
    const topElement = [...(astroElements.value ?? [])].sort((x, y) => y.n - x.n)[0]
    const topMode = [...(astroModes.value ?? [])].sort((x, y) => y.n - x.n)[0]
    const point = (p?: { sign?: string; degree_in_sign?: number } | null) =>
      p?.sign ? `${p.sign} ${Math.round(p.degree_in_sign ?? 0)}°` : '—'
    return [
      { label: t('fact.sun'), value: point(a.sun), hint: [a.sun?.element, a.sun?.mode].filter(Boolean).join(' · ') },
      { label: t('fact.moon'), value: point(a.moon), hint: [a.moon?.element, a.moon?.mode].filter(Boolean).join(' · ') },
      { label: t('fact.rising'), value: point(a.rising), hint: a.rising ? t('fact.mingStart') : t('fact.notRising') },
      {
        label: t('fact.dominantElement'),
        value: topElement ? `${topElement.label} ${topElement.n}` : '—',
        hint: topMode ? `${topMode.label} ${topMode.n}` : '',
      },
    ]
  }

  if (isQimenChart(c)) {
    return (c.lifelong?.anchors ?? []).map((x) => ({
      label: x.label,
      value: x.ganzhi,
      hint: x.palace ? `${x.palace.trigram} · ${x.palace.direction}` : x.role,
    }))
  }

  if (isSynastryChart(c)) {
    return [
      { label: t('fact.score'), value: String(c.score), hint: c.level },
      { label: t('fact.level'), value: c.level, hint: c.advice.length ? t('fact.advice', { n: c.advice.length }) : '' },
      {
        label: t('fact.matches'),
        value: String(c.matches.length),
        hint: c.complement?.length ? t('fact.complement', { n: c.complement.length }) : '',
      },
    ]
  }

  if (isTarotChart(c)) {
    return [
      { label: t('fact.spread'), value: c.spread_name, hint: c.spread },
      { label: t('fact.cards'), value: String(c.cards.length), hint: c.cards[0]?.position ?? '' },
      {
        label: t('fact.seed'),
        value: c.seed == null ? '—' : String(c.seed),
        hint: c.seed == null ? t('fact.unseeded') : t('fact.reproducible'),
      },
    ]
  }

  if (isLiuyaoChart(c)) {
    return [
      { label: t('fact.benGua'), value: c.ben_gua.name, hint: c.ben_gua.palace },
      { label: t('fact.bianGua'), value: c.bian_gua?.name ?? t('fact.noChange'), hint: c.bian_gua?.palace ?? '' },
      {
        label: t('fact.movingLines'),
        value: c.moving_lines.length ? c.moving_lines.join('、') : t('fact.static'),
        hint: t('fact.dayZhi', { zhi: c.day_gan_zhi }),
      },
    ]
  }

  if (isMeihuaChart(c)) {
    const ben = c.ben ?? c.ben_gua
    const bian = c.bian ?? c.bian_gua
    const rel = typeof c.relation === 'string' ? c.relation : c.relation?.name
    return [
      { label: t('fact.benGua'), value: ben?.name ?? '—', hint: ben?.yixiang ?? '' },
      { label: t('fact.bianGua'), value: bian?.name ?? '—', hint: c.moving_line_name ?? '' },
      { label: t('fact.tiYong'), value: rel ?? '—', hint: c.judgement ?? '' },
    ]
  }

  if (isKongmingChart(c)) {
    return [
      { label: t('fact.lotNumber'), value: `第 ${c.lot.number} 签`, hint: c.lot.palace },
      { label: t('fact.lotLevel'), value: c.lot.level, hint: c.lot.fortune },
      { label: t('fact.hexagram'), value: c.lot.hexagram, hint: c.lot.changed },
    ]
  }

  if (isMbtiChart(c)) {
    return [
      { label: t('fact.mbtiType'), value: c.type, hint: t('fact.answered', { n: c.answered }) },
      { label: t('fact.mbtiName'), value: c.name, hint: c.fit },
      { label: t('fact.mbtiDominant'), value: c.dimensions.map((d) => d.dominant).slice(0, 2).join(' · '), hint: c.strengths[0] ?? '' },
    ]
  }

  return []
})

const seal = computed(() => {
  const s = envelope.value?.system ?? ''
  if (s.endsWith('_hepan')) return '合'
  if (s === 'mbti') return '测'
  if (['liuyao', 'tarot', 'meihua', 'kongming'].includes(s)) return '卜'
  return '命'
})

const sealLabel = computed(() => (envelope.value?.system === 'mbti' ? 'MBTI' : categoryLabel.value))

const categoryKey = computed(() => {
  const s = envelope.value?.system ?? ''
  if (s.endsWith('_hepan')) return 'synastry' as const
  if (s === 'mbti') return 'fun' as const
  if (['liuyao', 'tarot', 'meihua', 'kongming'].includes(s)) return 'divination' as const
  return 'chart' as const
})

const categoryLabel = computed(() => {
  switch (categoryKey.value) {
    case 'synastry':
      return t('cat.synastry')
    case 'fun':
      return t('cat.fun')
    case 'divination':
      return t('cat.divination')
    default:
      return t('cat.chart')
  }
})


const hasRisk = computed(() => (envelope.value?.warnings.length ?? 0) > 0)
const anchors = computed(() => [
  { id: 'r-tune', label: t('result.tune'), on: !!tune.value },
  { id: 'r-dist', label: t('result.distTitle'), on: !!(stemDist.value || astroElements.value) },
  { id: 'r-reading', label: t('result.reading'), on: !!textHtml.value },
  { id: 'r-risk', label: t('result.risk'), on: hasRisk.value },
].filter((a) => a.on))
const useTabs = computed(() => anchors.value.length >= 3)

const bornLine = computed(() => {
  const e = envelope.value
  if (!e) return ''
  const input = e.input as { year?: number; month?: number; day?: number; hour?: number | null; minute?: number | null; gender?: string; place?: { name?: string } | null; true_solar_time?: boolean; datetime?: string }
  // 奇门等体系只回传 datetime 字符串
  const date = typeof input?.datetime === 'string'
    ? input.datetime
    : typeof input?.year === 'number'
      ? `${input.year}-${String(input.month).padStart(2, '0')}-${String(input.day).padStart(2, '0')}`
      : ''
  const time = typeof input?.datetime === 'string'
    ? ''
    : typeof input?.hour === 'number'
      ? ` ${String(input.hour).padStart(2, '0')}:${String(input.minute ?? 0).padStart(2, '0')}`
      : ''
  const parts = [date + time, input?.place?.name, input?.gender === 'male' ? t('birth.male') : input?.gender === 'female' ? t('birth.female') : '']
  return parts.filter(Boolean).join(metaSep.value)
})

function jump(id: string) {
  tab.value = 'analysis'
  requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}
</script>

<template>
  <div v-if="envelope" class="space-y-6 lg:space-y-10">
    <div class="flex min-h-11 items-center justify-between gap-2 border-b border-line pb-4">
      <div class="flex min-w-0 items-center gap-1">
      <RouterLink to="/" class="-ml-2.5 flex size-11 items-center justify-center text-ink-2 lg:hidden" :aria-label="t('result.backAria')">
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m15 5-7 7 7 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </RouterLink>
      <h1 class="min-w-0 flex-1 truncate title-serif text-[20px] lg:text-[15px] lg:text-ink-2">{{ heading }}</h1>
      </div>
      <div class="flex items-center gap-1 text-xs text-muted">
        <span class="max-md:hidden">{{ envelope.engine_version }}</span>
        <button type="button" class="let-action text-xs" @click="copyText">
          {{ copyState === 'ok' ? t('result.copied') : copyState === 'fail' ? t('result.copyFail') : t('result.copy') }}
        </button>
      </div>
    </div>

    <div class="result-grid">
      <!-- 左栏：盘面 + 周期 -->
      <aside class="result-side min-w-0">
        <button
          type="button"
          data-board-toggle
          class="mb-3 flex min-h-11 w-full items-center justify-between border-b border-line px-1 text-[13px] text-ink-2 lg:hidden"
          :aria-expanded="boardOpen"
          @click="boardOpen = !boardOpen"
        >
          <span>{{ t('result.board') }} / {{ boardLabel }}</span>
          <span class="text-muted">{{ boardOpen ? t('result.collapseBoard') : t('result.expandBoard') }}</span>
        </button>
        <div class="space-y-4" :class="boardOpen ? 'block' : 'hidden lg:block'">
          <p v-if="masked" class="label">{{ t('result.masked') }}</p>
          <template v-else>
            <BaziChartPanel v-if="isBaziChart(envelope.chart)" :chart="envelope.chart" />
            <ZiweiChartPanel v-else-if="isZiweiChart(envelope.chart)" :chart="envelope.chart" />
            <AstrologyPanel v-else-if="isAstrologyChart(envelope.chart)" :chart="envelope.chart" />
            <TarotSpread v-else-if="isTarotChart(envelope.chart)" :chart="envelope.chart" />
            <LiuyaoChartPanel v-else-if="isLiuyaoChart(envelope.chart)" :chart="envelope.chart" />
            <SynastryChartPanel
              v-else-if="isSynastryChart(envelope.chart)"
              :chart="envelope.chart"
              :kind="envelope.system === 'ziwei_hepan' ? 'ziwei' : 'bazi'"
            />
            <MbtiPanel v-else-if="isMbtiChart(envelope.chart)" :chart="envelope.chart" />
            <QimenPanel v-else-if="isQimenChart(envelope.chart)" :chart="envelope.chart" />
            <MeihuaPanel v-else-if="isMeihuaChart(envelope.chart)" :chart="envelope.chart" />
            <KongmingPanel v-else-if="isKongmingChart(envelope.chart)" :chart="envelope.chart" />
            <section v-else class="scroll-x border-t border-line pt-3">
              <pre class="text-xs">{{ JSON.stringify(envelope.chart, null, 2) }}</pre>
            </section>
          </template>

        </div>

        <div class="mt-5 flex flex-wrap gap-2 border-t border-line pt-5">
          <RouterLink :to="`/chart/${envelope.system}`" class="btn-line">
            {{ hasBirth ? t('stage.modify') : t('stage.modifyOptions') }}
          </RouterLink>
          <button v-if="hasBirth" type="button" class="btn-line" :aria-pressed="masked" @click="masked = !masked">
            {{ masked ? t('stage.unmask') : t('stage.mask') }}
          </button>
          <RouterLink :to="`/chart/${envelope.system}`" class="btn-line" @click="charts.current = null">{{ t('stage.restart') }}</RouterLink>
        </div>
      </aside>

      <!-- 右栏：分析 / AI -->
      <div class="min-w-0">
        <!-- 盘头：标题 + 关键事实 -->
        <header class="result-hero" data-result-hero>
          <div class="flex items-start justify-between gap-5">
            <div class="min-w-0">
              <h2 class="title-serif mt-3 text-[30px] leading-[1.25] sm:text-[36px] lg:text-[42px]" data-result-title>{{ heading }}</h2>
              <p v-if="summaryLine" class="tabular mt-3 max-w-[62ch] text-[13px] leading-[1.8] text-ink-2">{{ summaryLine }}</p>
              <p v-if="bornLine && !masked" class="tabular mt-1 text-[12px] leading-[1.8] text-muted">{{ bornLine }}</p>
            </div>
            <div class="result-seal" aria-hidden="true">
              <span>{{ seal }}</span>
              <small>{{ sealLabel }}</small>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line pt-3 text-[13px] text-muted">
            <span class="tabular">{{ envelope.engine_version }}</span>
            <span v-if="envelope.warnings.length" class="text-accent">{{ t('result.warnings') }} {{ envelope.warnings.length }}</span>
          </div>
        </header>

        <!-- 分段：文字 + 细下划线 -->
        <div class="result-tabs">
          <div class="result-tabs__track" role="tablist" :aria-label="t('result.tabAnalysis')">
            <button
              type="button"
              class="result-tabs__btn"
              :class="{ 'is-on': tab === 'analysis' }"
              :aria-pressed="tab === 'analysis'"
              @click="tab = 'analysis'"
            >
              {{ t('result.tabAnalysis') }}
            </button>
            <button
              type="button"
              class="result-tabs__btn"
              :class="{ 'is-on': tab === 'chat' }"
              :aria-pressed="tab === 'chat'"
              @click="tab = 'chat'"
            >
              {{ t('result.tabChat') }}
            </button>
          </div>
          <span class="result-tabs__hint">{{ t('result.aiHint') }}</span>
        </div>

        <div v-show="tab === 'analysis'" class="space-y-9 pb-4" :class="tab === 'analysis' ? 'panel-visible' : ''">
          <!-- 盘面要点 -->
          <section v-if="facts.length" data-result-facts>
            <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h3 class="label">{{ t('result.facts') }}</h3>
              <span class="text-[13px] text-muted">{{ t('result.factsNote') }}</span>
            </div>
            <div class="fact-grid">
              <article
                v-for="f in facts"
                :key="f.label + f.value"
                class="fact-card"
              >
                <p class="fact-card__label">{{ f.label }}</p>
                <p class="fact-card__value">{{ f.value }}</p>
                <p v-if="f.hint" class="fact-card__hint">{{ f.hint }}</p>
              </article>
            </div>
          </section>

          <!-- 定调 -->
          <blockquote v-if="tune" id="r-tune" class="pull-quote result-quote scroll-mt-32">{{ tune }}</blockquote>

          <div v-if="useTabs" class="result-anchors">
            <button
              v-for="a in anchors"
              :key="a.id"
              type="button"
              class="result-anchor"
              @click="jump(a.id)"
            >
              {{ a.label }}
            </button>
          </div>

          <!-- 分布 -->
          <section v-if="stemDist || astroElements" id="r-dist" class="scroll-mt-32">
            <div class="mb-5 flex flex-wrap items-baseline justify-between gap-3">
              <h3 class="title-serif text-[22px]">{{ t('result.distTitle') }}</h3>
              <span class="text-[13px] text-muted">{{ t('result.distNote') }}</span>
            </div>
            <div v-if="stemDist" class="mb-6">
              <p class="label mb-3">{{ t('result.stemZhi') }}</p>
              <ul class="space-y-3">
                <li v-for="(r, i) in stemDist" :key="r.label" class="grid grid-cols-[2rem_1fr_4.75rem] items-center gap-3">
                  <span class="font-serif text-[16px]" :style="{ color: distColor(r.label) }">{{ r.label }}</span>
                  <span class="bar-track">
                    <span
                      class="bar-fill"
                      :style="{ width: `${r.pct}%`, background: distColor(r.label), animationDelay: `${i * 80}ms` }"
                    />
                  </span>
                  <span class="tabular text-right text-[12px] text-muted">{{ r.n }} · {{ r.pct }}%</span>
                </li>
              </ul>
            </div>
            <div v-if="astroElements" class="grid gap-6 sm:grid-cols-2">
              <div>
                <p class="label mb-3">{{ t('result.elements') }}</p>
                <ul class="space-y-3">
                  <li v-for="(r, i) in astroElements" :key="r.label" class="grid grid-cols-[2rem_1fr_4.75rem] items-center gap-3">
                    <span class="font-serif text-[16px]" :style="{ color: distColor(r.label) }">{{ r.label }}</span>
                    <span class="bar-track">
                      <span
                        class="bar-fill"
                        :style="{ width: `${r.pct}%`, background: distColor(r.label), animationDelay: `${i * 80}ms` }"
                      />
                    </span>
                    <span class="tabular text-right text-[12px] text-muted">{{ r.n }} · {{ r.pct }}%</span>
                  </li>
                </ul>
              </div>
              <div>
                <p class="label mb-3">{{ t('result.modes') }}</p>
                <ul class="space-y-3">
                  <li v-for="(r, i) in astroModes ?? []" :key="r.label" class="grid grid-cols-[2rem_1fr_4.75rem] items-center gap-3">
                    <span class="font-serif text-[16px]" :style="{ color: distColor(r.label) }">{{ r.label }}</span>
                    <span class="bar-track">
                      <span
                        class="bar-fill"
                        :style="{ width: `${r.pct}%`, background: distColor(r.label), animationDelay: `${i * 80}ms` }"
                      />
                    </span>
                    <span class="tabular text-right text-[12px] text-muted">{{ r.n }} · {{ r.pct }}%</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <!-- 长文 -->
          <section v-if="textHtml" id="r-reading" class="scroll-mt-32">
            <div class="mb-4 flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-3">
              <h3 class="title-serif text-[22px]">{{ t('result.longTitle') }}</h3>
              <span v-if="readingMeta" class="tabular text-[13px] text-muted">{{ readingMeta }}</span>
            </div>
            <div class="prose-read" v-html="textHtml" />
          </section>
          <p v-else class="text-sm text-muted">{{ t('result.noText') }}</p>

          <!-- 风险 -->
          <div
            v-if="envelope.warnings.length"
            id="r-risk"
            class="risk-card scroll-mt-32 flex gap-3 text-[13px] leading-[1.8] text-accent"
          >
            <span class="label shrink-0 !text-accent">{{ t('result.warnings') }}</span>
            <ul class="space-y-1">
              <li v-for="w in envelope.warnings" :key="w">{{ w }}</li>
            </ul>
          </div>
        </div>

        <div v-show="tab === 'chat'" class="result-chat" :class="tab === 'chat' ? 'panel-visible' : ''">
          <InterpretPanel :record-id="envelope.id" :system="envelope.system" :chart="envelope.chart" :text="envelope.text" />
        </div>
      </div>
    </div>
  </div>
  <p v-else-if="loadState === 'loading' || !auth.ready" class="animate-pulse py-16 text-center text-sm text-muted">{{ t('common.loading') }}</p>
  <div v-else class="border-t border-line px-4 py-12 text-center" data-result-missing>
    <svg viewBox="0 0 24 24" class="mx-auto size-12 text-muted opacity-20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6M12 16.5v.5" stroke-linecap="round" />
    </svg>
    <p class="mt-3 text-sm text-muted">{{ routeId ? t('result.notFound') : t('result.empty') }}</p>
    <RouterLink :to="routeId ? '/history' : '/'" class="btn-ghost mt-1">{{ routeId ? t('history.title') : t('result.backHome') }}</RouterLink>
  </div>
</template>
