<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

type Mode = 'login' | 'register'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const mode = ref<Mode>(route.query.mode === 'register' ? 'register' : 'login')
const username = ref('')
const password = ref('')
const confirm = ref('')
const busy = ref(false)
const serverError = ref('')
const fieldErrors = reactive({ username: '', password: '', confirm: '' })

const nextPath = computed(() => {
  const n = route.query.next
  const path = typeof n === 'string' && n.startsWith('/') && !n.startsWith('//') ? n : '/'
  return path === '/login' ? '/' : path
})

const title = computed(() => (mode.value === 'login' ? t('auth.titleLogin') : t('auth.titleRegister')))
const intro = computed(() => (mode.value === 'login' ? t('auth.introLogin') : t('auth.introRegister')))
const submitLabel = computed(() =>
  busy.value
    ? t(mode.value === 'login' ? 'auth.pendingLogin' : 'auth.pendingRegister')
    : t(mode.value === 'login' ? 'auth.submitLogin' : 'auth.submitRegister'),
)

let leaving = false
function goNext() {
  if (leaving) return
  leaving = true
  router.replace(nextPath.value)
}

// 已登录访问 /login 直接跳走（含启动时 /auth/me 晚到的情况）
watch(
  [() => auth.ready, () => auth.user],
  ([ready, user]) => {
    if (ready && user) goNext()
  },
  { immediate: true },
)

function setMode(next: Mode) {
  if (mode.value === next) return
  mode.value = next
  password.value = ''
  confirm.value = ''
  serverError.value = ''
  fieldErrors.username = ''
  fieldErrors.password = ''
  fieldErrors.confirm = ''
}

function validate() {
  fieldErrors.username = ''
  fieldErrors.password = ''
  fieldErrors.confirm = ''

  const name = username.value.trim()
  if (name.length < 3 || name.length > 32 || /\s/.test(name)) {
    fieldErrors.username = t('auth.errUsername')
  }
  if (password.value.length < 8) {
    fieldErrors.password = t('auth.errPassword')
  }
  if (mode.value === 'register' && confirm.value !== password.value) {
    fieldErrors.confirm = t('auth.errConfirm')
  }
  return !fieldErrors.username && !fieldErrors.password && !fieldErrors.confirm
}

function messageFor(e: unknown) {
  if (e instanceof ApiError) {
    if (e.status === 401) return t('auth.errCredential')
    if (e.status === 409) return t('auth.errTaken')
    if (e.status === 429) return t('auth.errTooMany')
    // 404/5xx/网络错误多为部署或服务异常，给统一可读文案
    if (!e.status || e.status === 404 || e.status >= 500) return t('auth.errUnknown')
    return e.message || t('auth.errUnknown')
  }
  return t('auth.errUnknown')
}

async function submit() {
  if (busy.value) return
  serverError.value = ''
  if (!validate()) return

  busy.value = true
  try {
    const credentials = { username: username.value.trim(), password: password.value }
    if (mode.value === 'login') await auth.login(credentials)
    else await auth.register(credentials)
    goNext()
  } catch (e) {
    serverError.value = messageFor(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="mx-auto w-full max-w-[440px] py-2 lg:py-8">
    <h1 class="title-serif text-[28px] leading-tight lg:text-[32px]">{{ title }}</h1>
    <p class="mt-2 text-[13px] leading-[1.7] text-muted">{{ intro }}</p>

    <div class="seg seg-equal seg-wide mt-7" role="group" :aria-label="t('auth.tabs')">
      <button
        v-for="m in [{ id: 'login', label: t('auth.login') }, { id: 'register', label: t('auth.register') }] as const"
        :key="m.id"
        type="button"
        :class="{ 'is-on': mode === m.id }"
        :aria-pressed="mode === m.id"
        @click="setMode(m.id)"
      >
        {{ m.label }}
      </button>
    </div>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <div>
        <label for="auth-username" class="form-label">{{ t('auth.username') }}</label>
        <input
          id="auth-username"
          v-model="username"
          class="field"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          :aria-invalid="!!fieldErrors.username"
          :aria-describedby="fieldErrors.username ? 'auth-username-err' : undefined"
          @input="fieldErrors.username = ''"
        />
        <p v-if="fieldErrors.username" id="auth-username-err" class="mt-1.5 text-xs text-danger">
          {{ fieldErrors.username }}
        </p>
      </div>

      <div>
        <label for="auth-password" class="form-label">{{ t('auth.password') }}</label>
        <input
          id="auth-password"
          v-model="password"
          class="field"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          :aria-invalid="!!fieldErrors.password"
          :aria-describedby="fieldErrors.password ? 'auth-password-err' : undefined"
          @input="fieldErrors.password = ''"
        />
        <p v-if="fieldErrors.password" id="auth-password-err" class="mt-1.5 text-xs text-danger">
          {{ fieldErrors.password }}
        </p>
      </div>

      <div v-if="mode === 'register'">
        <label for="auth-confirm" class="form-label">{{ t('auth.confirm') }}</label>
        <input
          id="auth-confirm"
          v-model="confirm"
          class="field"
          type="password"
          autocomplete="new-password"
          :aria-invalid="!!fieldErrors.confirm"
          :aria-describedby="fieldErrors.confirm ? 'auth-confirm-err' : undefined"
          @input="fieldErrors.confirm = ''"
        />
        <p v-if="fieldErrors.confirm" id="auth-confirm-err" class="mt-1.5 text-xs text-danger">
          {{ fieldErrors.confirm }}
        </p>
      </div>

      <p
        v-if="serverError"
        role="alert"
        class="border-l-2 border-danger pl-3 text-[12.5px] leading-[1.6] text-danger"
      >
        {{ serverError }}
      </p>

      <button type="submit" class="btn-primary w-full" :disabled="busy" :aria-busy="busy">
        <svg
          v-if="busy"
          viewBox="0 0 24 24"
          class="size-4 animate-spin"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          aria-hidden="true"
        >
          <path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" />
        </svg>
        {{ submitLabel }}
      </button>
    </form>

    <p class="mt-5 border-t border-line pt-4 text-[13px] text-muted">
      {{ t(mode === 'login' ? 'auth.noAccount' : 'auth.haveAccount') }}
      <button
        type="button"
        class="let-action text-[13px]"
        @click="setMode(mode === 'login' ? 'register' : 'login')"
      >
        {{ t(mode === 'login' ? 'auth.toRegister' : 'auth.toLogin') }}
      </button>
    </p>
  </div>
</template>
