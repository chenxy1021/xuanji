<script setup lang="ts">
import { computed } from 'vue'
import type { MeihuaChart, MeihuaGua, MeihuaTrigramInfo } from '@/api/chartKinds'

const props = defineProps<{ chart: MeihuaChart }>()

// 八卦自下而上的阴阳（1 阳 / 0 阴）
const TRIGRAM_LINES: Record<string, number[]> = {
  乾: [1, 1, 1], 天: [1, 1, 1],
  兑: [1, 1, 0], 泽: [1, 1, 0],
  离: [1, 0, 1], 火: [1, 0, 1],
  震: [1, 0, 0], 雷: [1, 0, 0],
  巽: [0, 1, 1], 风: [0, 1, 1],
  坎: [0, 1, 0], 水: [0, 1, 0],
  艮: [0, 0, 1], 山: [0, 0, 1],
  坤: [0, 0, 0], 地: [0, 0, 0],
}

const ben = computed<MeihuaGua | undefined>(() => props.chart.ben ?? props.chart.ben_gua)
const hu = computed<MeihuaGua | undefined>(() => props.chart.hu ?? props.chart.hu_gua)
const bian = computed<MeihuaGua | undefined>(() => props.chart.bian ?? props.chart.bian_gua)

function linesOf(gua?: MeihuaGua): number[] | null {
  if (gua?.code) return gua.code.split('').map(Number)
  if (!gua?.upper || !gua?.lower) return null
  const lower = TRIGRAM_LINES[gua.lower[0]]
  const upper = TRIGRAM_LINES[gua.upper[0]]
  if (!lower || !upper) return null
  return [...lower, ...upper]
}

const benLines = computed(() => linesOf(ben.value))
const bianLines = computed(() => {
  const own = linesOf(bian.value)
  if (own) return own
  if (!benLines.value) return null
  const lines = [...benLines.value]
  const idx = (props.chart.moving_line ?? 0) - 1
  if (idx >= 0 && idx < 6) lines[idx] = lines[idx] ? 0 : 1
  return lines
})

const castText = computed(() => props.chart.cast?.detail ?? '')

function fmtTrigram(value?: MeihuaTrigramInfo | string) {
  if (!value) return ''
  if (typeof value === 'string') return value
  return `${value.trigram}（${value.element}，${value.position}）`
}

const tiYongText = computed(() => {
  const v = props.chart.ti_yong
  if (!v) return ''
  if (typeof v === 'string') return v
  return `体：${fmtTrigram(v.ti)}　用：${fmtTrigram(v.yong)}`
})

const relation = computed(() => {
  const v = props.chart.relation
  if (!v) return null
  return typeof v === 'string' ? { name: v, result: '', explain: '' } : v
})

const relationClass = computed(() => {
  const r = relation.value?.result ?? ''
  return r.includes('凶') ? 'text-accent' : r.includes('吉') ? 'text-primary' : 'text-ink'
})

function lineClass(block: { moving: boolean }, index: number) {
  return block.moving && props.chart.moving_line === index + 1 ? 'text-accent' : 'text-ink'
}
</script>

<template>
  <div class="space-y-3">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <p class="text-xs text-muted">
        {{ chart.method_name || (chart.method === 'time' ? '时间起卦' : '数字起卦') }}
        <span v-if="castText"> · {{ castText }}</span>
      </p>
      <p class="mt-1 font-serif text-[22px] leading-tight">{{ ben?.name || '本卦' }}</p>
      <p class="mt-1 text-[13px] text-ink-2">
        上{{ ben?.upper }}　下{{ ben?.lower }}
        <template v-if="chart.moving_line">　动爻：{{ chart.moving_line_name || `第 ${chart.moving_line} 爻` }}</template>
      </p>
      <p v-if="ben?.yixiang" class="mt-1.5 text-[13px] leading-[1.6] text-muted">{{ ben.yixiang }}</p>
    </section>

    <section class="grid grid-cols-3 gap-2">
      <article
        v-for="block in [
          { label: '本卦', gua: ben, lines: benLines, moving: true },
          { label: '互卦', gua: hu, lines: linesOf(hu), moving: false },
          { label: '变卦', gua: bian, lines: bianLines, moving: false },
        ]"
        :key="block.label"
        class="rounded-[var(--radius-lg)] border border-line bg-surface p-2 text-center"
      >
        <p class="text-[11px] text-muted">{{ block.label }}</p>
        <div class="mx-auto mt-2 flex h-[72px] w-[52px] flex-col-reverse justify-between">
          <template v-if="block.lines">
            <div
              v-for="(v, i) in block.lines"
              :key="i"
              class="flex h-[7px] items-center justify-center gap-[3px]"
              :class="lineClass(block, i)"
            >
              <span v-if="v" class="h-[4px] w-full rounded-[1px] bg-current" />
              <template v-else>
                <span class="h-[4px] w-[45%] rounded-[1px] bg-current" />
                <span class="h-[4px] w-[45%] rounded-[1px] bg-current" />
              </template>
            </div>
          </template>
          <p v-else class="text-[11px] text-muted">—</p>
        </div>
        <p class="mt-2 font-serif text-[13px] leading-tight">{{ block.gua?.name || '—' }}</p>
      </article>
    </section>

    <section v-if="tiYongText || relation || chart.judgement" class="space-y-2 rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <p v-if="tiYongText" class="text-[13px]"><span class="text-muted">体用：</span>{{ tiYongText }}</p>
      <p v-if="relation" class="text-[13px] leading-[1.6]">
        <span class="text-muted">生克：</span>
        <span :class="relationClass">{{ relation.name }}</span>
        <span v-if="relation.explain">　{{ relation.explain }}</span>
      </p>
      <p v-if="chart.judgement" class="font-serif text-[15px] leading-[1.7]">{{ chart.judgement }}</p>
    </section>

    <p class="px-1 text-[11px] leading-[1.6] text-muted">
      梅花易数重在体用生克与动爻；卦名只是索引，具体吉凶要结合所问之事。
    </p>
  </div>
</template>
