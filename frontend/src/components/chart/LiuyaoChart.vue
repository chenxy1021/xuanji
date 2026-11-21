<script setup lang="ts">
import type { LiuyaoChart } from '@/api/types'

defineProps<{ chart: LiuyaoChart }>()
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <p class="text-[13px] text-muted">{{ chart.method_name }} · {{ chart.cast_at }}</p>
      <p v-if="chart.question" class="mt-1 text-sm">问：{{ chart.question }}</p>
      <p class="mt-1 text-xs text-muted">
        {{ chart.lunar_date }} · {{ chart.year_gan_zhi }}年 {{ chart.month_gan_zhi }}月 {{ chart.day_gan_zhi }}日
      </p>
    </section>

    <section class="grid gap-3 sm:grid-cols-[auto_1fr]">
      <div class="rounded-[var(--radius-lg)] border border-line bg-surface p-3 text-center">
        <p class="text-xs text-muted">本卦</p>
        <p class="font-serif text-[26px] leading-tight">{{ chart.ben_gua.name }}</p>
        <p class="text-[11px] text-muted">{{ chart.ben_gua.full_name }} · {{ chart.ben_gua.palace }}宫{{ chart.ben_gua.element }}</p>
        <div class="mt-2 flex flex-col-reverse items-center gap-1" aria-label="本卦爻象">
          <div v-for="line in chart.ben_gua.lines" :key="line.position" class="flex w-16 items-center justify-center gap-1">
            <template v-if="line.yinyang === '阳'">
              <span class="h-1.5 w-full rounded-sm" :class="line.moving ? 'bg-accent' : 'bg-ink'" />
            </template>
            <template v-else>
              <span class="h-1.5 w-[42%] rounded-sm" :class="line.moving ? 'bg-accent' : 'bg-ink'" />
              <span class="h-1.5 w-[42%] rounded-sm" :class="line.moving ? 'bg-accent' : 'bg-ink'" />
            </template>
          </div>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-1">
        <div class="rounded-[var(--radius-md)] border border-line bg-surface p-3">
          <p class="text-xs text-muted">变卦</p>
          <p class="font-serif text-[18px]">{{ chart.bian_gua ? `${chart.bian_gua.name} · ${chart.bian_gua.full_name}` : '无动爻' }}</p>
        </div>
        <div class="rounded-[var(--radius-md)] border border-line bg-surface p-3">
          <p class="text-xs text-muted">互卦</p>
          <p class="font-serif text-[18px]">{{ chart.hu_gua.name }} · {{ chart.hu_gua.full_name }}</p>
        </div>
      </div>
    </section>

    <section class="rounded-[var(--radius-lg)] border border-line bg-surface p-4">
      <h3 class="mb-3 text-[13px] font-semibold text-ink-2">本卦六爻 <span class="ml-1 text-xs font-normal text-muted">自下而上</span></h3>
      <div class="scroll-x">
        <table class="w-full text-center text-[13px]">
          <thead>
            <tr class="bg-surface-2 text-xs text-muted">
              <th scope="col" class="px-2 py-1.5 font-medium">六神</th>
              <th scope="col" class="px-2 py-1.5 font-medium">爻</th>
              <th scope="col" class="px-2 py-1.5 font-medium">六亲</th>
              <th scope="col" class="px-2 py-1.5 font-medium">纳甲</th>
              <th scope="col" class="px-2 py-1.5 font-medium">世应</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="line in [...chart.ben_gua.lines].reverse()"
              :key="line.position"
              class="border-t border-line"
              :class="line.moving ? 'text-accent' : ''"
            >
              <td class="px-2 py-2 text-muted">{{ line.liushen }}</td>
              <td class="px-2 py-2">
                {{ line.yinyang }}<span v-if="line.moving" class="ml-0.5 text-[11px]">●</span>
              </td>
              <td class="px-2 py-2">{{ line.liuqin }}</td>
              <td class="px-2 py-2">{{ line.gan_zhi }}<span class="ml-0.5 text-[11px] text-muted">{{ line.wuxing }}</span></td>
              <td class="px-2 py-2 font-medium">{{ line.shi_ying ?? '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="chart.moving_lines.length" class="mt-2 text-xs text-muted">
        动爻：第 {{ chart.moving_lines.join('、') }} 爻
      </p>
    </section>
  </div>
</template>
