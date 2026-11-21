<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createChart } from '@/api/client'
import { t } from '@/i18n'

const props = withDefaults(defineProps<{ submitting?: boolean }>(), { submitting: false })
const emit = defineEmits<{ submit: [{ options: Record<string, unknown>; title: string }] }>()

type Method = 'coins' | 'time' | 'number'
const METHODS: { id: Method; name: string; description: string }[] = [
  { id: 'coins', name: '铜钱摇卦', description: '摇六次，自下而上记录 6/7/8/9' },
  { id: 'time', name: '时间起卦', description: '以当前/指定年月日时起卦（梅花易数法）' },
  { id: 'number', name: '数字起卦', description: '报两个正整数，以数取卦与动爻' },
]

const method = ref<Method>('coins')
// 六爻自下而上：6 老阴 / 7 少阳 / 8 少阴 / 9 老阳
const LINES = [
  { value: 6, label: '6 老阴' },
  { value: 7, label: '7 少阳' },
  { value: 8, label: '8 少阴' },
  { value: 9, label: '9 老阳' },
]
const lines = ref<number[]>([7, 8, 7, 8, 9, 6])
const numbers = ref<[number, number]>([7, 13])
const question = ref('')
const error = ref('')
const methods = ref(METHODS)

onMounted(async () => {
  try {
    const env = await createChart('liuyao', { options: { method: 'time' } })
    const available = (env.input as { available_methods?: Record<string, { name: string; description: string }> })
      .available_methods
    if (available) methods.value = METHODS.map((m) => ({ ...m, ...available[m.id] }))
  } catch {
    /* 说明文字以本地兜底 */
  }
})

const currentMethod = computed(() => methods.value.find((m) => m.id === method.value))

function shake() {
  lines.value = Array.from({ length: 6 }, () => [7, 8, 7, 8, 6, 9][Math.floor(Math.random() * 6)])
}

function submit() {
  error.value = ''
  if (method.value === 'number' && (!(numbers.value[0] > 0) || !(numbers.value[1] > 0))) {
    error.value = t('liuyao.badNumbers')
    return
  }
  const options: Record<string, unknown> = { method: method.value, question: question.value.trim() }
  if (method.value === 'coins') options.lines = [...lines.value]
  if (method.value === 'number') options.numbers = [...numbers.value]
  emit('submit', { options, title: t('liuyao.title', { name: currentMethod.value?.name ?? t('liuyao.castFallback') }) })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <div class="mb-2 text-[13px] text-ink-2">{{ t('liuyao.method') }}</div>
      <div class="grid gap-2 sm:grid-cols-3">
        <button
          v-for="m in methods"
          :key="m.id"
          type="button"
          class="rounded-[var(--radius-md)] border p-3 text-left"
          :class="method === m.id ? 'border-primary bg-primary-soft' : 'border-line-strong bg-surface'"
          :aria-pressed="method === m.id"
          @click="method = m.id"
        >
          <span class="block text-sm font-medium" :class="method === m.id ? 'text-primary' : ''">{{ m.name }}</span>
          <span class="mt-1 block text-xs leading-[1.45] text-muted">{{ m.description }}</span>
        </button>
      </div>
    </div>

    <div v-if="method === 'coins'">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-[13px] text-ink-2">{{ t('liuyao.lines') }} <span class="text-xs text-muted">{{ t('liuyao.bottomUp') }}</span></span>
        <button type="button" class="btn-ghost" @click="shake">{{ t('liuyao.shake') }}</button>
      </div>
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <label v-for="(_, i) in lines" :key="i" class="flex items-center gap-2 text-xs text-muted">
          {{ t('liuyao.line', { n: i + 1 }) }}
          <select v-model.number="lines[i]" class="field !h-11 min-w-0 flex-1 !text-sm" :aria-label="t('liuyao.lineAria', { n: i + 1 })">
            <option v-for="l in LINES" :key="l.value" :value="l.value">{{ l.label }}</option>
          </select>
        </label>
      </div>
    </div>

    <div v-else-if="method === 'number'" class="grid grid-cols-2 gap-2">
      <label class="text-xs text-muted">
        {{ t('liuyao.first') }}
        <input v-model.number="numbers[0]" type="number" min="1" class="field tabular mt-1" />
      </label>
      <label class="text-xs text-muted">
        {{ t('liuyao.second') }}
        <input v-model.number="numbers[1]" type="number" min="1" class="field tabular mt-1" />
      </label>
    </div>

    <p v-else class="rounded-[var(--radius-sm)] bg-bg-subtle px-2.5 py-2 text-xs leading-[1.6] text-muted">
      {{ t('liuyao.timeNote') }}
    </p>

    <div>
      <div class="mb-2 text-[13px] text-ink-2">{{ t('liuyao.question') }}</div>
      <textarea v-model="question" class="field resize-none" rows="2" maxlength="200" :placeholder="t('liuyao.placeholder')" />
    </div>

    <p v-if="error" class="flex items-center gap-1.5 text-xs text-danger">
      <span class="flex size-4 items-center justify-center rounded-full border border-danger text-[10px]" aria-hidden="true">!</span>
      {{ error }}
    </p>

    <button type="submit" class="btn-primary" :disabled="props.submitting">
      {{ props.submitting ? t('liuyao.casting') : t('liuyao.start') }}
    </button>
  </form>
</template>
