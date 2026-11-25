<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { t, type MsgKey } from '@/i18n'

const route = useRoute()

const tabs: { to: string; key: MsgKey; match: () => boolean; path: string }[] = [
  {
    to: '/',
    key: 'tab.home',
    match: () => route.path === '/',
    path: 'M3.5 10.5 12 3.5l8.5 7V20a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1z',
  },
  {
    to: '/history',
    key: 'tab.history',
    match: () => route.path === '/history',
    path: 'M12 7v5l3 2M4.5 12a7.5 7.5 0 1 0 2.2-5.3M4.5 4.5v3.2h3.2',
  },
  {
    to: '/settings',
    key: 'tab.settings',
    match: () => route.path === '/settings',
    path: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm7.4-3a7.4 7.4 0 0 0-.1-1.2l2-1.5-2-3.4-2.3 1a7.5 7.5 0 0 0-2-1.2L14.6 3h-4l-.4 2.5a7.5 7.5 0 0 0-2 1.2l-2.3-1-2 3.4 2 1.5a7.4 7.4 0 0 0 0 2.4l-2 1.5 2 3.4 2.3-1a7.5 7.5 0 0 0 2 1.2l.4 2.5h4l.4-2.5a7.5 7.5 0 0 0 2-1.2l2.3 1 2-3.4-2-1.5c.06-.4.1-.8.1-1.2Z',
  },
]

const active = computed(() => tabs.findIndex((t) => t.match()))
</script>

<template>
  <nav class="app-tabbar fixed inset-x-0 bottom-0 z-30 border-t border-line bg-bg">
    <div class="mx-auto flex h-[var(--tabbar-h)] w-full max-w-[var(--container-max)] items-center justify-around px-2">
      <RouterLink
        v-for="(tab, i) in tabs"
        :key="tab.to"
        :to="tab.to"
        class="flex min-h-11 min-w-16 flex-col items-center justify-center gap-0.5 text-[13px] leading-tight"
        :class="i === active ? 'tab-on' : 'text-muted'"
        :aria-current="i === active ? 'page' : undefined"
      >
        <svg viewBox="0 0 24 24" class="size-6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">
          <path :d="tab.path" />
        </svg>
        {{ t(tab.key) }}
      </RouterLink>
    </div>
  </nav>
</template>
