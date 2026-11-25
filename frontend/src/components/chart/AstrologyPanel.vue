<script setup lang="ts">
import { computed } from 'vue'
import type { AstrologyChart } from '@/api/chartKinds'

const props = defineProps<{ chart: AstrologyChart }>()

const SIGNS = ['白羊', '金牛', '双子', '巨蟹', '狮子', '处女', '天秤', '天蝎', '射手', '摩羯', '水瓶', '双鱼']
const SIGN_ELEMENT: Record<string, string> = {
  白羊: '火', 金牛: '土', 双子: '风', 巨蟹: '水',
  狮子: '火', 处女: '土', 天秤: '风', 天蝎: '水',
  射手: '火', 摩羯: '土', 水瓶: '风', 双鱼: '水',
}
const ABBR: Record<string, string> = {
  太阳: '日', 月亮: '月', 水星: '水', 金星: '金', 火星: '火',
  木星: '木', 土星: '土', 天王星: '天', 海王星: '海', 冥王星: '冥',
}
const ELEMENT_CLASS: Record<string, string> = {
  火: 'text-huo', 土: 'text-tu', 风: 'text-jin', 水: 'text-shui',
}
const ELEMENT_FILL: Record<string, string> = {
  火: 'var(--color-huo)', 土: 'var(--color-tu)', 风: 'var(--color-jin)', 水: 'var(--color-shui)',
}
const ASPECT_COLOR: Record<string, string> = {
  合相: 'var(--color-text-muted)',
  三分相: 'var(--color-primary)',
  六分相: 'var(--color-primary)',
  四分相: 'var(--color-accent)',
  对冲: 'var(--color-accent)',
}

/** 把「星座 + 座内度数」换成黄道经度，用于盘面定位 */
function longitude(sign?: string, degree?: number) {
  const idx = sign ? SIGNS.indexOf(sign) : -1
  return idx >= 0 ? idx * 30 + (degree ?? 0) : 0
}

const ascLon = computed(() => longitude(props.chart.rising?.sign, props.chart.rising?.degree_in_sign))
const mcLon = computed(() => longitude(props.chart.mc?.sign, props.chart.mc?.degree_in_sign))

const CX = 160
const CY = 160
const R_OUTER = 148
const R_INNER = 127
const R_PLANET = 104
const R_ASPECT = 86

/** 上升点固定在左侧，经度递增逆时针排布 */
function theta(lon: number) {
  return (180 - (lon - ascLon.value)) * (Math.PI / 180)
}
function pointAt(lon: number, r: number) {
  const t = theta(lon)
  return { x: CX + r * Math.cos(t), y: CY + r * Math.sin(t) }
}

const signTicks = computed(() =>
  SIGNS.flatMap((sign, i) => {
    const a = pointAt(i * 30, R_OUTER)
    const b = pointAt(i * 30, R_INNER)
    const c = pointAt(i * 30 + 15, (R_OUTER + R_INNER) / 2)
    return [{ sign, element: SIGN_ELEMENT[sign], line: [a, b], label: c }]
  }),
)

interface WheelPlanet {
  name: string
  abbr: string
  sign: string
  lon: number
  x: number
  y: number
  labelX: number
  labelY: number
  retrograde: boolean
}

/** 相近经度的行星往外叠一层，避免字叠在一起 */
const wheelPlanets = computed<WheelPlanet[]>(() => {
  const list = props.chart.planets.map((p) => ({
    p,
    lon: typeof p.longitude === 'number' ? p.longitude : longitude(p.sign, p.degree_in_sign),
  }))
  const order = [...list].sort((a, b) => theta(a.lon) - theta(b.lon))
  const placed: { th: number; level: number }[] = []
  return order.map(({ p, lon }) => {
    const th = theta(lon)
    let level = 0
    while (placed.some((q) => q.level === level && Math.abs(q.th - th) < 0.23)) level += 1
    placed.push({ th, level })
    const r = Math.max(56, R_PLANET - level * 15)
    const at = pointAt(lon, r)
    const label = pointAt(lon, r + 9)
    return {
      name: p.name,
      abbr: ABBR[p.name] ?? p.name,
      sign: p.sign,
      lon,
      x: at.x,
      y: at.y,
      labelX: label.x,
      labelY: label.y,
      retrograde: !!p.retrograde,
    }
  })
})

