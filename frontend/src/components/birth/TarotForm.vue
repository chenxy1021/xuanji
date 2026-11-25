<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createChart } from '@/api/client'
import type { SpreadInfo } from '@/api/types'
import { t } from '@/i18n'

const props = withDefaults(defineProps<{ submitting?: boolean }>(), { submitting: false })
const emit = defineEmits<{ submit: [{ options: Record<string, unknown>; title: string }] }>()

const SPREADS: { id: string; name: string; description: string }[] = [
  { id: 'single', name: '单张牌', description: '针对一个问题，看当下的核心讯息' },
  { id: 'three', name: '三张牌', description: '过去、现在、未来的时间线' },
  { id: 'five', name: '五张牌', description: '现状、阻力、助力、建议、结果' },
  { id: 'celtic', name: '凯尔特十字', description: '十个位置的完整牌阵，适合复杂问题' },
]

const spread = ref('three')
const question = ref('')
const seed = ref(Date.now() % 1_000_000_000)
const quickRefs = ref<Record<string, SpreadInfo>>({})
const error = ref('')

onMounted(async () => {
  // 牌阵说明以服务端为准；失败就用本地兜底文案
  try {
    const env = await createChart('tarot', { options: { spread: 'single', seed: 1 } })
    quickRefs.value = (env.input as { available_spreads?: Record<string, SpreadInfo> }).available_spreads ?? {}
  } catch {
    /* 忽略 */
  }
})

const spreads = computed(() =>
  SPREADS.map((s) => ({
    ...s,
    description: quickRefs.value[s.id]?.description ?? s.description,
    count: quickRefs.value[s.id]?.count,
  })),
)

function reroll() {
  seed.value = Math.floor(Math.random() * 1_000_000_000)
}

function submit() {
  error.value = ''
  emit('submit', {
    options: { spread: spread.value, question: question.value.trim(), seed: seed.value },
    title: t('tarot.title', { name: spreads.value.find((s) => s.id === spread.value)?.name ?? spread.value }),
  })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <section>
      <div class="form-label">{{ t('tarot.spread') }}</div>
      <div class="choice-grid choice-grid--2">
        <button
          v-for="s in spreads"
          :key="s.id"
          type="button"
          class="choice"
          :class="{ 'is-on': spread === s.id }"
          :aria-pressed="spread === s.id"
          @click="spread = s.id"
        >
          <span class="flex items-center justify-between">
            <span class="text-sm font-medium">{{ s.name }}</span>
            <span v-if="s.count" class="text-[13px] text-muted">{{ t('tarot.cards', { n: s.count }) }}</span>
          </span>
          <span class="mt-1 block text-xs leading-5 text-muted">{{ s.description }}</span>
        </button>
      </div>
    </section>

    <section>
      <div class="form-label">{{ t('tarot.question') }}</div>
      <textarea
        v-model="question"
        class="field resize-none"
        rows="3"
        maxlength="200"
        :placeholder="t('tarot.placeholder')"
      />
    </section>

    <section class="flex min-h-[60px] items-center justify-between gap-3">
      <div>
        <p class="text-sm">{{ t('tarot.seed') }}</p>
        <p class="text-xs text-muted">{{ t('tarot.seedHint') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <input v-model.number="seed" type="number" class="field tabular w-28" :aria-label="t('tarot.seed')" />
        <button type="button" class="btn-secondary shrink-0" @click="reroll">
          {{ t('tarot.reroll') }}
        </button>
      </div>
    </section>

    <button type="submit" class="btn-primary" :disabled="props.submitting">
      {{ props.submitting ? t('tarot.drawing') : t('tarot.start') }}
    </button>
  </form>
</template>
