<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getMbtiQuiz } from '@/api/client'
import type { MbtiQuiz } from '@/api/types'
import { t, useLocale } from '@/i18n'
import { isEn } from '@/i18n/terms'

const props = withDefaults(defineProps<{ submitting?: boolean }>(), { submitting: false })
const emit = defineEmits<{ submit: [{ options: Record<string, unknown>; title: string }] }>()

const quiz = ref<MbtiQuiz | null>(null)
const answers = ref<(number | null)[]>([])
const index = ref(0)
const error = ref('')
const locale = useLocale()

async function load() {
  try {
    const data = await getMbtiQuiz(locale.value)
    quiz.value = data
    // 切语言重拉题时保留已选答案
    answers.value = data.questions.map((_, i) => answers.value[i] ?? null)
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(load)
watch(locale, load)

const total = computed(() => quiz.value?.questions.length ?? 0)
const current = computed(() => quiz.value?.questions[index.value])
const answered = computed(() => answers.value.filter((a) => a !== null).length)
const progress = computed(() => (total.value ? Math.round((answered.value / total.value) * 100) : 0))
const allAnswered = computed(() => total.value > 0 && answered.value === total.value)
const labels = computed(() => quiz.value?.scale.labels ?? [])
// 后端 ?lang=en 就绪时 text_lang=en；否则题目仍是中文，加提示
const zhQuestions = computed(() => isEn() && quiz.value?.text_lang !== 'en')

function pick(v: number) {
  answers.value[index.value] = v
  // 选完自动进入下一题，最后一题停在原地
  if (index.value < total.value - 1) {
    setTimeout(() => {
      if (answers.value[index.value] === v) index.value += 1
    }, 160)
  }
}

function step(delta: number) {
  index.value = Math.min(total.value - 1, Math.max(0, index.value + delta))
}

function submit() {
  if (!allAnswered.value) {
    error.value = t('mbti.remainingErr', { n: total.value - answered.value })
    return
  }
  error.value = ''
  emit('submit', { options: { answers: [...answers.value] }, title: t('mbti.title') })
}
</script>

<template>
  <div v-if="quiz" class="space-y-4">
    <div>
      <div class="flex items-baseline justify-between">
        <p class="text-[13px] text-ink-2">{{ t('mbti.progress', { i: index + 1, n: total }) }}</p>
        <p class="tabular text-xs text-muted">{{ t('mbti.answered', { n: answered }) }}</p>
      </div>
      <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-bg-subtle" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100" :aria-label="t('mbti.progressAria')">
        <div class="h-full rounded-full bg-primary transition-[width] duration-200" :style="{ width: `${progress}%` }" />
      </div>
    </div>

    <p v-if="zhQuestions" class="text-xs leading-[1.6] text-muted">{{ t('mbti.zhFallback') }}</p>
    <p class="min-h-[72px] rounded-[var(--radius-md)] bg-surface-2 p-4 font-serif text-[19px] leading-[1.5]">
      {{ current?.text }}
    </p>

    <div class="grid gap-2" role="radiogroup" :aria-label="t('mbti.optionsAria', { i: index + 1 })">
      <button
        v-for="(text, i) in labels"
        :key="text"
        type="button"
        role="radio"
        :aria-checked="answers[index] === i + (quiz.scale.min ?? 1)"
        class="min-h-12 rounded-[var(--radius-md)] border px-4 text-left text-[15px] transition-colors"
        :class="
          answers[index] === i + (quiz.scale.min ?? 1)
            ? 'border-primary bg-primary-soft font-medium text-primary'
            : 'border-line-strong bg-surface text-ink-2 active:bg-surface-2'
        "
        @click="pick(i + (quiz.scale.min ?? 1))"
      >
        {{ text }}
      </button>
    </div>

    <div class="flex gap-2">
      <button type="button" class="btn-secondary flex-1" :disabled="index === 0" @click="step(-1)">{{ t('mbti.prev') }}</button>
      <button type="button" class="btn-secondary flex-1" :disabled="index >= total - 1" @click="step(1)">{{ t('mbti.next') }}</button>
    </div>

    <p v-if="error" class="flex items-center gap-1.5 text-xs text-danger">
      <span class="flex size-4 items-center justify-center rounded-full border border-danger text-[10px]" aria-hidden="true">!</span>
      {{ error }}
    </p>

    <button type="button" class="btn-primary" :disabled="props.submitting || !allAnswered" @click="submit">
      {{ props.submitting ? t('mbti.submitting') : allAnswered ? t('mbti.view') : t('mbti.remaining', { n: total - answered }) }}
    </button>
  </div>
  <p v-else-if="error" class="flex items-center gap-1.5 text-xs text-danger">
    <span class="flex size-4 items-center justify-center rounded-full border border-danger text-[10px]" aria-hidden="true">!</span>
    {{ error }}
  </p>
  <p v-else class="animate-pulse text-sm text-muted">{{ t('mbti.loading') }}</p>
</template>