interface Chord {
  key: string
  from: { x: number; y: number }
  to: { x: number; y: number }
  color: string
}

const chords = computed<Chord[]>(() => {
  const out: Chord[] = []
  for (const a of props.chart.aspects) {
    if ((a.orb ?? 9) > 3 || out.length >= 14) continue
    const pa = props.chart.planets.find((p) => p.name === a.a)
    const pb = props.chart.planets.find((p) => p.name === a.b)
    if (!pa || !pb) continue
    const la = typeof pa.longitude === 'number' ? pa.longitude : longitude(pa.sign, pa.degree_in_sign)
    const lb = typeof pb.longitude === 'number' ? pb.longitude : longitude(pb.sign, pb.degree_in_sign)
    out.push({
      key: `${a.a}-${a.b}-${a.type}`,
      from: pointAt(la, R_ASPECT),
      to: pointAt(lb, R_ASPECT),
      color: ASPECT_COLOR[a.type] ?? 'var(--color-text-muted)',
    })
  }
  return out
})

const hasAngles = computed(() => !!props.chart.rising)
const ascMark = computed(() => {
  if (!hasAngles.value) return null
  const a = pointAt(ascLon.value, R_OUTER)
  const b = pointAt(ascLon.value, R_INNER)
  const label = pointAt(ascLon.value, R_INNER - 14)
  return { a, b, label }
})
const mcMark = computed(() => {
  if (!props.chart.mc) return null
  const a = pointAt(mcLon.value, R_INNER)
  const b = pointAt(mcLon.value, R_ASPECT)
  return { a, b }
})

const bigThree = computed(() => {
  const items = [
    { label: '太阳', sign: props.chart.sun?.sign, degree: props.chart.sun?.degree_in_sign, note: [props.chart.sun?.element, props.chart.sun?.mode].filter(Boolean).join(' · ') },
    { label: '月亮', sign: props.chart.moon?.sign, degree: props.chart.moon?.degree_in_sign, note: [props.chart.moon?.element, props.chart.moon?.mode].filter(Boolean).join(' · ') },
  ]
  if (props.chart.rising) {
    items.push({ label: '上升', sign: props.chart.rising.sign, degree: props.chart.rising.degree_in_sign, note: '命宫起点' })
  }
  if (props.chart.mc) {
    items.push({ label: '天顶', sign: props.chart.mc.sign, degree: props.chart.mc.degree_in_sign, note: '事业方向' })
  }
  return items
})

const elements = computed(() => {
  const balance = props.chart.balance?.elements ?? {}
  const total = Object.values(balance).reduce((sum, n) => sum + (n || 0), 0) || 1
  return ['火', '土', '风', '水'].map((key) => ({
    key,
    count: balance[key] ?? 0,
    pct: Math.round(((balance[key] ?? 0) / total) * 100),
  }))
})
const modes = computed(() => {
  const balance = props.chart.balance?.modes ?? {}
  const total = Object.values(balance).reduce((sum, n) => sum + (n || 0), 0) || 1
  return ['基本', '固定', '变动'].map((key) => ({
    key,
    count: balance[key] ?? 0,
    pct: Math.round(((balance[key] ?? 0) / total) * 100),
  }))
})

function fmtDegree(deg?: number) {
  if (typeof deg !== 'number') return '—'
  return `${Number(deg.toFixed(2))}°`
}
function signClass(sign?: string) {
  return ELEMENT_CLASS[SIGN_ELEMENT[sign ?? ''] ?? ''] ?? 'text-ink'
}
</script>

