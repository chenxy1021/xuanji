<script setup lang="ts">
import { computed } from 'vue'
import type { BirthInput, Calendar, Gender, Shichen } from '@/api/types'
import { SHICHEN_HOURS, describeTime, pad } from '@/lib/shichen'
import { t } from '@/i18n'
import { isEn } from '@/i18n/terms'
import PlacePicker from './PlacePicker.vue'

const model = defineModel<BirthInput>({ required: true })

const props = withDefaults(defineProps<{ submitting?: boolean; submitLabel?: string }>(), {
  submitting: false,
  submitLabel: '',
})
const emit = defineEmits<{ submit: [] }>()

const now = new Date()
const years = Array.from({ length: now.getFullYear() - 1899 }, (_, i) => now.getFullYear() - i)
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const days = computed(() =>
  Array.from({ length: new Date(model.value.year, model.value.month, 0).getDate() }, (_, i) => i + 1),
)
// 农历月固定按 30 天列出（闰月以开关表示），具体合法性由后端校验
const lunarDays = Array.from({ length: 30 }, (_, i) => i + 1)
const hours = Array.from({ length: 24 }, (_, i) => i)
const minutes = Array.from({ length: 60 }, (_, i) => i)
const shichenOptions = computed(() =>
  (Object.keys(SHICHEN_HOURS) as Shichen[]).map((zhi) => ({ zhi, label: isEn() ? `${zhi} ${zhiEn[zhi]}` : `${zhi}时` })),
)
const zhiEn: Record<Shichen, string> = {
  子: 'Zi', 丑: 'Chou', 寅: 'Yin', 卯: 'Mao', 辰: 'Chen', 巳: 'Si',
  午: 'Wu', 未: 'Wei', 申: 'Shen', 酉: 'You', 戌: 'Xu', 亥: 'Hai',
}
const LUNAR_MONTHS = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']

const unknownTime = computed({
  get: () => model.value.hour === null && !model.value.shichen,
  set: (v: boolean) => {
    if (v) {
      model.value.hour = null
      model.value.minute = null
      model.value.shichen = null
    } else {
      model.value.hour = now.getHours()
      model.value.minute = now.getMinutes()
    }
  },
})

const timeHint = computed(() =>
  model.value.hour !== null && model.value.minute !== null
    ? describeTime(model.value.hour, model.value.minute, isEn())
    : '',
)

function setCalendar(c: Calendar) {
  model.value.calendar = c
  model.value.is_leap_month = false
  if (c === 'solar' && model.value.day > days.value.length) model.value.day = days.value.length
}

function clampDay() {
  if (model.value.calendar === 'solar' && model.value.day > days.value.length) {
    model.value.day = days.value.length
  }
}

function pickShichen(zhi: Shichen | null) {
  model.value.shichen = zhi
  if (zhi) {
    const [start, end] = SHICHEN_HOURS[zhi]
    model.value.hour = zhi === '子' ? 0 : Math.floor((start + end) / 2)
    model.value.minute = 0
  }
}

function onHourChange(e: Event) {
  model.value.hour = Number((e.target as HTMLSelectElement).value)
  model.value.shichen = null
}

