<script setup lang="ts">
import { computed } from 'vue'
import type { BaziChart } from '@/api/types'

const props = defineProps<{ chart: BaziChart }>()

// 五行按天干地支归类，颜色只用 token
const WUXING: Record<string, 'mu' | 'huo' | 'tu' | 'jin' | 'shui'> = {
  甲: 'mu', 乙: 'mu', 寅: 'mu', 卯: 'mu',
  丙: 'huo', 丁: 'huo', 巳: 'huo', 午: 'huo',
  戊: 'tu', 己: 'tu', 辰: 'tu', 戌: 'tu', 丑: 'tu', 未: 'tu',
  庚: 'jin', 辛: 'jin', 申: 'jin', 酉: 'jin',
  壬: 'shui', 癸: 'shui', 亥: 'shui', 子: 'shui',
}
const WX_LABEL = { mu: '木', huo: '火', tu: '土', jin: '金', shui: '水' } as const
const charColor = (ch: string) => ({ color: `var(--color-${WUXING[ch] ?? 'text'})` })

const columns = [
  { key: 'year', label: '年柱' },
  { key: 'month', label: '月柱' },
  { key: 'day', label: '日柱' },
  { key: 'hour', label: '时柱' },
] as const

const pillars = computed(() =>
  columns.map((c) => ({ ...c, pillar: props.chart.pillars[c.key], isDay: c.key === 'day' })),
)

// 五行统计（干支各计一次）
const wuxingCount = computed(() => {
  const count: Record<string, number> = {}
  for (const p of pillars.value) {
    for (const ch of [p.pillar.gan, p.pillar.zhi]) {
      const wx = WUXING[ch]
      if (wx) count[wx] = (count[wx] ?? 0) + 1
    }
  }
  return count
})

// 神煞行形如「- 天乙贵人 — 见于年支、时支 — 年干/日干查地支」
const shensha = computed(() =>
  props.chart.shensha.map((line) => {
    const [name, ...rest] = line.replace(/^-\s*/, '').split('—').map((s) => s.trim())
    return { name, detail: rest.join(' · ') }
  }),
)

const tst = computed(() => props.chart.true_solar_time)
const fmtMin = (n: number) => `${n > 0 ? '+' : ''}${n.toFixed(2)} 分钟`

const WX_ORDER = ['mu', 'huo', 'tu', 'jin', 'shui'] as const
const wuxingRows = computed(() =>
  WX_ORDER.map((wx) => ({
    key: wx,
    label: WX_LABEL[wx],
    n: wuxingCount.value[wx] ?? 0,
  })),
)
const maxWx = computed(() => Math.max(1, ...wuxingRows.value.map((r) => r.n)))
</script>

