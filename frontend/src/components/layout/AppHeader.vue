<script setup lang="ts">
import LangSwitch from '@/components/layout/LangSwitch.vue'
import UserMenu from '@/components/layout/UserMenu.vue'
import { t } from '@/i18n'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
</script>

<template>
  <header class="app-header sticky top-0 z-30 border-b border-line bg-bg">
    <div class="wrap flex h-[var(--header-h)] items-center justify-between">
      <RouterLink to="/" class="flex min-w-0 min-h-11 items-center gap-3">
        <span class="flex size-[26px] items-center justify-center text-ink" aria-hidden="true">
          <svg viewBox="0 0 24 24" class="size-full" fill="none" stroke="currentColor" stroke-width="1.4">
            <circle cx="12" cy="12" r="8.5" />
            <path d="M12 3.5a8.5 8.5 0 0 0 0 17M12 7a5 5 0 0 1 0 10" stroke-linecap="round" />
          </svg>
        </span>
        <span class="flex min-w-0 flex-col">
          <span class="title-serif text-[22px] leading-tight tracking-[0.18em]">{{ t('brand.name') }}</span>
          <span class="app-brand-sub max-w-[13rem] truncate text-xs leading-tight text-muted">{{ t('brand.subtitle') }}</span>
        </span>
      </RouterLink>
      <div class="flex shrink-0 items-center gap-1">
        <LangSwitch />
        <button
          type="button"
          class="flex size-11 items-center justify-center rounded-[var(--radius-md)] text-ink-2 hover:bg-bg-subtle active:bg-bg-subtle"
          :aria-label="settings.isDark ? t('header.themeLight') : t('header.themeDark')"
          @click="settings.toggleTheme()"
        >
        <svg v-if="settings.isDark" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19" stroke-linecap="round" />
        </svg>
        <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" stroke-linejoin="round" />
        </svg>
        </button>
        <UserMenu compact />
      </div>
    </div>
  </header>
</template>
