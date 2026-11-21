<script setup lang="ts">
import type { TarotChart } from '@/api/types'

defineProps<{ chart: TarotChart }>()
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <p class="font-serif text-[18px]">{{ chart.spread_name }}</p>
      <p class="mt-1 text-[13px] leading-[1.6] text-muted">{{ chart.spread_description }}</p>
      <p v-if="chart.question" class="mt-2 rounded-[var(--radius-sm)] bg-surface-2 px-3 py-2 text-sm">问：{{ chart.question }}</p>
      <p v-if="chart.seed != null" class="mt-2 text-[11px] text-muted">seed {{ chart.seed }}</p>
    </section>

    <section
      class="grid gap-2"
      :class="chart.cards.length === 1 ? '' : 'sm:grid-cols-2'"
    >
      <article
        v-for="card in chart.cards"
        :key="card.position + card.name"
        class="rounded-[var(--radius-lg)] border border-line bg-surface p-3"
      >
        <p class="text-xs text-muted">{{ card.position }}</p>
        <div class="mt-1 flex items-baseline gap-2">
          <h3 class="font-serif text-[20px] leading-tight">{{ card.name }}</h3>
          <span
            class="chip"
            :class="card.orientation === '逆位' ? 'chip--accent' : 'chip--primary'"
          >
            {{ card.orientation }}
          </span>
        </div>
        <p class="mt-0.5 text-[11px] text-muted">
          {{ card.arcana === 'major' ? '大阿尔卡纳' : `${card.suit} · 小阿尔卡纳` }}
        </p>
        <p class="mt-2 text-[13px] leading-[1.6] text-ink-2">{{ card.keywords }}</p>
      </article>
    </section>
  </div>
</template>
