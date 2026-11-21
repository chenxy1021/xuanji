<script setup lang="ts">
import { computed } from 'vue'
import type { SystemSpec } from '@/api/types'
import { t } from '@/i18n'
import { systemName, systemTagline } from '@/i18n/terms'

// v2：编号行（无图标块、无卡片底）
const props = withDefaults(defineProps<{ spec: SystemSpec; index?: number }>(), { index: 0 })

const isReady = computed(() => props.spec.status !== 'planned')
</script>

<template>
  <component
    :is="isReady ? 'RouterLink' : 'div'"
    v-bind="isReady ? { to: `/chart/${spec.id}` } : {}"
    class="sys-row"
    :class="{ 'is-off': !isReady }"
    :aria-disabled="isReady ? undefined : 'true'"
  >
    <span class="eyebrow mt-1.5 w-6 shrink-0 tabular">{{ String(index + 1).padStart(2, '0') }}</span>
    <div class="min-w-0 flex-1">
      <p class="sys-name">
        {{ systemName(spec) }}
        <span v-if="!isReady" class="ml-2 align-middle text-[11px] font-sans font-normal tracking-[0.14em] text-muted">
          {{ t('status.planned') }}
        </span>
      </p>
      <p class="sys-desc mt-2 line-clamp-2 text-[13px] leading-[1.7] text-muted">{{ systemTagline(spec) }}</p>
    </div>
    <svg
      v-if="isReady"
      viewBox="0 0 24 24"
      class="sys-arrow mt-1.5 size-4 shrink-0"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      aria-hidden="true"
    >
      <path d="m9 5 7 7-7 7" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  </component>
</template>
