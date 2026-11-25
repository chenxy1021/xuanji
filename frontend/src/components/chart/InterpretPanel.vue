<script setup lang="ts">
import { marked } from 'marked'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ApiError, getFocusTopics, getMeta, getReading, saveReading, streamInterpret, type FocusTopic } from '@/api/client'
import { t, useLocale } from '@/i18n'
import { isEn } from '@/i18n/terms'
import { findGuestRecord, getGuestReading, saveGuestReading } from '@/lib/guestRecords'
import { loadLocalLlm } from '@/lib/llmConfig'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ recordId: string; system: string; chart: unknown; text: string }>()

const QUESTION_MAX = 500
const auth = useAuthStore()
const DEFAULT_PRESETS = ['今年事业运势如何？', '我的性格特点与优势', '感情与婚姻建议', '适合的行业方向']
const PRESETS_BY_SYSTEM: Record<string, string[]> = {
  kongming: ['这支签对我所问之事怎么说？', '我最该注意什么？', '近期整体运势'],
  qimen: ['一生的格局与事业方向', '财运与求财方式', '感情与婚姻'],
}
const PRESETS_EN: Record<string, string[]> = {
  kongming: ['What does this lot say about my question?', 'What should I watch out for?', 'My near-term outlook'],
  qimen: ['Overall pattern and career direction', 'Wealth and how to earn it', 'Love and marriage'],
}

const locale = useLocale()
const presets = computed(() =>
  isEn()
    ? (PRESETS_EN[props.system] ?? ['How is my career this year?', 'My strengths and blind spots', 'Love and marriage advice', 'Which industries suit me'])
    : (PRESETS_BY_SYSTEM[props.system] ?? DEFAULT_PRESETS),
)

const topics = ref<FocusTopic[]>([])
const focus = ref<string[]>([])
const question = ref('')
const style = ref<'concise' | 'detailed'>('concise')
const output = ref('')
const running = ref(false)
const error = ref<{ code: string; message: string } | null>(null)
const llmOff = ref(false)
const copied = ref(false)
const saved = ref(false)
let controller: AbortController | null = null
let restoreSeq = 0

const topicLabel = (topic: FocusTopic) => (locale.value === 'en' && topic.label_en ? topic.label_en : topic.label)

function restore() {
  controller?.abort()
  const seq = ++restoreSeq
  running.value = false
  error.value = null
  saved.value = false
  output.value = ''
  style.value = 'concise'
  question.value = ''
  focus.value = []
  const id = props.recordId
  // 未登录、或这张盘本来就是匿名时排的：解读存在浏览器里
  if (!auth.isLoggedIn || findGuestRecord(id)) {
    const record = getGuestReading(id)
    if (record) {
      output.value = record.text
      saved.value = true
      style.value = record.style === 'detailed' ? 'detailed' : 'concise'
      question.value = record.question ?? ''
      focus.value = record.focus
    }
    return
  }
  getReading(id)
    .then((record) => {
      if (seq !== restoreSeq || id !== props.recordId || !record) return
      output.value = record.text
      saved.value = true
      style.value = record.style === 'detailed' ? 'detailed' : 'concise'
      question.value = record.question ?? ''
      focus.value = record.focus
    })
    .catch(() => {
      /* 读取失败按无存档处理，不影响起盘内容 */
    })
}

async function persist() {
  const id = props.recordId
  const body = {
    text: output.value,
    focus: [...focus.value],
    style: style.value,
    question: question.value,
    system: props.system,
  }
  try {
    if (auth.isLoggedIn && !findGuestRecord(id)) await saveReading(id, body)
    else saveGuestReading(id, body)
    // 保存期间已切到别的记录就不显示标识
    if (id === props.recordId) saved.value = true
  } catch {
    /* 保存失败不打断阅读；不显示「已保存」 */
  }
}

