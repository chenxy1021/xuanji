<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const props = withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })

const auth = useAuthStore()
const router = useRouter()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

const initial = computed(() => (auth.user?.username ?? '').trim().charAt(0).toUpperCase())

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function onDocumentClick(e: MouseEvent) {
  if (open.value && root.value && !root.value.contains(e.target as Node)) close()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})

async function signOut() {
  close()
  await auth.logout()
  if (router.currentRoute.value.name === 'login') router.replace('/')
}
</script>

<template>
  <div ref="root" class="relative flex shrink-0 items-center">
    <template v-if="auth.ready">
      <RouterLink
        v-if="!auth.user"
        :to="{ name: 'login' }"
        class="flex min-h-11 items-center px-1 text-[13px] text-ink-2 transition-colors hover:text-ink"
      >
        {{ t('auth.login') }}
      </RouterLink>

      <button
        v-else
        type="button"
        class="flex min-h-11 items-center gap-2 px-1 text-ink-2 transition-colors hover:text-ink"
        aria-haspopup="menu"
        :aria-expanded="open"
        :aria-label="t('auth.menu')"
        @click.stop="toggle"
      >
        <span
          class="flex size-7 shrink-0 items-center justify-center rounded-full border border-line-strong bg-bg-subtle text-[12px] leading-none text-ink"
          aria-hidden="true"
        >
          {{ initial }}
        </span>
        <span v-if="!props.compact" class="max-w-[7.5rem] truncate text-[13px]">{{ auth.user.username }}</span>
        <svg
          v-if="!props.compact"
          viewBox="0 0 24 24"
          class="size-3.5 shrink-0"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          aria-hidden="true"
        >
          <path d="M6 9.5 12 15.5 18 9.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </template>

    <div
      v-if="open && auth.user"
      class="absolute right-0 top-[calc(100%+6px)] z-40 w-52 overflow-hidden rounded-[var(--radius-md)] border border-line bg-surface py-1 shadow-[var(--shadow-md)]"
      role="menu"
      :aria-label="t('auth.menu')"
    >
      <div class="border-b border-line px-3 pb-2.5 pt-2">
        <div class="flex items-center gap-2">
          <span class="truncate text-[13px] text-ink">{{ auth.user.username }}</span>
          <span v-if="auth.isAdmin" class="chip chip--primary !h-5 !px-1.5 !text-[10px]">{{ t('auth.admin') }}</span>
        </div>
      </div>
      <RouterLink
        :to="{ path: '/settings' }"
        role="menuitem"
        class="flex min-h-11 items-center px-3 text-[13px] text-ink-2 hover:bg-bg-subtle hover:text-ink"
        @click="close"
      >
        {{ t('tab.settings') }}
      </RouterLink>
      <button
        type="button"
        role="menuitem"
        class="flex min-h-11 w-full items-center px-3 text-left text-[13px] text-ink-2 hover:bg-bg-subtle hover:text-ink"
        @click="signOut"
      >
        {{ t('auth.logout') }}
      </button>
    </div>
  </div>
</template>