<template>
  <div class="space-y-4">
    <!-- 命盘：四柱为主体，元信息收进盘头 -->
    <section class="chart-frame">
      <header class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="eyebrow">本命盘 · 四柱</p>
          <p class="tabular mt-1.5 text-[13px] leading-[1.6]">{{ chart.solar_date }}</p>
          <p class="text-[11px] leading-[1.6] text-muted">
            农历 {{ chart.lunar_date }} {{ chart.shichen }}
            <template v-if="chart.zishi !== '无'"> · {{ chart.zishi }}</template>
          </p>
        </div>
        <span v-if="tst" class="chip chip--primary shrink-0">
          真太阳时 {{ tst.true_solar_time.slice(11) }}
        </span>
        <span v-else class="chip shrink-0">未校正</span>
      </header>

      <!-- 四柱：细线分栏，日柱单独提亮 -->
      <div class="mt-4 grid grid-cols-4 overflow-hidden rounded-[var(--radius-md)] border border-line">
        <div
          v-for="(p, i) in pillars"
          :key="p.key"
          class="relative px-1.5 py-3 text-center"
          :class="[p.isDay ? 'bg-primary-soft' : '', i > 0 ? 'border-l border-line' : '']"
        >
          <p class="text-[10px] tracking-[0.18em]" :class="p.isDay ? 'text-primary' : 'text-muted'">{{ p.label }}</p>
          <p class="mt-1 truncate text-[11px]" :class="p.isDay ? 'font-medium text-primary' : 'text-ink-2'">
            {{ p.isDay ? '日主' : p.pillar.shishen }}
          </p>
          <p class="mt-1.5 font-serif text-[32px] leading-[1.05]" :style="charColor(p.pillar.gan)">
            {{ p.pillar.gan }}
          </p>
          <p class="font-serif text-[32px] leading-[1.05]" :style="charColor(p.pillar.zhi)">
            {{ p.pillar.zhi }}
          </p>
          <div class="mt-2 border-t border-line/70 pt-1.5">
            <p class="text-[10px] text-muted">藏干</p>
            <p class="mt-0.5 text-[10px] leading-[1.5] text-ink-2">{{ p.pillar.canggan }}</p>
          </div>
        </div>
      </div>

      <!-- 五行计数：短条，不是评分 -->
      <ul class="mt-4 grid grid-cols-5 gap-2">
        <li v-for="r in wuxingRows" :key="r.key" class="min-w-0">
          <div class="flex items-baseline justify-between gap-1">
            <span class="font-serif text-[13px]" :style="{ color: `var(--color-${r.key})` }">{{ r.label }}</span>
            <span class="tabular text-[11px] text-muted">{{ r.n }}</span>
          </div>
          <div class="mt-1 h-[3px] overflow-hidden rounded-full bg-surface-2">
            <span
              class="block h-full rounded-full"
              :style="{ width: `${(r.n / maxWx) * 100}%`, background: `var(--color-${r.key})` }"
            />
          </div>
        </li>
      </ul>

      <details v-if="tst" class="mt-3 border-t border-line pt-2 text-[11px] leading-[1.6] text-muted">
        <summary class="cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
          校正明细 · 钟表时 {{ tst.clock_time }} → {{ tst.true_solar_time }}
        </summary>
        <p class="mt-1.5">
          经度差 {{ fmtMin(tst.longitude_correction_minutes) }} + 均时差
          {{ fmtMin(tst.equation_of_time_minutes) }}，合计 {{ fmtMin(tst.total_correction_minutes) }}。
        </p>
      </details>
    </section>

    <!-- 神煞 -->
    <section v-if="shensha.length">
      <div class="mb-2 flex items-baseline justify-between">
        <h3 class="text-[13px] font-semibold text-ink-2">神煞</h3>
        <span class="text-xs text-muted">{{ shensha.length }} 项</span>
      </div>
      <ul class="flex flex-wrap gap-1.5">
        <li v-for="s in shensha" :key="s.name" class="chip" :title="s.detail">
          <span>{{ s.name }}</span>
        </li>
      </ul>
    </section>

    <!-- 大运 -->
    <section v-if="chart.dayun.length">
      <div class="mb-2 flex items-baseline justify-between">
        <h3 class="text-[13px] font-semibold text-ink-2">大运</h3>
        <span class="text-xs text-muted">{{ chart.qiyun }}起运 · {{ chart.forward ? '顺行' : '逆行' }}</span>
      </div>
      <div class="scroll-x -mx-1 px-1">
        <ul class="flex snap-x snap-mandatory gap-2 pb-1">
          <li
            v-for="row in chart.dayun"
            :key="row.index"
            class="w-[64px] shrink-0 snap-start rounded-[var(--radius-md)] border border-line bg-surface py-2.5 text-center"
          >
            <p class="tabular text-[10px] leading-tight text-muted">{{ row.age_range }}</p>
            <p class="mt-1 font-serif text-[19px] leading-tight">
              <span :style="charColor(row.ganzhi[0])">{{ row.ganzhi[0] }}</span><span :style="charColor(row.ganzhi[1])">{{ row.ganzhi[1] }}</span>
            </p>
            <p class="mt-0.5 text-[10px] leading-tight text-muted">{{ row.index === '起运前' ? '小运' : `第${row.index}步` }}</p>
          </li>
        </ul>
      </div>
      <p class="mt-2 text-[11px] text-muted">↔ 左右滑动查看全部大运</p>
    </section>

    <!-- 流年 -->
    <section v-if="chart.liunian.length">
      <h3 class="mb-2 text-[13px] font-semibold text-ink-2">近年流年</h3>
      <div class="grid grid-cols-4 gap-1.5 sm:grid-cols-6">
        <div v-for="y in chart.liunian" :key="y.year" class="rounded-[var(--radius-sm)] bg-surface-2 px-1 py-2 text-center">
          <p class="tabular text-[10px] text-muted">{{ y.year }}</p>
          <p class="mt-0.5 font-serif text-[15px] leading-tight">
            <span :style="charColor(y.ganzhi[0])">{{ y.ganzhi[0] }}</span><span :style="charColor(y.ganzhi[1])">{{ y.ganzhi[1] }}</span>
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
