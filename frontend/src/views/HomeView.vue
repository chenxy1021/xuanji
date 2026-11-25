<script setup lang="ts">
// hero 视觉参考 design/unslop/home.html（unslop by @heydamir · CC BY 4.0）
import { computed, onMounted, ref } from 'vue'
import StarChart from '@/components/StarChart.vue'
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
    <section class="home-hero">
      <div class="mx-auto w-full max-w-[600px] lg:mx-0">
        <h1>
          {{ t('home.titleBefore') }}<br />{{ t('home.titleAfter') }}
        </h1>
        <p class="home-sub">{{ t('home.subtitle') }}</p>
        <p class="home-meta">{{ t('home.meta', { n: visibleCount }) }}</p>
      </div>
      <StarChart />
    </section>

    <section v-for="(g, gi) in groups" :key="g.key" class="home-group" :aria-labelledby="`grp-${g.key}`">
      <div class="group-head">
        <div class="flex items-baseline gap-4">
          <span class="idx">{{ String(gi + 1).padStart(2, '0') }}</span>
          <h2 :id="`grp-${g.key}`">{{ t(g.label) }}</h2>
        </div>
        <span class="idx">{{ t('home.available', { n: g.items.length }) }}</span>
      </div>
      <div class="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-4">
        <SystemCard v-for="s in g.items" :key="s.id" :spec="s" />
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
