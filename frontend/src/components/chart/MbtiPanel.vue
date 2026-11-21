<script setup lang="ts">
import type { MbtiChart } from '@/api/chartKinds'

defineProps<{ chart: MbtiChart }>()
</script>

<template>
  <div class="space-y-3">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4 text-center">
      <p class="font-serif text-[40px] leading-none tracking-[0.08em] text-primary">{{ chart.type }}</p>
      <p class="mt-2 text-[15px] font-medium">{{ chart.name }}</p>
      <p class="mx-auto mt-2 max-w-[34ch] text-[13px] leading-[1.7] text-ink-2">{{ chart.summary }}</p>
    </section>

    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <h3 class="text-[13px] font-semibold">四个维度</h3>
      <div class="mt-3 space-y-3">
        <div v-for="d in chart.dimensions" :key="d.key">
          <div class="flex items-baseline justify-between text-xs">
            <span :class="d.left_pct >= 50 ? 'font-medium text-primary' : 'text-muted'">
              {{ d.left_name }} {{ d.left }} · {{ d.left_pct }}%
            </span>
            <span :class="d.right_pct > 50 ? 'font-medium text-primary' : 'text-muted'">
              {{ d.right_pct }}% · {{ d.right }} {{ d.right_name }}
            </span>
          </div>
          <div class="relative mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
            <div class="absolute inset-y-0 left-0 bg-primary/70" :style="{ width: `${d.left_pct}%` }" />
            <div class="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
          </div>
          <p class="mt-1 text-[11px] text-muted">倾向{{ d.dominant }}（{{ d.strength }}）</p>
        </div>
      </div>
    </section>

    <section class="grid gap-2 sm:grid-cols-2">
      <div class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
        <h3 class="text-[13px] font-semibold text-primary">优势</h3>
        <ul class="mt-2 flex flex-wrap gap-1.5">
          <li v-for="s in chart.strengths" :key="s" class="chip chip--primary">{{ s }}</li>
        </ul>
      </div>
      <div class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
        <h3 class="text-[13px] font-semibold text-accent">盲点</h3>
        <ul class="mt-2 flex flex-wrap gap-1.5">
          <li v-for="s in chart.blind_spots" :key="s" class="chip chip--accent">{{ s }}</li>
        </ul>
      </div>
    </section>

    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <h3 class="text-[13px] font-semibold">适配环境</h3>
      <p class="mt-1.5 text-[13px] leading-[1.6] text-ink-2">{{ chart.fit }}</p>
    </section>

    <p class="px-1 text-[11px] leading-[1.6] text-muted">{{ chart.disclaimer }}</p>
  </div>
</template>
