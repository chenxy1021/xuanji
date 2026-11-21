import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { setLocaleFrom } from './i18n'
import { loadJSON } from './lib/storage'
import router from './router'
import './styles.css'

// 先设 lang，避免首屏闪烁
setLocaleFrom(loadJSON<string | null>('sm_locale', null))

createApp(App).use(createPinia()).use(router).mount('#app')