function onMinuteChange(e: Event) {
  model.value.minute = Number((e.target as HTMLSelectElement).value)
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="emit('submit')">
    <div class="seg seg-equal seg-wide" role="group" :aria-label="t('birth.calendar')">
      <button
        v-for="c in [{ id: 'solar', label: t('birth.solar') }, { id: 'lunar', label: t('birth.lunar') }] as const"
        :key="c.id"
        type="button"
        :class="{ 'is-on': model.calendar === c.id }"
        :aria-pressed="model.calendar === c.id"
        @click="setCalendar(c.id)"
      >
        {{ c.label }}
      </button>
    </div>

    <div>
      <div class="form-label">
        {{ t('birth.date') }} <span class="text-xs text-muted">{{ model.calendar === 'solar' ? t('birth.solar') : t('birth.lunar') }}</span>
      </div>
      <div class="grid grid-cols-[1.25fr_1fr_1fr] gap-2">
        <select v-model.number="model.year" class="field" :aria-label="t('birth.year')" @change="clampDay">
          <option v-for="y in years" :key="y" :value="y">{{ y }} {{ t('birth.year') }}</option>
        </select>
        <select v-model.number="model.month" class="field" :aria-label="t('birth.month')" @change="clampDay">
          <option v-for="m in months" :key="m" :value="m">
            {{ model.calendar === 'solar' || isEn() ? `${m} ${t('birth.month')}` : `${LUNAR_MONTHS[m - 1]}月` }}
          </option>
        </select>
        <select v-model.number="model.day" class="field" :aria-label="t('birth.day')">
          <option v-for="d in model.calendar === 'solar' ? days : lunarDays" :key="d" :value="d">{{ d }} {{ t('birth.day') }}</option>
        </select>
      </div>
      <label v-if="model.calendar === 'lunar'" class="mt-2 flex min-h-11 items-center gap-2 text-[13px] text-ink-2">
        <input v-model="model.is_leap_month" type="checkbox" class="check" />
        {{ t('birth.leap') }}
      </label>
    </div>

    <div>
      <div class="form-label">{{ t('birth.time') }} <span class="text-xs text-muted">{{ t('birth.timeOnlyHint') }}</span></div>
      <template v-if="!unknownTime">
        <div class="grid grid-cols-2 gap-2">
          <select :value="model.hour ?? ''" class="field" :aria-label="t('birth.hour')" @change="onHourChange">
            <option v-for="h in hours" :key="h" :value="h">{{ pad(h) }} {{ t('birth.hour') }}</option>
          </select>
          <select :value="model.minute ?? ''" class="field" :aria-label="t('birth.minute')" @change="onMinuteChange">
            <option v-for="m in minutes" :key="m" :value="m">{{ pad(m) }} {{ t('birth.minute') }}</option>
          </select>
        </div>
        <p v-if="timeHint" class="mt-2 border-l-2 border-line-strong px-2.5 py-1 text-xs text-ink-2">
          {{ timeHint }}
        </p>
        <p class="mt-2 text-xs text-muted">{{ t('birth.pickShichen') }}</p>
        <div class="scroll-x mt-1 flex gap-1.5 pb-1">
          <button
            v-for="s in shichenOptions"
            :key="s.zhi"
            type="button"
            class="shichen-chip"
            :class="
              model.shichen === s.zhi
                ? 'is-on'
                : ''
            "
            :aria-pressed="model.shichen === s.zhi"
            @click="pickShichen(model.shichen === s.zhi ? null : s.zhi)"
          >
            {{ s.label }}
          </button>
        </div>
      </template>
      <p v-else class="border-l-2 border-line-strong bg-bg-subtle px-2.5 py-2 text-xs leading-[1.6] text-muted">
        {{ t('birth.unknownTimeNote') }}
      </p>
      <label class="switch-row mt-2">
        <span class="min-w-0">
          <span class="block text-[15px]">{{ t('birth.unknownTime') }}</span>
          <span class="block text-xs leading-[1.45] text-muted">{{ t('birth.unknownTimeHint') }}</span>
        </span>
        <input v-model="unknownTime" type="checkbox" role="switch" class="switch" :aria-label="t('birth.unknownTime')" />
      </label>
    </div>

    <div>
      <div class="form-label">{{ t('birth.place') }} <span class="text-xs text-muted">{{ t('birth.placeHint') }}</span></div>
      <PlacePicker v-model="model.place" />
    </div>

    <div>
      <div class="form-label">{{ t('birth.gender') }}</div>
      <div class="seg seg-equal seg-wide" role="group" :aria-label="t('birth.gender')">
        <button
          v-for="g in [{ id: 'male', label: t('birth.male') }, { id: 'female', label: t('birth.female') }] as { id: Gender; label: string }[]"
          :key="g.id"
          type="button"
          :class="{ 'is-on': model.gender === g.id }"
          :aria-pressed="model.gender === g.id"
          @click="model.gender = g.id"
        >
          {{ g.label }}
        </button>
      </div>
    </div>

    <label class="switch-row border-t border-line pt-3">
      <span class="min-w-0">
        <span class="block text-[15px]">{{ t('birth.trueSolar') }}</span>
        <span class="block text-xs leading-[1.45] text-muted">{{ t('birth.trueSolarHint') }}</span>
      </span>
      <input
        v-model="model.true_solar_time"
        type="checkbox"
        role="switch"
        class="switch"
        :aria-label="t('birth.trueSolar')"
      />
    </label>

    <button type="submit" class="btn-primary" :disabled="props.submitting">
      <svg
        v-if="props.submitting"
        viewBox="0 0 24 24"
        class="size-4 animate-spin"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        aria-hidden="true"
      >
        <path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" />
      </svg>
      {{ props.submitting ? t('birth.submitting') : props.submitLabel || t('option.start') }}
    </button>
  </form>
</template>
