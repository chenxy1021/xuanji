<script setup lang="ts">
import { computed } from 'vue'
import type { KongmingChart } from '@/api/chartKinds'

const props = defineProps<{ chart: KongmingChart }>()

const poemLines = computed(() => props.chart.lot.poem.match(/[^，。；]+[，。；]?/g) ?? [])

const toneClass = computed(() => {
  const tone = props.chart.reading.tone
  if (tone.includes('吉')) return 'chip--primary'
  if (tone.includes('凶')) return 'chip--accent'
  return ''
})
</script>

<template>
  <div class="space-y-3">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <div class="flex items-baseline justify-between gap-2">
        <p class="font-serif text-[20px]">第 {{ chart.lot.number }} 签</p>
        <span class="chip shrink-0" :class="toneClass">{{ chart.lot.fortune }}</span>
      </div>
      <p class="mt-1 text-[12px] text-ink-2">
        {{ chart.lot.palace }} · {{ chart.lot.hexagram }}变{{ chart.lot.changed }}
        <span class="text-muted">（{{ chart.lot.line }}）</span>
      </p>
      <p v-if="chart.question" class="mt-1.5 text-[12px] leading-[1.6] text-muted">
        所问：{{ chart.question }}
      </p>
    </section>

    <section class="rounded-[var(--radius-lg)] border border-line bg-surface px-4 py-5">
      <p class="text-[11px] text-muted">签文</p>
      <div class="mt-2 space-y-1 text-center font-serif text-[18px] leading-[1.9] tracking-[0.06em]">
        <p v-for="(line, i) in poemLines" :key="i">{{ line }}</p>
      </div>
    </section>

    <section class="space-y-2 rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <div class="flex flex-wrap items-center gap-1.5">
        <span class="text-[13px]">基调 · {{ chart.reading.tone }}</span>
        <span v-for="k in chart.reading.keywords" :key="k" class="chip">{{ k }}</span>
      </div>
      <p class="text-[13px] leading-[1.7] text-ink-2">{{ chart.reading.advice }}</p>
    </section>

    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-3">
      <p class="text-[11px] text-muted">取签过程</p>
      <p class="mt-1 text-[12px] leading-[1.7]">{{ chart.calculation.detail }}</p>
    </section>

    <p class="px-1 text-[11px] leading-[1.6] text-muted">{{ chart.disclaimer }}</p>
  </div>
</template>
