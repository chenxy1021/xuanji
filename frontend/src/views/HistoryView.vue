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
  loading.value = true
  try {
    if (auth.isLoggedIn) await charts.loadFromServer()
    else charts.loadLocal()
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
  <div class="history-page">
    <div class="flex items-end justify-between gap-4 border-b border-line pb-5">
      <div>
        <h1 class="title-serif h-h1">{{ t('history.title') }}</h1>
        <p class="mt-2 text-xs text-muted">{{ auth.isLoggedIn ? t('history.onlineNote') : t('history.note') }}</p>
      </div>
      <button
        v-if="charts.history.length"
        type="button"
        class="btn-danger shrink-0"
        :disabled="busy"
        @click="clearAll"
      >
        {{ t('history.clearAll') }}
      </button>
    </div>

    <p v-if="error" class="mt-4 border-l-2 border-danger pl-3 text-[13px] leading-[1.6] text-danger" role="alert" data-history-error>
      {{ error }}
    </p>

    <p v-if="loading && !charts.history.length" class="animate-pulse border-t border-line py-10 text-sm text-muted">{{ t('common.loading') }}</p>

    <div v-else-if="!charts.history.length" class="border-t border-line py-10">
      <p class="text-sm text-muted">{{ t('history.empty') }}</p>
      <RouterLink to="/chart/bazi" class="let-action mt-2">{{ t('history.goChart') }}</RouterLink>
    </div>

    <!-- 桌面：细线表格 -->
    <table v-if="charts.history.length" class="dtable hist-table">
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
            <RouterLink :to="`/result?id=${rec.id}`" class="text-ink underline-offset-4 hover:underline" @click="open(rec.id)">{{ systemLabel(rec) }}</RouterLink>
          </td>
          <td class="text-ink-2">
            {{ boardSummary(rec) || '—' }}
          </td>
          <td class="text-right">
            <RouterLink :to="`/result?id=${rec.id}`" class="let-action text-[13px] !min-h-0" @click="open(rec.id)">{{ t('history.view') }}</RouterLink>
            <button type="button" class="let-action ml-2 text-[13px] !min-h-0 hover:text-danger" :aria-label="t('history.delete')" :disabled="busy" @click="removeRecord(rec.id)">
              {{ t('history.delete') }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 手机：两行式列表 -->
    <ul v-if="charts.history.length" class="hist-list">
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
          <p v-if="chartSubtitle(rec.chart)" class="mt-0.5 text-xs text-muted">{{ chartSubtitle(rec.chart) }}</p>
        </RouterLink>
        <button
          type="button"
          class="let-action shrink-0 text-[13px] hover:text-danger"
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
