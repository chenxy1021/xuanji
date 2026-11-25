<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { searchCities } from '@/api/client'
import type { Place } from '@/api/types'
import { t } from '@/i18n'
import { zh } from '@/i18n/zh'
import { en } from '@/i18n/en'

const model = defineModel<Place | null>({ required: true })

/** 手动坐标写入的 province 值（中英各一份，用于跨语言识别） */
const MANUAL_LABELS = new Set([zh['place.manual'], en['place.manual']])
const isManualPlace = (p: Place | null) => !!p && MANUAL_LABELS.has(p.province)

const label = (p: Place | null) => {
  if (!p) return ''
  if (isManualPlace(p)) return p.name || t('place.manual')
  return `${p.province} ${p.name}`
}

const query = ref(label(model.value))
const results = ref<Place[]>([])
const open = ref(false)
const loading = ref(false)
const error = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
let controller: AbortController | undefined

watch(query, (q) => {
  clearTimeout(timer)
  if (q.trim() === label(model.value)) return
  if (model.value) model.value = null
  controller?.abort()
  // 新搜索开始就重开：输入时先 blur 关掉的下拉，不能被迟到的结果再打开
  open.value = true
  if (!q.trim()) {
    results.value = []
    open.value = false
    return
  }
  timer = setTimeout(async () => {
    controller = new AbortController()
    loading.value = true
    error.value = ''
    try {
      results.value = await searchCities(q.trim(), controller.signal)
    } catch (e) {
      if ((e as Error).name !== 'AbortError') error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }, 300)
})

function select(place: Place) {
  model.value = place
  query.value = label(place)
  open.value = false
}

function clear() {
  model.value = null
  query.value = ''
  results.value = []
  open.value = false
}

function closeSoon() {
  setTimeout(() => (open.value = false), 150)
}

/* ---------------- 手动坐标 ---------------- */
const manualOpen = ref(false)
const mLon = ref('')
const mLat = ref('')
const mTz = ref('8')
const mName = ref('')
const mErrors = reactive({ lon: '', lat: '', tz: '' })

const NUM_RE = /^[+-]?(\d+(\.\d*)?|\.\d+)$/

function parseNumber(raw: string): number {
  const s = raw.trim()
  if (!s || !NUM_RE.test(s)) return NaN
  return Number(s)
}

function resetManual() {
  mLon.value = ''
  mLat.value = ''
  mTz.value = '8'
  mName.value = ''
  mErrors.lon = ''
  mErrors.lat = ''
  mErrors.tz = ''
}

function openManual() {
  clearTimeout(timer)
  controller?.abort()
  loading.value = false
  open.value = false
  results.value = []
  error.value = ''
  resetManual()
  if (model.value) {
    mLon.value = String(model.value.longitude)
    mLat.value = String(model.value.latitude)
    if (typeof model.value.timezone === 'number') mTz.value = String(model.value.timezone)
    mName.value = isManualPlace(model.value) ? model.value.name : ''
  }
  manualOpen.value = true
}

function closeManual() {
  manualOpen.value = false
  resetManual()
}

function confirmManual() {
  mErrors.lon = ''
  mErrors.lat = ''
  mErrors.tz = ''

  const lon = parseNumber(mLon.value)
  const lat = parseNumber(mLat.value)
  const tzRaw = mTz.value.trim()
  const tz = tzRaw === '' ? 8 : parseNumber(tzRaw)
  let ok = true

  if (Number.isNaN(lon)) {
    mErrors.lon = t('place.errNum')
    ok = false
  } else if (lon < -180 || lon > 180) {
    mErrors.lon = t('place.errLon')
    ok = false
  }

  if (Number.isNaN(lat)) {
    mErrors.lat = t('place.errNum')
    ok = false
  } else if (lat < -90 || lat > 90) {
    mErrors.lat = t('place.errLat')
    ok = false
  }

  if (Number.isNaN(tz)) {
    mErrors.tz = t('place.errNum')
    ok = false
  } else if (tz < -12 || tz > 14) {
    mErrors.tz = t('place.errTz')
    ok = false
  }

  if (!ok) return

  const name = mName.value.trim() || t('place.manual')
  model.value = {
    name,
    province: t('place.manual'),
    longitude: lon,
    latitude: lat,
    timezone: tz,
  }
  query.value = name
  manualOpen.value = false
  resetManual()
}

const tzText = computed(() => {
  const tz = model.value?.timezone
  if (typeof tz !== 'number' || !Number.isFinite(tz)) return ''
  const sign = tz < 0 ? '-' : '+'
  const abs = Math.abs(tz)
  const h = Math.floor(abs)
  const m = Math.round((abs - h) * 60)
  return m ? `UTC${sign}${h}:${String(m).padStart(2, '0')}` : `UTC${sign}${h}`
})

/** 外部重置/切换记录时，回到搜索模式并清空手动草稿 */
watch(model, (p) => {
  clearTimeout(timer)
  controller?.abort()
  loading.value = false
  open.value = false
  results.value = []
  error.value = ''
  manualOpen.value = false
  resetManual()
  query.value = label(p)
})
</script>

<template>
  <div class="relative">
    <!-- 搜索模式 -->
    <template v-if="!manualOpen">
      <div class="flex gap-2">
        <input
          v-model="query"
          class="field"
          type="search"
          :placeholder="t('place.search')"
          autocomplete="off"
          :aria-label="t('birth.place')"
          @focus="results.length && (open = true)"
          @blur="closeSoon"
        />
        <button
          v-if="model"
          type="button"
          class="btn-secondary shrink-0"
          @mousedown.prevent
          @click="clear"
        >
          {{ t('place.clear') }}
        </button>
      </div>

      <p v-if="model" class="tabular mt-2 text-xs text-muted" data-manual-place>
        {{ t('place.coord', { lon: model.longitude.toFixed(3), lat: model.latitude.toFixed(3) }) }}
        <template v-if="tzText"> · {{ tzText }}</template>
      </p>

      <div class="mt-1 flex items-center justify-between gap-2">
        <p v-if="!model && !query" class="text-xs text-muted">{{ t('place.optional') }}</p>
        <button
          type="button"
          class="link-underline -mx-2 ml-auto flex min-h-11 items-center gap-1.5 px-2 text-xs text-ink-2"
          @click="openManual"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
            <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
            <circle cx="12" cy="12" r="5" />
            <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
          </svg>
          {{ t('place.manualEntry') }}
        </button>
      </div>

      <p v-if="error" class="mt-2 flex items-center gap-1.5 text-xs text-danger">
        <span class="flex size-4 items-center justify-center rounded-full border border-danger text-[12px]" aria-hidden="true">!</span>
        {{ error }}
      </p>

      <ul
        v-if="open && (results.length || loading)"
        @mousedown.prevent
        class="absolute inset-x-0 z-20 mt-6 overflow-hidden rounded-[var(--radius-sm)] border border-line-strong bg-surface shadow-[var(--shadow-md)]"
      >
        <li v-if="loading" class="px-3 py-3 text-sm text-muted">{{ t('place.loading') }}</li>
        <li v-for="(p, i) in results" :key="p.name + p.province" :class="i ? 'border-t border-line' : ''">
          <button
            type="button"
            class="flex min-h-11 w-full items-center gap-2 px-3 text-left text-sm active:bg-surface-2"
            @mousedown.prevent="select(p)"
          >
            <span>{{ p.name }}</span>
            <span class="ml-auto text-xs text-muted">{{ p.province }}</span>
          </button>
        </li>
      </ul>
    </template>

    <!-- 手动坐标模式 -->
    <div v-else class="border border-line-strong bg-surface-2 p-3">
      <div class="mb-2 flex items-center justify-between gap-2">
        <span class="text-[13px] text-ink">{{ t('place.manualTitle') }}</span>
        <button
          type="button"
          class="link-underline -my-2 -mr-1 flex min-h-11 items-center px-1 text-xs text-ink-2"
          @click="closeManual"
        >
          {{ t('place.back') }}
        </button>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <label class="block">
          <span class="mb-1 block text-xs text-ink-2">{{ t('place.lon') }}</span>
          <input
            v-model="mLon"
            class="field tabular"
            inputmode="decimal"
            autocomplete="off"
            placeholder="-180 ~ 180"
            :aria-label="t('place.lon')"
            :aria-invalid="!!mErrors.lon"
            @input="mErrors.lon = ''"
            @keydown.enter.prevent="confirmManual"
          />
          <span v-if="mErrors.lon" class="mt-1 block text-[13px] leading-[1.45] text-danger">! {{ mErrors.lon }}</span>
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-ink-2">{{ t('place.lat') }}</span>
          <input
            v-model="mLat"
            class="field tabular"
            inputmode="decimal"
            autocomplete="off"
            placeholder="-90 ~ 90"
            :aria-label="t('place.lat')"
            :aria-invalid="!!mErrors.lat"
            @input="mErrors.lat = ''"
            @keydown.enter.prevent="confirmManual"
          />
          <span v-if="mErrors.lat" class="mt-1 block text-[13px] leading-[1.45] text-danger">! {{ mErrors.lat }}</span>
        </label>
      </div>

      <div class="mt-2 grid grid-cols-[110px_1fr] gap-2">
        <label class="block">
          <span class="mb-1 block text-xs text-ink-2">{{ t('place.tz') }}</span>
          <input
            v-model="mTz"
            class="field tabular"
            inputmode="decimal"
            autocomplete="off"
            placeholder="8"
            :aria-label="t('place.tz')"
            :aria-invalid="!!mErrors.tz"
            @input="mErrors.tz = ''"
            @keydown.enter.prevent="confirmManual"
          />
          <span v-if="mErrors.tz" class="mt-1 block text-[13px] leading-[1.45] text-danger">! {{ mErrors.tz }}</span>
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-ink-2">{{ t('place.name') }}</span>
          <input
            v-model="mName"
            class="field"
            type="text"
            autocomplete="off"
            :placeholder="t('place.namePlaceholder')"
            :aria-label="t('place.name')"
            @keydown.enter.prevent="confirmManual"
          />
        </label>
      </div>

      <p class="mt-2 text-xs leading-[1.5] text-muted">{{ t('place.manualHint') }}</p>

      <button type="button" class="btn-secondary mt-3 w-full" @click="confirmManual">
        {{ t('place.confirm') }}
      </button>
    </div>
  </div>
</template>
