<script setup lang="ts">
import { computed } from 'vue'
import type { SynastryChart, SynastryPerson } from '@/api/types'

const props = defineProps<{ chart: SynastryChart; kind: 'bazi' | 'ziwei' }>()

const EFFECT: Record<string, string> = {
  positive: 'chip--primary',
  neutral: '',
  negative: 'chip--accent',
}

const people = computed<[string, SynastryPerson, SynastryPerson][]>(() => [
  ['甲方', props.chart.a, props.chart.b],
  ['乙方', props.chart.b, props.chart.a],
])

const detailOf = (p: SynastryPerson) =>
  props.kind === 'bazi'
    ? {
        日主: p.day_master ? `${p.day_master}${p.day_master_element ?? ''}` : '—',
        夫妻宫: p.spouse_palace ?? '—',
        生肖: p.zodiac ?? '—',
        四柱: p.pillars ? Object.values(p.pillars).join(' ') : '—',
      }
    : {
        命宫: `${p.ming_branch ?? '—'}${p.ming_stars?.length ? ` ${p.ming_stars.join('、')}` : ''}`,
        夫妻宫: `${p.spouse_branch ?? '—'}${p.spouse_stars?.length ? ` ${p.spouse_stars.join('、')}` : ''}`,
        五行局: p.bureau ?? '—',
        四化: p.sihua ? Object.entries(p.sihua).map(([h, s]) => `${h}${s}`).join(' ') : '—',
      }
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4 text-center">
      <p class="text-xs text-muted">合盘评分</p>
      <p class="tabular mt-1 font-serif text-[32px] leading-tight text-primary">{{ chart.score }}</p>
      <span class="chip chip--primary mt-1">匹配度「{{ chart.level }}」</span>
    </section>

    <section class="grid grid-cols-2 gap-3">
      <div v-for="[label, p] in people" :key="label" class="rounded-[var(--radius-lg)] border border-line bg-surface p-3">
        <p class="text-[13px] font-semibold">{{ label }}<span class="ml-1 text-xs font-normal text-muted">{{ p.gender }}</span></p>
        <p class="mt-0.5 text-[11px] text-muted">{{ p.solar_date }}</p>
        <dl class="mt-2 space-y-1 text-[12px]">
          <div v-for="(v, k) in detailOf(p)" :key="k" class="flex gap-2">
            <dt class="w-12 shrink-0 text-muted">{{ k }}</dt>
            <dd class="min-w-0 break-all text-ink-2">{{ v }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section v-if="chart.matches.length">
      <h3 class="mb-2 text-[13px] font-semibold text-ink-2">契合点</h3>
      <ul class="space-y-2">
        <li v-for="(m, i) in chart.matches" :key="i" class="rounded-[var(--radius-md)] border border-line bg-surface p-3">
          <div class="flex items-center gap-1.5">
            <span class="text-xs text-muted">{{ m.scope }}</span>
            <span class="chip h-6" :class="EFFECT[m.effect ?? '']">{{ m.kind }}</span>
          </div>
          <p class="mt-1 text-[13px] leading-[1.6] text-ink-2">{{ m.detail }}</p>
        </li>
      </ul>
    </section>

    <section v-if="chart.advice.length">
      <h3 class="mb-2 text-[13px] font-semibold text-ink-2">建议</h3>
      <ul class="space-y-1.5 text-[13px] leading-[1.6] text-ink-2">
        <li v-for="a in chart.advice" :key="a" class="flex gap-2">
          <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
          {{ a }}
        </li>
      </ul>
    </section>

    <p class="rounded-[var(--radius-sm)] bg-bg-subtle p-3 text-xs leading-[1.6] text-muted">{{ chart.disclaimer }}</p>
  </div>
</template>
