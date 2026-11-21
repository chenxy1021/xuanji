import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  getMe,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  type AuthCredentials,
  type AuthUser,
} from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  /** 首次 /auth/me 是否已返回（用于避免未就绪时闪「登录」） */
  const ready = ref(false)

  const isAdmin = computed(() => user.value?.is_admin === true)
  const isLoggedIn = computed(() => user.value !== null)

  let booting: Promise<void> | null = null

  async function fetchMe() {
    try {
      const res = await getMe()
      user.value = res?.user ?? null
    } catch {
      // 401 / 网络错误都按未登录处理；不阻塞页面
      user.value = null
    } finally {
      ready.value = true
    }
  }

  /** 启动时只请求一次，重复调用复用同一个 Promise */
  function bootstrap() {
    if (!booting) booting = fetchMe()
    return booting
  }

  async function login(credentials: AuthCredentials) {
    const res = await apiLogin(credentials)
    booting = null
    user.value = res.user
    ready.value = true
    return res.user
  }

  async function register(credentials: AuthCredentials) {
    const res = await apiRegister(credentials)
    booting = null
    user.value = res.user
    ready.value = true
    return res.user
  }

  async function logout() {
    try {
      await apiLogout()
    } finally {
      // 即便请求失败也清本地状态，避免卡在已登录
      booting = null
      user.value = null
      ready.value = true
    }
  }

  return { user, ready, isAdmin, isLoggedIn, fetchMe, bootstrap, login, register, logout }
})
