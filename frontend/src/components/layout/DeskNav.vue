<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import LangSwitch from '@/components/layout/LangSwitch.vue'
import UserMenu from '@/components/layout/UserMenu.vue'
import { t, type MsgKey } from '@/i18n'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const settings = useSettingsStore()

const items: { to: string; key: MsgKey; match: () => boolean }[] = [
  { to: '/', key: 'tab.home', match: () => route.path === '/' },
  { to: '/chart/bazi', key: 'tab.chart', match: () => route.path.startsWith('/chart') || route.path === '/result' },
  { to: '/history', key: 'tab.history', match: () => route.path === '/history' },
  { to: '/settings', key: 'tab.settings', match: () => route.path === '/settings' },
]
const active = computed(() => items.find((i) => i.match())?.to)
</script>

<template>
  <header class="desk-nav">
    <div class="wrap flex h-full items-center justify-between gap-8">
      <RouterLink to="/" class="flex shrink-0 items-baseline gap-2.5">
        <span class="title-serif text-[22px] leading-none tracking-[0.22em]">{{ t('brand.name') }}</span>
        <span class="eyebrow leading-none">XUANJI</span>
      </RouterLink>
      <nav class="flex h-full items-center gap-9" :aria-label="t('nav.aria')">
        <RouterLink
          v-for="i in items"
          :key="i.to"
          :to="i.to"
          class="nav-item"
          :class="{ 'is-on': active === i.to }"
          :aria-current="active === i.to ? 'page' : undefined"
        >
          {{ t(i.key) }}
        </RouterLink>
      </nav>
      <div class="flex shrink-0 items-center gap-3">
        <LangSwitch />
        <button
          type="button"
          class="flex size-10 items-center justify-center text-ink-2 transition-colors hover:text-ink"
          :aria-label="settings.isDark ? t('header.themeLight') : t('header.themeDark')"
          @click="settings.toggleTheme()"
        >
          <svg v-if="settings.isDark" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.6">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19" stroke-linecap="round" />
          </svg>
          <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" stroke-linejoin="round" />
          </svg>
        </button>
        <UserMenu />
      </div>
    </div>
  </header>
</template>
