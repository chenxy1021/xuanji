<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'
import { chartSubtitle, type HistoryRecord } from '@/api/types'
import { t, useLocale } from '@/i18n'
import { systemNameById } from '@/i18n/terms'

const charts = useChartsStore()
const auth = useAuthStore()
const locale = useLocale()
const loading = ref(false)
const error = ref('')
const busy = ref(false)

async function load() {
  error.value = ''
  await auth.bootstrap()
  if (!auth.isLoggedIn) return
  loading.value = true
  try {
    await charts.loadFromServer()
  } catch (e) {
    error.value = e instanceof ApiError && e.status === 401 ? t('history.needLogin') : t('history.loadFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
// App.vue 换账号时先 reset()，这里在登录态变化后补拉一次
watch(() => auth.user?.id, load)

async function removeRecord(id: string) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await charts.remove(id, auth.isLoggedIn)
  } catch (e) {
    error.value = e instanceof ApiError && e.status === 401 ? t('history.needLogin') : t('history.deleteFailed')
  } finally {
    busy.value = false
  }
}

async function clearAll() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await charts.clear(auth.isLoggedIn)
  } catch (e) {
    error.value = e instanceof ApiError && e.status === 401 ? t('history.needLogin') : t('history.deleteFailed')
  } finally {
    busy.value = false
  }
}

const fmt = (ts: number) =>
  new Date(ts).toLocaleString(locale.value === 'en' ? 'en-US' : 'zh-CN', { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })

function open(id: string) {
  const rec = charts.find(id)
  if (rec) charts.current = rec
}

// 命盘列：四柱给干支四字，其余给盘面自带摘要（农历/星盘名等）
const boardSummary = (rec: HistoryRecord) => {
  const c = rec.chart as { pillars?: Record<string, { gan: string; zhi: string }> }
  if (c?.pillars) return Object.values(c.pillars).map((p) => p.gan + p.zhi).join('  ')
  return chartSubtitle(rec.chart)
}
const systemLabel = (rec: HistoryRecord) => systemNameById(rec.system) ?? rec.title.replace(/^[\d\s:.-]+/, '').split(' · ')[0]
</script>

<template>
  <div>
    <div class="flex items-end justify-between gap-4 border-b border-line pb-5">
      <div>
        <p class="eyebrow">{{ t('tab.history') }} · HISTORY</p>
        <h1 class="title-serif h-h1 mt-3">{{ t('history.title') }}</h1>
        <p class="mt-2 text-xs text-muted">{{ auth.isLoggedIn ? t('history.onlineNote') : t('history.note') }}</p>
      </div>
      <button
        v-if="charts.history.length && auth.isLoggedIn"
        type="button"
        class="link-underline shrink-0 text-[13px] text-danger disabled:opacity-50"
        :disabled="busy"
        @click="clearAll"
      >
        {{ t('history.clearAll') }}
      </button>
    </div>

    <p v-if="error" class="mt-4 flex gap-2 rounded-[var(--radius-sm)] bg-danger-soft p-3 text-xs leading-[1.6] text-danger" role="alert" data-history-error>
      <span class="flex size-4 shrink-0 items-center justify-center rounded-full border border-danger text-[10px]" aria-hidden="true">!</span>
      {{ error }}
    </p>

    <!-- 未登录：不展示本机遗留的旧记录 -->
    <div v-if="auth.ready && !auth.isLoggedIn" class="py-16 text-left" data-history-guest>
      <p class="text-sm text-muted">{{ t('history.needLogin') }}</p>
      <RouterLink to="/login?next=/history" class="btn-line mt-4 inline-flex">{{ t('common.login') }}</RouterLink>
    </div>

    <p v-else-if="loading && !charts.history.length" class="animate-pulse py-16 text-sm text-muted">{{ t('common.loading') }}</p>

    <div v-else-if="!charts.history.length" class="py-16 text-left">
      <p class="text-sm text-muted">{{ t('history.empty') }}</p>
      <RouterLink to="/chart/bazi" class="link-underline mt-3 inline-block text-sm">{{ t('history.goChart') }}</RouterLink>
    </div>

    <!-- 桌面：细线表格 -->
    <table v-if="charts.history.length" class="dtable mt-2 hidden md:table">
      <thead>
        <tr>
          <th class="w-[16%]">{{ t('history.time') }}</th>
          <th class="w-[24%]">{{ t('history.system') }}</th>
          <th>{{ t('history.board') }}</th>
          <th class="w-[18%] text-right">{{ t('history.action') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rec in charts.history" :key="rec.id">
          <td class="tabular text-muted whitespace-nowrap">{{ rec.createdAt ? fmt(rec.createdAt) : '' }}</td>
          <td>
            <RouterLink :to="`/result?id=${rec.id}`" class="text-ink hover:underline" @click="open(rec.id)">{{ systemLabel(rec) }}</RouterLink>
          </td>
          <td class="text-ink-2">
            {{ boardSummary(rec) || '—' }}
          </td>
          <td class="text-right">
            <RouterLink :to="`/result?id=${rec.id}`" class="link-underline text-[13px]" @click="open(rec.id)">{{ t('history.view') }}</RouterLink>
            <button type="button" class="ml-4 text-[13px] text-muted hover:text-danger" :aria-label="t('history.delete')" :disabled="busy" @click="removeRecord(rec.id)">
              {{ t('history.delete') }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 手机：两行式列表 -->
    <ul v-if="charts.history.length" class="md:hidden">
      <li
        v-for="rec in charts.history"
        :key="rec.id"
        class="flex min-h-[64px] items-center gap-2 border-b border-line py-3"
      >
        <RouterLink :to="`/result?id=${rec.id}`" class="min-w-0 flex-1" @click="open(rec.id)">
          <p class="flex items-baseline justify-between gap-3">
            <span class="truncate text-[15px] font-medium">{{ systemLabel(rec) }}</span>
            <span class="shrink-0 text-xs text-muted tabular">{{ fmt(rec.createdAt) }}</span>
          </p>
          <p class="mt-0.5 text-xs text-muted">
            <template v-if="chartSubtitle(rec.chart)">{{ chartSubtitle(rec.chart) }}</template>
            <template v-else>{{ systemLabel(rec) }}</template>
          </p>
        </RouterLink>
        <button
          type="button"
          class="min-h-11 shrink-0 px-2 text-[13px] text-muted hover:text-danger"
          :aria-label="t('history.delete')"
          :disabled="busy"
          @click="removeRecord(rec.id)"
        >
          {{ t('history.delete') }}
        </button>
      </li>
    </ul>
  </div>
</template>
