<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createChart, createRecord, getSystems } from '@/api/client'
import type { ChartBody } from '@/api/client'
import type { SystemSpec } from '@/api/types'
import type { HistoryRecord } from '@/api/types'
import BirthForm from '@/components/birth/BirthForm.vue'
import LiuyaoForm from '@/components/birth/LiuyaoForm.vue'
import MbtiForm from '@/components/birth/MbtiForm.vue'
import OptionForm from '@/components/birth/OptionForm.vue'
import TarotForm from '@/components/birth/TarotForm.vue'
import { useBirthStore, useSecondaryStore } from '@/stores/birth'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { newGuestId, saveGuestRecord } from '@/lib/guestRecords'
import { collectOptions, todayLabel } from '@/lib/options'
import { t } from '@/i18n'
import { systemMethod, systemName, systemTagline } from '@/i18n/terms'

const props = defineProps<{ system: string }>()
const router = useRouter()
const birthStore = useBirthStore()
const secondaryStore = useSecondaryStore()
const charts = useChartsStore()
const auth = useAuthStore()

const spec = ref<SystemSpec | null>(null)
// 体系列表不含未注册 id：用 settled 区分「还在拉取」和「确实没有这个体系」
const settled = ref(false)
const submitting = ref(false)
const error = ref('')
const showSecond = ref(false)
const extraOptions = ref<Record<string, unknown>>({})

const title = computed(() => (spec.value ? systemName(spec.value) : ''))
const sysName = computed(() => (spec.value ? systemName(spec.value) : ''))
const sysTagline = computed(() => (spec.value ? systemTagline(spec.value) : ''))
const methods = computed(() => (spec.value ? systemMethod(spec.value.id) : []))

getSystems()
  .then((list) => {
    spec.value = list.find((s) => s.id === props.system) ?? null
    settled.value = true
  })
  .catch((e) => {
    error.value = (e as Error).message
  })
  .finally(() => (settled.value = true))

function makeTitle() {
  const b = birthStore.birth
  return `${b.year}-${String(b.month).padStart(2, '0')}-${String(b.day).padStart(2, '0')} ${sysName.value}`
}

async function submit(body: ChartBody, title: string) {
  error.value = ''
  submitting.value = true
  try {
    const envelope = await createChart(props.system, body)
    await auth.bootstrap()
    let record: HistoryRecord
    if (auth.isLoggedIn) {
      record = await createRecord({ ...envelope, title })
      charts.addRecord(record)
    } else {
      // 未登录不落库：记录只写当前浏览器的 localStorage
      record = { ...envelope, id: newGuestId(), createdAt: Date.now(), title }
      saveGuestRecord(record)
    }
    charts.remember(record)
    router.push(`/result?id=${record.id}`)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    submitting.value = false
  }
}

function submitBirth() {
  if (spec.value?.requires_secondary) {
    submit({ birth: birthStore.birth, secondary: secondaryStore.birth, options: {} }, `${makeTitle()} · ${t('cat.synastry')}`)
    return
  }
  const fields = spec.value?.fields ?? []
  const { options, error: e } = collectOptions(fields, extraOptions.value)
  if (e) {
    error.value = e
    return
  }
  submit({ birth: birthStore.birth, options }, makeTitle())
}

function submitOptions(payload: { options: Record<string, unknown>; title: string }) {
  submit({ options: payload.options }, payload.title)
}

const personTabs = computed(() => [
  { label: t('chart.personA'), on: false },
  { label: t('chart.personB'), on: true },
])
const formTitle = computed(() => (showSecond.value ? t('chart.personB') : t('chart.personA')))

type Route = 'tarot' | 'liuyao' | 'mbti' | 'synastry' | 'options' | 'birth' | 'option-birth'
const route = computed<Route | null>(() => {
  const s = spec.value
  if (!s || s.status === 'planned') return null
  if (s.id === 'tarot') return 'tarot'
  if (s.id === 'liuyao') return 'liuyao'
  if (s.id === 'mbti') return 'mbti'
  if (s.requires_secondary) return 'synastry'
  if (s.requires_birth) return s.fields?.length ? 'option-birth' : 'birth'
  if (s.fields?.length) return 'options'
  return 'options'
})

// 生辰类可追加额外业务字段（目前没有体系同时用生辰和字段）
const extraFields = computed(() =>
  route.value === 'option-birth' ? (spec.value?.fields ?? []) : [],
)
const today = todayLabel()
</script>

