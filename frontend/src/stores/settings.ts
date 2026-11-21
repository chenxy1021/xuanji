import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { loadJSON, saveJSON } from '@/lib/storage'
import { setLocaleFrom, useLocale, type Locale } from '@/i18n'

export type ThemeMode = 'system' | 'light' | 'dark'

const systemDark = () => matchMedia('(prefers-color-scheme: dark)').matches

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadJSON<{ mode?: ThemeMode; theme?: 'light' | 'dark' } | null>('sm_theme', null)
  const mode = ref<ThemeMode>(saved?.mode ?? saved?.theme ?? 'dark')

  // 主题统一写 data-theme，与 tokens.css 对齐
  const apply = () => {
    // v2 深色为默认：只有显式选了 light，或 system 且系统为浅色，才走浅色
    const dark = mode.value === 'dark' || (mode.value === 'system' && systemDark())
    if (dark) delete document.documentElement.dataset.theme
    else document.documentElement.dataset.theme = 'light'
  }
  apply()

  const media = matchMedia('(prefers-color-scheme: dark)')
  media.addEventListener('change', () => {
    if (mode.value === 'system') apply()
  })

  watch(mode, () => {
    apply()
    saveJSON('sm_theme', { mode: mode.value })
  })

  const isDark = computed(
    () => mode.value === 'dark' || (mode.value === 'system' && media.matches),
  )
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
