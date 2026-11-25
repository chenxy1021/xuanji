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
    <section class="border-t border-line-strong pb-4 pt-4">
      <p class="text-xs text-muted">合盘评分</p>
      <p class="tabular mt-1 font-serif text-[32px] leading-tight">{{ chart.score }}</p>
      <span class="chip chip--primary mt-1">匹配度「{{ chart.level }}」</span>
    </section>

    <section class="grid grid-cols-2 gap-4">
      <div v-for="[label, p] in people" :key="label" class="border-t border-line pt-3">
        <p class="text-[13px] font-semibold">{{ label }}<span class="ml-1 text-xs font-normal text-muted">{{ p.gender }}</span></p>
        <p class="mt-0.5 text-[13px] text-muted">{{ p.solar_date }}</p>
        <dl class="mt-2 space-y-1 text-[12px]">
          <div v-for="(v, k) in detailOf(p)" :key="k" class="flex gap-2">
            <dt class="w-12 shrink-0 text-muted">{{ k }}</dt>
            <dd class="min-w-0 break-all text-ink-2">{{ v }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section v-if="chart.matches.length">
      <h3 class="form-label">契合点</h3>
      <ul>
        <li v-for="(m, i) in chart.matches" :key="i" class="border-t border-line py-2.5">
          <div class="flex items-center gap-1.5">
            <span class="text-xs text-muted">{{ m.scope }}</span>
            <span class="chip h-6" :class="EFFECT[m.effect ?? '']">{{ m.kind }}</span>
          </div>
          <p class="mt-1 text-[13px] leading-[1.6] text-ink-2">{{ m.detail }}</p>
        </li>
      </ul>
    </section>

    <section v-if="chart.advice.length">
      <h3 class="form-label">建议</h3>
      <ul class="list-disc space-y-1.5 pl-5 text-[13px] leading-[1.6] text-ink-2">
        <li v-for="a in chart.advice" :key="a">{{ a }}</li>
      </ul>
    </section>

    <p class="border-t border-line pt-3 text-xs leading-[1.6] text-muted">{{ chart.disclaimer }}</p>
  </div>
</template>