// 未配密钥时提前说明，避免用户点「开始解读」才发现不可用。
// 用 watch 而不是 onMounted：同一路由换一条记录时组件会被复用，方向目录要跟着换。
watch(
  () => props.system,
  async (system) => {
    const [meta, catalog] = await Promise.allSettled([getMeta(), getFocusTopics(system)])
    if (system !== props.system) return // 快速切换体系时丢弃旧响应
    // 浏览器里保存了自己的模型配置时，即使本站默认没配也能解读
    const hasLocal = !!loadLocalLlm()
    llmOff.value = meta.status === 'fulfilled' ? !hasLocal && !meta.value.llm_configured : !hasLocal
    if (catalog.status === 'fulfilled') {
      topics.value = catalog.value.topics
      // 方向目录晚于恢复返回时，只补上存档里已失效的 id
      focus.value = focus.value.filter((id) => catalog.value.topics.some((x) => x.id === id))
      const overview = catalog.value.topics.find((x) => x.id === 'overview')
      if (!focus.value.length && overview) focus.value = [overview.id]
    }
  },
  { immediate: true },
)

// 换一条盘时恢复它自己的存档，避免张冠李戴；登录状态晚到时也要再试一次
watch([() => props.recordId, () => auth.isLoggedIn], restore, { immediate: true })

const html = computed(() => marked.parse(output.value, { async: false }) as string)

function toggleTopic(id: string) {
  focus.value = focus.value.includes(id) ? focus.value.filter((x) => x !== id) : [...focus.value, id]
}

const allSelected = computed(() => topics.value.length > 0 && focus.value.length === topics.value.length)

function toggleAll() {
  focus.value = allSelected.value ? [] : topics.value.map((x) => x.id)
}

async function run() {
  controller?.abort()
  controller = new AbortController()
  running.value = true
  output.value = ''
  error.value = null
  copied.value = false
  saved.value = false
  let done = false
  const localLlm = loadLocalLlm()
  if (localLlm) llmOff.value = false
  try {
    await streamInterpret(
      {
        system: props.system,
        chart: props.chart,
        question: question.value.trim(),
        style: style.value,
        focus: focus.value,
        lang: locale.value,
        ...(localLlm ? { llm: localLlm } : {}),
      },
      (event, data) => {
        if (event === 'delta') output.value += String(data.text ?? '')
        else if (event === 'done') done = true
        else if (event === 'error') {
          error.value = { code: String(data.code ?? 'error'), message: String(data.message ?? t('ai.failed')) }
        }
      },
      controller.signal,
    )
    if (done && output.value.trim()) await persist()
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    error.value =
      e instanceof ApiError ? { code: e.code, message: e.message } : { code: 'error', message: (e as Error).message }
  } finally {
    running.value = false
  }
}

function stop() {
  controller?.abort()
  running.value = false
}

function usePreset(q: string) {
  question.value = q
  run()
}

