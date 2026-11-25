<script setup lang="ts">
// 首页星盘：二十八宿外环缓转，刻度反向微转，朱砂指针扫过盘面。
// 纯 SVG + CSS 动画；prefers-reduced-motion 下全部静止。
import { t } from '@/i18n'

const SIZE = 420
const C = SIZE / 2
const R_OUT = 198
const R_TICK_OUT = 160
const R_SIGN = 126
const R_IN = 108
const R_SWEEP = 160

const polar = (r: number, deg: number) => {
  const rad = ((deg - 90) * Math.PI) / 180
  return {
    x: +(C + r * Math.cos(rad)).toFixed(2),
    y: +(C + r * Math.sin(rad)).toFixed(2),
  }
}

// 二十八宿（角起，顺时针）
const MANSIONS = [
  '角', '亢', '氐', '房', '心', '尾', '箕',
  '斗', '牛', '女', '虚', '危', '室', '壁',
  '奎', '娄', '胃', '昴', '毕', '觜', '参',
  '井', '鬼', '柳', '星', '张', '翼', '轸',
]
const SIGNS = ['白羊', '金牛', '双子', '巨蟹', '狮子', '处女', '天秤', '天蝎', '射手', '摩羯', '水瓶', '双鱼']

const mansions = MANSIONS.map((name, i) => {
  const deg = (i * 360) / MANSIONS.length
  return { name, ...polar(176, deg) }
})

// 七十二刻度，每 30° 一根长刻度
const ticks = Array.from({ length: 72 }, (_, i) => {
  const deg = i * 5
  const major = i % 6 === 0
  const a = polar(R_TICK_OUT, deg)
  const b = polar(major ? 148 : 154, deg)
  return { x1: a.x, y1: a.y, x2: b.x, y2: b.y, major }
})

// 十二宫落在刻度间（每宫中线）
const signs = SIGNS.map((name, i) => ({ name, ...polar(R_SIGN, i * 30 + 15) }))

const houses = Array.from({ length: 12 }, (_, i) => {
  const a = polar(R_IN, i * 30)
  const b = polar(148, i * 30)
  return { x1: a.x, y1: a.y, x2: b.x, y2: b.y }
})

// 内圈星点：确定性分布，刷新不变
const stars = Array.from({ length: 40 }, (_, i) => {
  const deg = (i * 137.508 + 17) % 360
  const r = 64 + ((i * 19 + 11) % 40)
  const p = polar(r, deg)
  const size = i % 11 === 0 ? 1.7 : i % 4 === 0 ? 1.2 : 0.8
  return {
    ...p,
    size,
    delay: `${((i * 0.41) % 4.4).toFixed(2)}s`,
    dur: `${(3.2 + (i % 6) * 0.55).toFixed(2)}s`,
  }
})

// 两个交错三角 = 六芒相位线，落在内圈之外、刻度之内
const triangle = (offset: number) =>
  [0, 1, 2]
    .map((k) => polar(104, offset + k * 120))
    .map((p) => `${p.x},${p.y}`)
    .join(' ')
const aspectA = triangle(0)
const aspectB = triangle(60)

// 朱砂扇形：26° 的扫描光
const sweepStart = polar(R_SWEEP, -13)
const sweepEnd = polar(R_SWEEP, 13)
const sweepPath = `M ${C} ${C} L ${sweepStart.x} ${sweepStart.y} A ${R_SWEEP} ${R_SWEEP} 0 0 1 ${sweepEnd.x} ${sweepEnd.y} Z`
</script>

<template>
  <figure class="plate" :aria-label="t('home.plateAria')">
    <svg class="as" viewBox="0 0 420 420" role="img" :aria-label="t('home.plateAria')">
      <defs>
        <radialGradient id="as-sweep-fill" cx="50%" cy="50%" r="50%">
          <stop offset="54%" stop-color="var(--color-accent)" stop-opacity="0" />
          <stop offset="100%" stop-color="var(--color-accent)" stop-opacity="0.14" />
        </radialGradient>
      </defs>

      <g class="as-rings" aria-hidden="true">
        <circle :cx="C" :cy="C" :r="R_OUT" class="as-ring as-ring--strong" />
        <circle :cx="C" :cy="C" :r="164" class="as-ring" />
        <circle :cx="C" :cy="C" :r="148" class="as-ring" />
        <circle :cx="C" :cy="C" :r="R_IN" class="as-ring as-ring--strong" />
      </g>

      <g class="as-spin as-mansions" aria-hidden="true">
        <text
          v-for="m in mansions"
          :key="m.name"
          :x="m.x"
          :y="m.y"
          :style="{ transformOrigin: `${m.x}px ${m.y}px` }"
        >{{ m.name }}</text>
      </g>

      <g class="as-spin-rev as-ticks" aria-hidden="true">
        <line
          v-for="(tk, i) in ticks"
          :key="i"
          :x1="tk.x1"
          :y1="tk.y1"
          :x2="tk.x2"
          :y2="tk.y2"
          :class="tk.major ? 'is-major' : undefined"
        />
      </g>

      <g class="as-houses" aria-hidden="true">
        <line v-for="(h, i) in houses" :key="i" :x1="h.x1" :y1="h.y1" :x2="h.x2" :y2="h.y2" />
      </g>

      <g class="as-signs" aria-hidden="true">
        <text v-for="s in signs" :key="s.name" :x="s.x" :y="s.y">{{ s.name }}</text>
      </g>

      <g class="as-stars" aria-hidden="true">
        <circle
          v-for="(s, i) in stars"
          :key="i"
          :cx="s.x"
          :cy="s.y"
          :r="s.size"
          :style="{ animationDelay: s.delay, animationDuration: s.dur }"
        />
      </g>

      <g class="as-spin-mid as-aspect" aria-hidden="true">
        <polygon :points="aspectA" />
        <polygon :points="aspectB" />
      </g>

      <g class="as-sweep" aria-hidden="true">
        <path :d="sweepPath" class="as-sweep-wedge" />
        <line :x1="C" :y1="C" :x2="C" :y2="C - R_OUT" class="as-hand" />
        <circle :cx="C" :cy="C - (R_OUT - 8)" r="2.2" class="as-hand-dot" />
      </g>

      <g class="as-hub">
        <circle :cx="C" :cy="C" r="56" class="as-hub-disc" />
        <circle :cx="C" :cy="C" r="47" class="as-hub-ring" />
        <text :x="C" :y="C - 4" class="as-hub-name">{{ t('brand.name') }}</text>
      </g>
    </svg>
    <figcaption class="plate-cap">
      <span>{{ t('home.plateCap') }}</span>
      <span>{{ t('home.plateTag') }}</span>
    </figcaption>
  </figure>
</template>
