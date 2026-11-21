<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { OptionField } from '@/api/types'
import { collectOptions, initialValues, todayLabel } from '@/lib/options'
import { t } from '@/i18n'
import { fieldText } from '@/i18n/terms'

const props = withDefaults(
  defineProps<{
    fields: OptionField[]
    name: string
    submitting?: boolean
    submitLabel?: string
    hint?: string
    /** 嵌在 BirthForm 下方时：只渲染字段，不渲染标题和主按钮 */
    inline?: boolean
  }>(),
  { submitting: false, submitLabel: '', inline: false },
)
const emit = defineEmits<{ submit: [{ options: Record<string, unknown>; title: string }] }>()

// 勾选框的值是 boolean，其余控件要 string | number
const values = ref<Record<string, string | number | boolean>>(initialValues(props.fields))
const error = ref('')
const label = (f: OptionField) => fieldText(f).label
const hint = (f: OptionField) => fieldText(f).hint
const placeholder = (f: OptionField) => fieldText(f).placeholder

// 内联模式下由父组件收集字段值（随输入实时更新）
if (props.inline) watch(values, (v) => emit('submit', { options: { ...v }, title: '' }), { deep: true })

// 标题用今天或所选时刻
const stamp = computed(() => {
  const dt = props.fields.find((f) => f.kind === 'datetime' || f.kind === 'date')
  const raw = dt ? String(values.value[dt.key] ?? '') : ''
  if (!raw) return todayLabel()
  if (dt!.kind === 'datetime') return raw.replace('T', ' ')
  return raw
})

function submit() {
  error.value = ''
  const { options, error: e } = collectOptions(props.fields, values.value)
  if (e) {
    error.value = e
    return
  }
  emit('submit', { options, title: t('option.title', { name: props.name, stamp: stamp.value }) })
}
</script>

<template>
  <form :class="inline ? 'space-y-4 border-b border-line pb-4' : 'space-y-4'" @submit.prevent="submit">
    <p v-if="inline && hint" class="text-xs text-muted">{{ hint }}</p>
    <div v-for="f in fields" :key="f.key">
      <div class="mb-2 text-[13px] text-ink-2">
        {{ label(f) }}
        <span v-if="!f.required" class="text-xs text-muted">{{ t('option.optional') }}</span>
      </div>

      <select
        v-if="f.kind === 'select'"
        v-model="values[f.key]"
        class="field"
        :aria-label="label(f)"
      >
        <option value="">{{ placeholder(f) || t('option.select') }}</option>
        <option v-for="o in fieldText(f).options ?? []" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>

      <textarea
        v-else-if="f.kind === 'textarea'"
        :value="String(values[f.key] ?? '')"
        @input="values[f.key] = ($event.target as HTMLTextAreaElement).value"
        class="field resize-none"
        rows="3"
        :placeholder="placeholder(f)"
        :aria-label="label(f)"
      />

      <input
        v-else-if="f.kind === 'number'"
        v-model="values[f.key]"
        type="number"
        class="field tabular"
        :placeholder="placeholder(f)"
        :aria-label="label(f)"
      />

      <input
        v-else-if="f.kind === 'date'"
        v-model="values[f.key]"
        type="date"
        class="field tabular"
        :aria-label="label(f)"
      />

      <input
        v-else-if="f.kind === 'time'"
        v-model="values[f.key]"
        type="time"
        class="field tabular"
        :aria-label="label(f)"
      />

      <input
        v-else-if="f.kind === 'datetime'"
        v-model="values[f.key]"
        type="datetime-local"
        class="field tabular"
        :aria-label="label(f)"
      />

      <label v-else-if="f.kind === 'toggle'" class="switch-row">
        <span class="text-[15px]">{{ hint(f) || label(f) }}</span>
        <input v-model="values[f.key]" type="checkbox" role="switch" class="switch" :aria-label="label(f)" />
      </label>

      <input
        v-else
        v-model="values[f.key]"
        type="text"
        class="field"
        :placeholder="placeholder(f)"
        :aria-label="label(f)"
      />

      <p v-if="hint(f) && f.kind !== 'toggle'" class="mt-1.5 text-xs text-muted">{{ hint(f) }}</p>
    </div>

    <template v-if="!inline">
      <p v-if="error" class="flex items-center gap-1.5 text-xs text-danger">
        <span class="flex size-4 items-center justify-center rounded-full border border-danger text-[10px]" aria-hidden="true">!</span>
        {{ error }}
      </p>
      <button type="submit" class="btn-primary" :disabled="submitting">
        {{ submitting ? t('option.submitting') : submitLabel || t('option.start') }}
      </button>
    </template>
  </form>
</template>
