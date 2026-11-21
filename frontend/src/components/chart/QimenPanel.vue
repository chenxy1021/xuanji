<script setup lang="ts">
import type { QimenChart } from '@/api/chartKinds'

defineProps<{ chart: QimenChart }>()
</script>

<template>
  <div class="space-y-3">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <div class="flex items-baseline justify-between">
        <p class="font-serif text-[20px]">{{ chart.ju_text }}<span class="ml-2 text-xs text-muted">{{ chart.yuan }}</span></p>
        <p class="text-xs text-muted">{{ chart.solar_term }}</p>
      </div>
      <p class="mt-2 text-[11px] text-muted">
        {{ chart.datetime }} 出生<span class="mx-1">·</span>{{ chart.lunar_date }}
        <template v-if="chart.lifelong"> · 属{{ chart.lifelong.zodiac }}</template>
      </p>
      <dl class="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px]">
        <div class="flex gap-1.5"><dt class="text-muted">值符</dt><dd>{{ chart.leaders.star }}</dd></div>
        <div class="flex gap-1.5"><dt class="text-muted">值使</dt><dd>{{ chart.leaders.door }}</dd></div>
        <div class="flex gap-1.5"><dt class="text-muted">旬首</dt><dd>{{ chart.xun.head }}</dd></div>
        <div class="flex gap-1.5"><dt class="text-muted">空亡</dt><dd>{{ chart.xun.void_branches.join('、') || '—' }}</dd></div>
        <div class="flex gap-1.5"><dt class="text-muted">马星</dt><dd>{{ chart.horse.branch }}（{{ chart.horse.palace }}宫）</dd></div>
        <div class="flex gap-1.5"><dt class="text-muted">四柱</dt><dd class="tabular">{{ Object.values(chart.four_pillars).join(' ') }}</dd></div>
      </dl>
    </section>

    <section v-if="chart.lifelong" class="space-y-2">
      <article
        v-for="a in chart.lifelong.anchors"
        :key="a.key"
        class="rounded-[var(--radius-lg)] border border-line bg-surface p-3"
      >
        <div class="flex items-baseline justify-between gap-2">
          <p class="text-[11px] text-muted">{{ a.label }} · {{ a.role }}</p>
          <span class="chip shrink-0">{{ a.ganzhi }}</span>
        </div>
        <template v-if="a.palace">
          <p class="mt-1 font-serif text-[18px] leading-tight">
            {{ a.palace.trigram }}宫<span class="mx-1 text-muted">·</span>{{ a.palace.door }}
            <span class="mx-1 text-muted">·</span>{{ a.star }}
          </p>
          <p class="mt-1 text-[12px] leading-[1.6] text-ink-2">{{ a.summary }}</p>
          <p class="mt-1.5 border-t border-line pt-1.5 text-[10px] text-muted">
            {{ a.basis }}<template v-if="a.relation?.name"> · {{ a.relation.name }}</template>
          </p>
        </template>
        <p v-else class="mt-1 text-[12px] text-muted">该天干未见于地盘，暂不作断。</p>
      </article>
    </section>

    <section class="grid grid-cols-3 overflow-hidden rounded-[var(--radius-lg)] border border-line">
      <article
        v-for="p in chart.grid"
        :key="p.number"
        :data-palace="p.number"
        class="relative min-h-[104px] border-line/70 p-2"
        :class="[
          p.number === 5 ? 'bg-surface-2' : 'bg-surface',
          p.number !== 4 && p.number !== 9 && p.number !== 2 ? 'border-t' : '',
          p.number !== 4 && p.number !== 3 && p.number !== 8 ? 'border-l' : '',
        ]"
      >
        <div class="flex items-center justify-between text-[10px] text-muted">
          <span>{{ p.trigram === '中' ? '中宫' : `${p.trigram}${p.number}` }}</span>
          <span v-if="p.is_horse" class="text-accent">马</span>
        </div>

        <template v-if="p.number === 5">
          <p class="mt-3 text-center text-[11px] text-muted">天禽寄坤</p>
          <p class="mt-1 text-center font-serif text-[16px]">{{ p.earth_stem }}</p>
        </template>

        <template v-else>
          <p class="mt-1 text-[10px] text-muted">{{ p.deity }}</p>
          <p class="font-serif text-[15px] leading-tight">{{ p.stars.join('·') || '—' }}</p>
          <p class="text-[12px] text-primary">{{ p.door }}</p>
          <p class="tabular mt-0.5 text-[10px] text-muted">
            天{{ p.heaven_stems.join('') || '—' }} · 地{{ p.earth_stem }}
          </p>
          <p v-if="p.void_branches.length" class="text-[10px] text-muted">空{{ p.void_branches.join('') }}</p>
        </template>
      </article>
    </section>

    <p class="px-1 text-[11px] leading-[1.6] text-muted">
      终身局以年命看一生底色、日干看本人、时干看事业与晚运；门星神与干宫生克要合看。
    </p>
  </div>
</template>
