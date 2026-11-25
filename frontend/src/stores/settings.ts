import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { loadJSON, saveJSON } from '@/lib/storage'
import { telegramColorScheme } from '@/lib/telegram'
import { setLocaleFrom, useLocale, type Locale } from '@/i18n'

export type ThemeMode = 'system' | 'light' | 'dark'

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadJSON<{ mode?: ThemeMode; theme?: 'light' | 'dark' } | null>('sm_theme', null)
  const mode = ref<ThemeMode>(saved?.mode ?? saved?.theme ?? 'system')
  const media = matchMedia('(prefers-color-scheme: dark)')
  const systemIsDark = ref(media.matches)
  const tgScheme = ref(telegramColorScheme())
  const isDark = computed(
    () =>
      mode.value === 'dark' ||
      (mode.value === 'system' && (tgScheme.value ? tgScheme.value === 'dark' : systemIsDark.value)),
  )

  // 浅色是默认；深色只通过 data-theme="dark" 覆盖，和 tokens-v2.css 对齐
  const apply = () => {
    if (isDark.value) document.documentElement.dataset.theme = 'dark'
    else delete document.documentElement.dataset.theme
  }
  apply()

  media.addEventListener('change', (e) => {
    systemIsDark.value = e.matches
    if (mode.value === 'system') apply()
  })
  window.addEventListener('tg-theme-changed', () => {
    tgScheme.value = telegramColorScheme()
    if (mode.value === 'system') apply()
  })

  watch(mode, () => {
    apply()
    saveJSON('sm_theme', { mode: mode.value })
  })

  const toggleTheme = () => (mode.value = isDark.value ? 'light' : 'dark')
  const setMode = (m: ThemeMode) => (mode.value = m)

  // 语言以 i18n 模块为唯一状态源，store 只负责持久化
  setLocaleFrom(loadJSON<Locale | null>('sm_locale', null))
  const locale = useLocale()
  watch(
    () => locale.value,
    (l) => saveJSON('sm_locale', l),
  )
  const setLocale = (l: Locale) => setLocaleFrom(l)
  const toggleLocale = () => setLocaleFrom(locale.value === 'zh' ? 'en' : 'zh')

  return { mode, isDark, toggleTheme, setMode, locale, setLocale, toggleLocale }
})
