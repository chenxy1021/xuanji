<script setup lang="ts">
import { watch } from 'vue'
import DeskNav from '@/components/layout/DeskNav.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import TabBar from '@/components/layout/TabBar.vue'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { useSettingsStore } from '@/stores/settings'
import { syncTelegramTheme } from '@/lib/telegram'

// 启动时拉一次登录态；失败按未登录处理
const auth = useAuthStore()
const charts = useChartsStore()
auth.bootstrap()

// Telegram 标题栏/背景色跟随站内主题切换；immediate 补首次挂载时的同步
watch(() => useSettingsStore().isDark, syncTelegramTheme, { flush: 'post', immediate: true })

// 换账号就换一套记录：登录后拉自己的，未登录只读本浏览器缓存。
// 等 /auth/me 返回后再决定读哪一边，避免已登录用户先闪一眼游客记录。
watch(
  () => [auth.ready, auth.user?.id ?? null] as const,
  ([ready, id]) => {
    if (!ready) return
    if (id === null) {
      charts.reset()
      charts.loadLocal()
      return
    }
    charts.loadFromServer().catch(() => {
      /* 列表失败由各页面自己的错误态呈现 */
    })
  },
  { immediate: true },
)
</script>

<template>
  <div class="app-shell min-h-dvh text-ink">
    <DeskNav />
    <AppHeader />
    <main class="wrap app-main pb-28 pt-6 md:pb-10 lg:pt-14">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </main>
    <TabBar />
    <footer v-if="t('footer.note')" class="app-footer">
      <div class="wrap">
        <p class="border-t border-line pt-4 text-xs leading-[1.7] text-muted">{{ t('footer.note') }}</p>
      </div>
    </footer>
  </div>
</template>