<template>
  <div
    class="space-y-3"
    :data-astrology="chart.rising?.sign ?? 'none'"
    :data-ascendant="chart.rising?.sign ?? ''"
    :data-aspects="chart.aspects.length"
  >
    <section class="border-t border-line-strong pt-3">
      <div class="flex items-baseline justify-between gap-2">
        <p class="font-serif text-[20px]">{{ chart.rising ? `${chart.rising.sign}上升` : '本命盘' }}</p>
        <span class="chip shrink-0">{{ chart.zodiac }}</span>
      </div>
      <p class="mt-2 text-[13px] leading-[1.6] text-muted">
        {{ chart.local_time }} 出生<template v-if="chart.place"><span class="mx-1">·</span>{{ chart.place }}</template>
        <br />
        UTC {{ chart.utc_time }}<span class="mx-1">·</span>{{ chart.house_system }}分宫制
      </p>
      <p v-if="!hasAngles" class="mt-1.5 text-[13px] leading-[1.6] text-warning">
        本次未算出上升与宫位（缺出生地/时刻，或出生地纬度过高），行星落座与相位仍可参考。
      </p>
    </section>

    <section class="grid grid-cols-2 gap-x-4">
      <article
        v-for="item in bigThree"
        :key="item.label"
        class="border-t border-line py-2.5"
      >
        <p class="text-[13px] text-muted">{{ item.label }}</p>
        <p class="mt-0.5 font-serif text-[19px] leading-tight" :class="signClass(item.sign)">
          {{ item.sign || '—' }}
          <span class="tabular text-[13px] text-muted">{{ fmtDegree(item.degree) }}</span>
        </p>
        <p v-if="item.note" class="mt-1 text-[12px] text-muted">{{ item.note }}</p>
      </article>
    </section>

    <section class="border-t border-line pt-3">
      <svg viewBox="0 0 320 320" class="mx-auto block w-full max-w-[320px]" role="img" aria-label="本命盘示意图">
        <circle :cx="CX" :cy="CY" :r="R_OUTER" fill="none" :style="{ stroke: 'var(--color-border-strong)' }" stroke-width="1" />
        <circle :cx="CX" :cy="CY" :r="R_INNER" fill="none" :style="{ stroke: 'var(--color-border)' }" stroke-width="1" />

        <line
          v-for="tick in signTicks"
          :key="tick.sign + '-line'"
          :x1="tick.line[0].x"
          :y1="tick.line[0].y"
          :x2="tick.line[1].x"
          :y2="tick.line[1].y"
          :style="{ stroke: 'var(--color-border)' }"
          stroke-width="0.8"
        />
        <text
          v-for="tick in signTicks"
          :key="tick.sign"
          :x="tick.label.x"
          :y="tick.label.y"
          text-anchor="middle"
          dominant-baseline="middle"
          font-size="8.5"
          :style="{ fill: ELEMENT_FILL[tick.element] }"
        >
          {{ tick.sign }}
        </text>

        <line
          v-for="chord in chords"
          :key="chord.key"
          :x1="chord.from.x"
          :y1="chord.from.y"
          :x2="chord.to.x"
          :y2="chord.to.y"
          :style="{ stroke: chord.color }"
          stroke-width="0.9"
          opacity="0.42"
        />

        <template v-if="ascMark">
          <line
            :x1="ascMark.a.x"
            :y1="ascMark.a.y"
            :x2="ascMark.b.x"
            :y2="ascMark.b.y"
            :style="{ stroke: 'var(--color-accent)' }"
            stroke-width="1.6"
          />
          <text
            :x="ascMark.label.x"
            :y="ascMark.label.y"
            text-anchor="middle"
            dominant-baseline="middle"
            font-size="7.5"
            font-weight="500"
            :style="{ fill: 'var(--color-accent)' }"
          >
            ASC
          </text>
        </template>
        <line
          v-if="mcMark"
          :x1="mcMark.a.x"
          :y1="mcMark.a.y"
          :x2="mcMark.b.x"
          :y2="mcMark.b.y"
          :style="{ stroke: 'var(--color-primary)' }"
          stroke-width="1"
          stroke-dasharray="2 2"
        />

        <g v-for="p in wheelPlanets" :key="p.name">
          <circle :cx="p.x" :cy="p.y" r="2.4" :style="{ fill: 'var(--color-primary)' }" />
          <text
            :x="p.labelX"
            :y="p.labelY"
            text-anchor="middle"
            dominant-baseline="middle"
            font-size="9"
            :style="{ fill: 'var(--color-text)' }"
          >
            {{ p.abbr }}<tspan v-if="p.retrograde" font-size="5.5" :style="{ fill: 'var(--color-text-muted)' }">R</tspan>
          </text>
        </g>
      </svg>
      <div class="mt-1 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[12px] text-muted">
        <span>· 日 月 水 金 火 木 土 天 海 冥</span>
        <span v-if="hasAngles" class="text-accent">— 上升</span>
        <span v-if="chart.mc" class="text-ink-2">-- 天顶</span>
        <span v-if="!hasAngles">未定上升，盘面以白羊 0° 起排</span>
      </div>
    </section>

    <section class="overflow-hidden border-t border-line-strong">
      <div class="grid grid-cols-[1.1fr_1fr_1fr_0.6fr_0.5fr] gap-2 border-b border-line px-1 py-2 text-[12px] text-muted">
        <span>行星</span><span>星座</span><span class="text-right">度数</span><span class="text-center">宫位</span><span class="text-right">逆行</span>
      </div>
      <div
        v-for="p in chart.planets"
        :key="p.name"
        class="grid grid-cols-[1.1fr_1fr_1fr_0.6fr_0.5fr] items-center gap-2 border-b border-line px-1 py-1.5 text-[12px] last:border-b-0"
        :data-planet="p.name"
        :data-sign="p.sign"
        :data-house="p.house ?? ''"
        :data-retrograde="p.retrograde ? 'true' : 'false'"
      >
        <span>{{ p.name }}</span>
        <span :class="signClass(p.sign)">{{ p.sign }}</span>
        <span class="tabular text-right text-ink-2">{{ fmtDegree(p.degree_in_sign) }}</span>
        <span class="tabular text-center text-ink-2">{{ p.house ?? '—' }}</span>
        <span class="text-right" :class="p.retrograde ? 'text-accent' : 'text-muted'">{{ p.retrograde ? '是' : '—' }}</span>
      </div>
    </section>

    <section v-if="chart.aspects.length" class="border-t border-line-strong pt-3">
      <p class="mb-1.5 text-[13px] text-muted">主要相位（容许度 ≤ 3°）</p>
      <ul class="space-y-1">
        <li
          v-for="a in chart.aspects.filter((x) => (x.orb ?? 9) <= 3).slice(0, 12)"
          :key="`${a.a}-${a.b}-${a.type}`"
          class="flex items-baseline justify-between gap-2 text-[12px]"
        >
          <span class="min-w-0">
            {{ a.a }}<span class="mx-1 text-muted">{{ a.type }}</span>{{ a.b }}
          </span>
          <span class="tabular shrink-0 text-[13px] text-muted">{{ Number(a.orb.toFixed(2)) }}°</span>
        </li>
      </ul>
      <p v-if="chart.aspects.every((x) => (x.orb ?? 9) > 3)" class="text-[12px] text-muted">暂无紧密相位，放宽容许度可看到更多组合。</p>
    </section>

    <section class="border-t border-line-strong pt-3">
      <p class="mb-2 text-[13px] text-muted">元素平衡（日月与内行星）</p>
      <div class="space-y-1.5">
        <div v-for="e in elements" :key="e.key" class="flex items-center gap-2 text-[13px]">
          <span class="w-3 shrink-0" :class="ELEMENT_CLASS[e.key]">{{ e.key }}</span>
          <div class="h-1.5 min-w-0 flex-1 overflow-hidden bg-surface-2">
            <div class="h-full" :style="{ width: `${e.pct}%`, background: ELEMENT_FILL[e.key] }" />
          </div>
          <span class="tabular w-6 shrink-0 text-right text-muted">{{ e.count }}</span>
        </div>
      </div>

      <p class="mb-2 mt-3 text-[13px] text-muted">模式平衡</p>
      <div class="space-y-1.5">
        <div v-for="m in modes" :key="m.key" class="flex items-center gap-2 text-[13px]">
          <span class="w-6 shrink-0 text-ink-2">{{ m.key }}</span>
          <div class="h-1.5 min-w-0 flex-1 overflow-hidden bg-surface-2">
            <div class="h-full bg-ink" :style="{ width: `${m.pct}%` }" />
          </div>
          <span class="tabular w-6 shrink-0 text-right text-muted">{{ m.count }}</span>
        </div>
      </div>
    </section>

    <p class="px-1 text-[13px] leading-[1.6] text-muted">
      <template v-if="hasAngles">盘面以上升点定在左侧，行星按黄道经度逆时针排列；相位线仅画容许度 3° 以内的组合。</template>
      <template v-else>未算出上升与宫位，盘面按黄道经度排列，不标上升；宫位一栏显示为「—」。</template>
    </p>
  </div>
</template>
