<script setup lang="ts">
import { useLocale, t } from '@/i18n'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const locale = useLocale()
</script>

<template>
  <div class="seg" role="group" :aria-label="t('header.lang')">
    <button
      v-for="l in [{ id: 'zh', label: '中' }, { id: 'en', label: 'EN' }] as const"
      :key="l.id"
      type="button"
      class="min-w-[44px] px-2 !text-[13px]"
      :class="{ 'is-on': locale === l.id }"
      :aria-pressed="locale === l.id"
      :lang="l.id === 'en' ? 'en' : 'zh-CN'"
      @click="settings.setLocale(l.id)"
    >
      {{ l.label }}
    </button>
  </div>
</template>
