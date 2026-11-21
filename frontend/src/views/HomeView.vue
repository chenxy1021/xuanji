<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import SystemCard from '@/components/SystemCard.vue'
import { getSystems } from '@/api/client'
import type { SystemCategory, SystemSpec } from '@/api/types'
import { onLocaleChange, t, type MsgKey } from '@/i18n'

const systems = ref<SystemSpec[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    systems.value = await getSystems()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
// 英文名来自后端，切语言时重拉一次
onLocaleChange(load)

// 分组标题与顺序固定；组内保持后端返回顺序。后端只注册上线清单内的体系
const GROUPS: { key: SystemCategory; label: MsgKey }[] = [
  { key: 'chart', label: 'cat.chart' },
  { key: 'synastry', label: 'cat.synastry' },
  { key: 'divination', label: 'cat.divination' },
  { key: 'fun', label: 'cat.fun' },
]
const groups = computed(() =>
  GROUPS.map((g) => ({
    ...g,
    items: systems.value.filter((s) => (s.category ?? 'chart') === g.key),
  })).filter((g) => g.items.length > 0),
)
const visibleCount = computed(() => groups.value.reduce((n, g) => n + g.items.length, 0))
</script>

<template>
  <div class="pb-6">
    <section class="grid items-center gap-10 pb-12 pt-2 lg:grid-cols-12 lg:gap-6 lg:pb-20 lg:pt-8">
      <div class="lg:col-span-7">
        <p class="eyebrow">{{ t('home.eyebrow') }}</p>
        <h1 class="title-serif h-display mt-4 max-w-[15ch]">
          {{ t('home.title') }}
        </h1>
        <p class="mt-6 max-w-[560px] text-[15px] leading-[1.85] text-ink-2">
          {{ t('home.subtitle') }}
        </p>
        <p class="mt-2 max-w-[560px] text-[15px] leading-[1.85] text-muted">{{ t('home.lead') }}</p>
        <div class="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
          <RouterLink to="/chart/bazi" class="btn-ink w-full sm:w-auto">{{ t('home.cta') }}</RouterLink>
          <span class="text-[12px] text-muted">{{ t('home.meta', { n: visibleCount }) }}</span>
        </div>
      </div>
      <div class="hidden justify-end lg:col-span-5 lg:flex" aria-hidden="true">
        <svg viewBox="0 0 320 320" class="size-[320px] text-muted opacity-70" fill="none" stroke="currentColor" stroke-width="0.8">
          <circle cx="160" cy="160" r="148" />
          <circle cx="160" cy="160" r="118" />
          <circle cx="160" cy="160" r="74" stroke-dasharray="2 6" />
          <circle cx="160" cy="160" r="30" />
          <path d="M160 12v296M12 160h296M55 55l210 210M265 55 55 265" stroke-opacity=".35" />
          <g stroke="none" fill="currentColor">
            <circle cx="160" cy="42" r="2" />
            <circle cx="252" cy="272" r="1.6" />
            <circle cx="70" cy="226" r="1.4" />
            <circle cx="238" cy="92" r="1.8" />
          </g>
          <g fill="currentColor" stroke="none" font-size="11" font-family="var(--font-sans)" text-anchor="middle">
            <text x="160" y="30">子</text><text x="230" y="46">丑</text><text x="286" y="104">寅</text>
            <text x="300" y="164">卯</text><text x="276" y="228">辰</text><text x="220" y="286">巳</text>
            <text x="160" y="306">午</text><text x="100" y="286">未</text><text x="44" y="228">申</text>
            <text x="22" y="164">酉</text><text x="46" y="102">戌</text><text x="96" y="46">亥</text>
          </g>
        </svg>
      </div>
    </section>

    <section v-for="(g, gi) in groups" :key="g.key" class="pb-10 lg:pb-14" :aria-labelledby="`grp-${g.key}`">
      <div class="flex items-end justify-between gap-4 border-t-2 border-t-ink pb-5 pt-5">
        <h2 :id="`grp-${g.key}`" class="flex items-baseline gap-4">
          <span class="eyebrow tabular">{{ String(gi + 1).padStart(2, '0') }}</span>
          <span class="title-serif text-[22px] leading-none">{{ t(g.label) }}</span>
        </h2>
        <span class="text-[12px] text-muted">{{ t('home.available', { n: g.items.length }) }}</span>
      </div>
      <div class="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-4">
        <SystemCard v-for="(s, i) in g.items" :key="s.id" :spec="s" :index="i" />
      </div>
    </section>

    <div v-if="loading" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="h-[92px] animate-pulse border-t border-line" />
    </div>
    <div v-else-if="error" class="border-y border-line py-10">
      <p class="flex items-center gap-2 text-sm text-danger">
        <span class="flex size-5 shrink-0 items-center justify-center rounded-full border border-danger text-xs" aria-hidden="true">!</span>
        {{ error }}
      </p>
      <button type="button" class="link-underline mt-4 text-sm" @click="load">{{ t('home.retry') }}</button>
    </div>
  </div>
</template>
