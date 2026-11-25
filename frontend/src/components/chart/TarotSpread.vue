<script setup lang="ts">
import type { TarotChart } from '@/api/types'

defineProps<{ chart: TarotChart }>()
</script>

<template>
  <div class="space-y-4">
    <section class="border-t border-line-strong pt-3">
      <p class="font-serif text-[18px]">{{ chart.spread_name }}</p>
      <p class="mt-1 text-[13px] leading-[1.6] text-muted">{{ chart.spread_description }}</p>
      <p v-if="chart.question" class="mt-2 border-l border-line-strong pl-3 text-sm">问：{{ chart.question }}</p>
      <p v-if="chart.seed != null" class="mt-2 text-[13px] text-muted">seed {{ chart.seed }}</p>
    </section>

    <section
      class="grid gap-x-6"
      :class="chart.cards.length === 1 ? '' : 'sm:grid-cols-2'"
    >
      <article
        v-for="card in chart.cards"
        :key="card.position + card.name"
        class="border-t border-line py-3"
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
        <p class="mt-0.5 text-[13px] text-muted">
          {{ card.arcana === 'major' ? '大阿尔卡纳' : `${card.suit} · 小阿尔卡纳` }}
        </p>
        <p class="mt-2 text-[13px] leading-[1.6] text-ink-2">{{ card.keywords }}</p>
      </article>
    </section>
  </div>
</template>