async function copyOutput() {
  try {
    await navigator.clipboard.writeText(output.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* 剪贴板不可用时静默 */
  }
}

onBeforeUnmount(stop)
</script>

<template>
  <section class="ai-panel" data-ai-panel>
    <header class="flex flex-wrap items-center gap-2">
      <span class="ai-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7">
          <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z" stroke-linejoin="round" />
        </svg>
      </span>
      <div class="min-w-0">
        <h3 class="text-[14px] font-semibold leading-tight">{{ t('ai.title') }}</h3>
        <p class="mt-0.5 text-[13px] text-muted">{{ t('ai.badge') }}</p>
      </div>
      <div class="seg seg-wide ml-auto" role="group" :aria-label="t('ai.styleAria')">
        <button
          v-for="s in [{ id: 'concise', label: t('ai.concise') }, { id: 'detailed', label: t('ai.detailed') }] as const"
          :key="s.id"
          type="button"
          class="min-w-0 px-3"
          :class="{ 'is-on': style === s.id }"
          :aria-pressed="style === s.id"
          @click="style = s.id"
        >
          {{ s.label }}
        </button>
      </div>
    </header>

    <!-- 方向选择 -->
    <div v-if="topics.length" class="mt-6">
      <div class="flex items-baseline justify-between gap-3">
        <p class="label">{{ t('ai.focusLabel') }}</p>
        <div class="flex flex-wrap items-center justify-end gap-2 text-[13px] text-muted">
          <span class="tabular">{{ t('ai.focusSelected', { n: focus.length }) }}</span>
          <button type="button" class="let-action" @click="toggleAll">
            {{ allSelected ? t('ai.focusNone') : t('ai.focusAll') }}
          </button>
          <button v-if="focus.length" type="button" class="let-action" @click="focus = []">
            {{ t('ai.focusClear') }}
          </button>
        </div>
      </div>
      <p class="mt-1 text-[13px] leading-relaxed text-muted">{{ t('ai.focusHint') }}</p>
      <div class="topic-rail mt-3" role="group" :aria-label="t('ai.focusAria')">
        <button
          v-for="topic in topics"
          :key="topic.id"
          type="button"
          class="topic-chip"
          :class="{ 'is-on': focus.includes(topic.id) }"
          :aria-pressed="focus.includes(topic.id)"
          :data-focus-id="topic.id"
          @click="toggleTopic(topic.id)"
        >
          {{ topicLabel(topic) }}
        </button>
      </div>
    </div>

    <div
      v-if="llmOff"
      class="mt-5 flex gap-2.5 border-l-2 border-line-strong py-1 pl-3 text-xs leading-[1.7] text-ink-2"
      role="status"
    >
      <span class="flex size-4 shrink-0 items-center justify-center border border-line-strong text-[12px] text-muted" aria-hidden="true">!</span>
      <div>
        <p>{{ t('ai.notConfigured') }}</p>
        <p class="mt-1 text-muted">{{ t('ai.notConfiguredHint') }}</p>
        <RouterLink to="/settings#set-ai" class="let-action mt-2 inline-block">
          {{ t('ai.gotoSettings') }}
        </RouterLink>
      </div>
    </div>

    <div class="mt-6">
      <p class="label mb-2">{{ t('ai.questionOptional') }}</p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="p in presets"
          :key="p"
          type="button"
          class="chip min-h-9"
          :disabled="running || llmOff"
          @click="usePreset(p)"
        >
          {{ p }}
        </button>
      </div>

      <textarea
        v-model="question"
        class="field mt-3 resize-none"
        rows="3"
        :maxlength="QUESTION_MAX"
        :placeholder="t('ai.placeholder')"
        :aria-label="t('ai.questionAria')"
      />
      <div class="tabular mt-1 flex items-center justify-between text-[13px] text-muted">
        <span>{{ focus.length ? t('ai.focusSelected', { n: focus.length }) : t('ai.focusHint') }}</span>
        <span>{{ question.length }}/{{ QUESTION_MAX }}</span>
      </div>
    </div>

    <div class="mt-3 flex gap-2">
      <button type="button" class="btn-primary flex-1" :class="{ 'is-off': llmOff }" :disabled="running || llmOff" @click="run">
        <svg
          v-if="running"
          viewBox="0 0 24 24"
          class="size-4 animate-spin"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          aria-hidden="true"
        >
          <path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" />
        </svg>
        {{ running ? t('ai.running') : llmOff ? t('ai.unavailable') : output || error ? t('ai.rerun') : t('ai.start') }}
      </button>
      <button v-if="running" type="button" class="btn-secondary" @click="stop">{{ t('ai.stop') }}</button>
    </div>

    <div
      v-if="error && !(llmOff && error.code === 'llm_not_configured')"
      class="mt-3 flex gap-2 border border-danger px-3 py-2 text-xs leading-[1.6] text-danger"
    >
      <span class="flex size-4 shrink-0 items-center justify-center border border-danger text-[12px]" aria-hidden="true">!</span>
      <div>
        <p v-if="error.code === 'llm_not_configured'">{{ t('ai.notConfigured') }}</p>
        <p v-else>{{ error.message }}</p>
        <p class="mt-1 opacity-80">{{ t('ai.notConfiguredHint') }}</p>
      </div>
    </div>

    <div v-if="output" class="ai-output mt-4" data-ai-output>
      <div class="mb-2 flex items-center justify-between gap-2">
        <p class="label flex items-center gap-2">
          {{ t('ai.output') }}
          <span v-if="saved" class="border border-line px-1.5 py-0.5 text-[12px] font-normal normal-case tracking-normal text-muted">
            {{ t('ai.saved') }}
          </span>
        </p>
        <button type="button" class="btn-ghost !min-h-8 !px-2 text-[13px]" @click="copyOutput">
          {{ copied ? t('ai.copied') : t('ai.copy') }}
        </button>
      </div>
      <div class="markdown" v-html="html" />
      <span v-if="running" class="stream-caret" aria-hidden="true" />
    </div>
    <div v-else-if="running && !error" class="mt-4 space-y-2" aria-live="polite">
      <p class="text-sm text-muted">{{ t('ai.thinking') }}</p>
      <div class="skeleton-line w-11/12" />
      <div class="skeleton-line w-9/12" />
      <div class="skeleton-line w-10/12" />
    </div>
  </section>
</template>
