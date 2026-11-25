<script setup lang="ts">
import { computed } from 'vue'
import type { SystemSpec } from '@/api/types'
import { t } from '@/i18n'
import { systemName, systemTagline } from '@/i18n/terms'

const props = defineProps<{ spec: SystemSpec }>()

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
    <div class="min-w-0 flex-1">
      <p class="sys-name">{{ systemName(spec) }}</p>
      <p class="sys-desc line-clamp-2">{{ systemTagline(spec) }}</p>
      <p v-if="!isReady" class="mt-2 text-xs text-muted">{{ t('status.planned') }}</p>
    </div>
    <svg
      viewBox="0 0 24 24"
      class="sys-arrow size-4 shrink-0"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="m9 5 7 7-7 7" />
    </svg>
  </component>
</template>
