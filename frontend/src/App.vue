<script setup lang="ts">
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
const route = useRoute()
const router = useRouter()
auth.bootstrap()

// Telegram 标题栏/背景色跟随站内主题切换
watch(() => useSettingsStore().isDark, syncTelegramTheme, { flush: 'post' })

// 换账号就换一套记录：登录后拉自己的，登出清空并离开依赖记录的页面
watch(
  () => auth.user?.id ?? null,
  (id, prev) => {
    if (id === null) {
      charts.reset()
      if (prev !== undefined && ['history', 'result'].includes(String(route.name))) router.replace('/')
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
  <div class="min-h-dvh bg-bg text-ink">
    <DeskNav />
    <AppHeader />
    <main class="wrap pb-28 pt-6 md:pb-10 lg:pt-14">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </main>
    <TabBar />
    <footer v-if="t('footer.note')" class="wrap pb-24 pt-2 text-center text-[11px] leading-[1.6] text-muted md:pb-10">
      {{ t('footer.note') }}
    </footer>
  </div>
</template>