<template>
  <div>
    <RouterLink to="/" class="link-underline mb-5 hidden text-[13px] text-ink-2 lg:inline-flex">← {{ t('chart.back') }}</RouterLink>
    <RouterLink to="/" class="mb-4 -ml-2.5 flex size-11 items-center justify-center text-ink-2 lg:hidden" :aria-label="t('chart.back')">
      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m15 5-7 7 7 7" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </RouterLink>

    <template v-if="spec">
      <div v-if="!route" class="border-l border-line-strong pl-4 text-sm leading-[1.7] text-muted">
        {{ t('chart.planned', { name: sysName }) }}
        <RouterLink to="/" class="btn-ghost mt-1">{{ t('chart.toHome') }}</RouterLink>
      </div>
      <div v-else class="chart-grid">
        <aside class="chart-aside order-2 lg:order-none">
          <p class="label hidden lg:block">{{ t('chart.label') }}</p>
          <h1 class="title-serif h-h1 mt-3 hidden lg:block">{{ title }}</h1>
          <p class="mt-4 max-w-[460px] text-[15px] leading-[1.85] text-ink-2">{{ sysTagline }}</p>
          <!-- 用 div 而不是详情折叠：桌面由 CSS 隐藏标题直接展示，手机可点开 -->
          <div v-if="methods.length" class="method-details mt-8 border-t border-line pt-5">
            <p class="label">{{ t('chart.method') }}</p>
            <div class="method-body">
              <ol class="mt-3 max-w-[460px] space-y-2 text-[13px] leading-[1.85] text-muted">
                <li v-for="(m, i) in methods" :key="m" class="flex gap-3">
                  <span class="tabular shrink-0 text-[13px]">{{ String(i + 1).padStart(2, '0') }}</span>
                  <span>{{ m }}</span>
                </li>
              </ol>
              <p class="method-note mt-4 max-w-[460px] text-[12px] leading-[1.8] text-muted">{{ t('chart.methodNote') }}</p>
            </div>
          </div>
        </aside>

        <div class="chart-form order-1 min-w-0 lg:order-none">
          <div class="mb-5 border-b border-line pb-3 lg:hidden">
            <p class="label">{{ t('chart.label') }}</p>
            <h1 class="title-serif mt-2 text-[26px] leading-[1.3]">{{ title }}</h1>
          </div>
          <p class="mb-5 border-b border-line pb-3 text-xs leading-[1.6] text-muted lg:hidden">{{ sysTagline }}</p>
          <div v-if="route === 'synastry'" class="seg seg-equal seg-wide mb-4">
            <button
              v-for="tab in personTabs"
              :key="tab.label"
              type="button"
              :class="{ 'is-on': showSecond === tab.on }"
              :aria-pressed="showSecond === tab.on"
              @click="showSecond = tab.on"
            >
              {{ tab.label }}
            </button>
          </div>
          <p v-if="route === 'synastry'" class="mb-3 text-xs text-muted">{{ t('chart.filling', { name: formTitle }) }}</p>

          <TarotForm v-if="route === 'tarot'" :submitting="submitting" @submit="submitOptions" />
          <LiuyaoForm v-else-if="route === 'liuyao'" :submitting="submitting" @submit="submitOptions" />
          <MbtiForm v-else-if="route === 'mbti'" :submitting="submitting" @submit="submitOptions" />
          <OptionForm
            v-else-if="route === 'options'"
            :fields="spec.fields ?? []"
            :name="sysName"
            :submitting="submitting"
            :submit-label="t('chart.start', { name: sysName })"
            @submit="submitOptions"
          />
          <BirthForm
            v-else-if="showSecond"
            v-model="secondaryStore.birth"
            :submit-label="t('chart.saveB')"
            @submit="showSecond = false"
          />
          <BirthForm
            v-else-if="route === 'birth' || route === 'synastry' || route === 'option-birth'"
            v-model="birthStore.birth"
            :submitting="submitting"
            :submit-label="spec.requires_secondary ? t('chart.startSynastry') : t('chart.startChart', { name: sysName })"
            @submit="submitBirth"
          />
          <OptionForm
            v-if="route === 'option-birth' && !showSecond"
            :fields="extraFields"
            :name="sysName"
            :hint="t('chart.extraHint', { date: today })"
            @submit="(p) => (extraOptions = p.options)"
          />
        </div>
      </div>
      <p v-if="error" class="mt-6 border-l border-danger pl-3 text-xs leading-[1.6] text-danger" role="alert">
        {{ error }}
      </p>
    </template>
    <p v-else-if="error" class="border-l border-danger pl-3 text-sm leading-[1.7] text-danger">
      {{ error }}
    </p>
    <p v-else-if="!settled" class="animate-pulse text-sm text-muted">{{ t('chart.loading') }}</p>
    <div v-else class="border-l border-line-strong pl-4 text-sm leading-[1.7] text-muted">
      {{ t('chart.planned', { name: props.system }) }}
      <RouterLink to="/" class="btn-ghost mt-1">{{ t('chart.toHome') }}</RouterLink>
    </div>
  </div>
</template>
