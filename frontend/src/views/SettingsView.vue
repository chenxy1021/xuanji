<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import LangSwitch from '@/components/layout/LangSwitch.vue'
import { ApiError, getLlmSettings, getMeta, saveLlmSettings, type LlmSettings } from '@/api/client'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const charts = useChartsStore()
const auth = useAuthStore()

/** 非管理员只能看到 AI 是否可用（公开 /meta），不看也不改配置 */
const llmPublic = ref(false)

const PROVIDERS = [
  { id: 'deepseek', label: 'DeepSeek', base: 'https://api.deepseek.com', model: 'deepseek-chat' },
  { id: 'openai', label: 'OpenAI', base: 'https://api.openai.com/v1', model: 'gpt-4.1-mini' },
  { id: 'custom', label: '自定义', base: '', model: '' },
] as const

const llm = ref<LlmSettings | null>(null)
const baseUrl = ref('')
const model = ref('')
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')

const provider = computed(() => {
  const url = baseUrl.value.trim().replace(/\/+$/, '')
  if (url === 'https://api.deepseek.com') return 'deepseek'
  if (url === 'https://api.openai.com/v1') return 'openai'
  return 'custom'
})

const configured = computed(() => !!llm.value?.configured)
const sourceLabel = computed(() => {
  const source = llm.value?.source ?? 'default'
  return t(source === 'runtime' ? 'settings.aiSourceRuntime' : source === 'env' ? 'settings.aiSourceEnv' : 'settings.aiSourceDefault')
})

function apply(info: LlmSettings) {
  llm.value = info
  baseUrl.value = info.base_url
  model.value = info.model
}

function pickProvider(id: (typeof PROVIDERS)[number]['id']) {
  const p = PROVIDERS.find((x) => x.id === id)
  if (!p || id === 'custom') return
  baseUrl.value = p.base
  model.value = p.model
}

async function load() {
  try {
    apply(await getLlmSettings())
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : t('err.generic')
  }
}

async function save() {
  error.value = ''
  message.value = ''
  const url = baseUrl.value.trim().replace(/\/+$/, '')
  if (!/^https?:\/\//.test(url) || /\s/.test(url) || !model.value.trim()) {
    error.value = t('settings.aiInvalid')
    return
  }
  saving.value = true
  try {
    const info = await saveLlmSettings({
      base_url: url,
      model: model.value.trim(),
      ...(apiKey.value.trim() ? { api_key: apiKey.value.trim() } : {}),
    })
    apply(info)
    apiKey.value = ''
    showKey.value = false
    message.value = t('settings.aiSaved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : t('settings.aiSaveFailed')
  } finally {
    saving.value = false
  }
}

async function clearKey() {
  error.value = ''
  message.value = ''
  try {
    // 只清密钥，保留已保存的接口地址与模型
    apply(await saveLlmSettings({ clear_key: true }))
    apiKey.value = ''
    message.value = t('settings.aiCleared')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : t('settings.aiSaveFailed')
  }
}

const canEdit = computed(() => auth.isAdmin)
const configuredReadOnly = computed(() => llmPublic.value)

onMounted(async () => {
  await auth.bootstrap()
  if (auth.isAdmin) {
    await load()
    return
  }
  try {
    llmPublic.value = (await getMeta()).llm_configured
  } catch {
    /* 状态展示失败就不标已配置 */
  }
})

const clearing = ref(false)
async function clearRecords() {
  clearing.value = true
  error.value = ''
  try {
    await charts.clear(auth.isLoggedIn)
  } catch {
    error.value = t('history.deleteFailed')
  } finally {
    clearing.value = false
  }
}
</script>

<template>
  <div>
    <div class="border-b border-line pb-5">
      <p class="eyebrow">{{ t('settings.eyebrow') }}</p>
      <h1 class="title-serif h-h1 mt-3">{{ t('settings.title') }}</h1>
    </div>

    <div class="settings-grid mt-8 grid gap-10 lg:grid-cols-[200px_minmax(0,640px)] lg:gap-16">
      <nav class="hidden self-start lg:sticky lg:top-[calc(var(--header-h)+32px)] lg:block" :aria-label="t('settings.title')">
        <ul class="space-y-3 text-[13px]">
          <li><a href="#set-appearance" class="text-ink-2 hover:text-ink">{{ t('settings.navAppearance') }}</a></li>
          <li><a href="#set-ai" class="text-ink-2 hover:text-ink">{{ t('settings.navAi') }}</a></li>
          <li><a href="#set-data" class="text-ink-2 hover:text-ink">{{ t('settings.navData') }}</a></li>
          <li><a href="#set-about" class="text-ink-2 hover:text-ink">{{ t('settings.navAbout') }}</a></li>
        </ul>
      </nav>

      <div class="min-w-0 space-y-10">
        <section id="set-appearance" class="scroll-mt-28">
          <h2 class="eyebrow mb-1 block border-b border-line pb-3">{{ t('settings.navAppearance') }}</h2>
          <div class="flex min-h-[64px] items-center justify-between gap-3 border-b border-line py-3">
            <div>
              <p class="text-[15px]">{{ t('settings.language') }}</p>
              <p class="text-xs text-muted">{{ t('settings.languageHint') }}</p>
            </div>
            <LangSwitch />
          </div>
          <label class="switch-row border-b border-line py-3">
            <div>
              <p class="text-[15px]">{{ t('settings.dark') }}</p>
              <p class="text-xs text-muted">{{ t('settings.darkHint') }}</p>
            </div>
            <input
              :checked="settings.mode === 'dark'"
              type="checkbox"
              role="switch"
              :aria-label="t('settings.darkAria')"
              class="switch"
              @change="settings.setMode(($event.target as HTMLInputElement).checked ? 'dark' : 'system')"
            />
          </label>
        </section>

        <section id="set-ai" class="scroll-mt-28">
          <div class="mb-3 flex items-center justify-between gap-3 border-b border-line pb-3">
            <h2 class="eyebrow">{{ t('settings.navAi') }}</h2>
            <span
              class="inline-flex items-center gap-1.5 text-[11px]"
              :class="(canEdit ? configured : configuredReadOnly) ? 'text-success' : 'text-muted'"
              data-llm-status
            >
              <span
                class="size-1.5 rounded-full"
                :class="(canEdit ? configured : configuredReadOnly) ? 'bg-success shadow-[0_0_0_3px_var(--color-success-soft)]' : 'bg-muted'"
                aria-hidden="true"
              />
              {{ (canEdit ? configured : configuredReadOnly) ? t('settings.aiStatusOn') : t('settings.aiStatusOff') }}
              <span v-if="canEdit && configured" class="text-muted">· {{ sourceLabel }}</span>
            </span>
          </div>

          <!-- 非管理员 / 未登录：只读说明 -->
          <div v-if="!canEdit" class="settings-card" data-llm-readonly>
            <p class="max-w-[58ch] text-[13px] leading-[1.75] text-muted">{{ t('settings.aiAdminOnly') }}</p>
            <p v-if="!auth.isLoggedIn" class="mt-3 text-[12px] text-muted">
              <RouterLink to="/login?next=/settings" class="link-underline text-primary">{{ t('common.login') }}</RouterLink>
            </p>
          </div>

          <div v-else class="settings-card" data-llm-settings>
            <p class="max-w-[58ch] text-[13px] leading-[1.75] text-muted">{{ t('settings.aiHint') }}</p>

            <div class="mt-5">
              <p class="eyebrow mb-2">{{ t('settings.aiProvider') }}</p>
              <div class="flex flex-wrap gap-1.5" role="group" :aria-label="t('settings.aiProvider')">
                <button
                  v-for="p in PROVIDERS"
                  :key="p.id"
                  type="button"
                  class="provider-pill"
                  :class="{ 'is-on': provider === p.id }"
                  :aria-pressed="provider === p.id"
                  @click="pickProvider(p.id)"
                >
                  {{ p.id === 'custom' ? t('settings.aiCustom') : p.label }}
                </button>
              </div>
            </div>

            <label class="settings-field mt-5">
              <span class="settings-field__label">{{ t('settings.aiBaseUrl') }}</span>
              <input
                v-model="baseUrl"
                type="url"
                class="field"
                spellcheck="false"
                autocomplete="off"
                placeholder="https://api.deepseek.com"
              />
              <small class="settings-field__hint">{{ t('settings.aiBaseUrlHint') }}</small>
            </label>

            <label class="settings-field mt-4">
              <span class="settings-field__label">{{ t('settings.aiModel') }}</span>
              <input
                v-model="model"
                type="text"
                class="field"
                spellcheck="false"
                autocomplete="off"
                placeholder="deepseek-chat"
              />
              <small class="settings-field__hint">{{ t('settings.aiModelHint') }}</small>
            </label>

            <label class="settings-field mt-4">
              <span class="settings-field__label">
                {{ t('settings.aiKey') }}
                <span v-if="llm?.key_hint" class="tabular ml-1 font-normal text-muted">{{ llm.key_hint }}</span>
              </span>
              <span class="relative block">
                <input
                  v-model="apiKey"
                  :type="showKey ? 'text' : 'password'"
                  class="field !pr-16"
                  spellcheck="false"
                  autocomplete="new-password"
                  :placeholder="t('settings.aiKeyPlaceholder')"
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 px-3 text-[11px] text-muted hover:text-ink"
                  :aria-label="showKey ? t('settings.aiHideKey') : t('settings.aiShowKey')"
                  @click="showKey = !showKey"
                >
                  {{ showKey ? t('settings.aiHideKey') : t('settings.aiShowKey') }}
                </button>
              </span>
              <small v-if="configured" class="settings-field__hint">{{ t('settings.aiKeyKeep', { hint: llm?.key_hint ?? '' }) }}</small>
            </label>

            <div class="mt-5 flex flex-wrap items-center gap-2">
              <button type="button" class="btn-primary !w-auto !px-5" :disabled="saving" @click="save">
                {{ saving ? t('settings.aiSaving') : t('settings.aiSave') }}
              </button>
              <button type="button" class="btn-line" :disabled="!configured || saving" @click="clearKey">
                {{ t('settings.aiClear') }}
              </button>
              <span class="ml-auto text-[11px] text-muted">{{ sourceLabel }}</span>
            </div>

            <p v-if="message" class="mt-3 text-[12px] text-success" role="status" aria-live="polite">{{ message }}</p>
            <p v-if="error" class="mt-3 text-[12px] text-danger" role="alert">{{ error }}</p>

            <p class="mt-4 border-t border-line pt-3 text-[11px] leading-[1.7] text-muted">{{ t('settings.aiLocalNote') }}</p>
          </div>
        </section>

        <section id="set-data" class="scroll-mt-28">
          <h2 class="eyebrow mb-1 block border-b border-line pb-3">{{ t('settings.navData') }}</h2>
          <div class="flex min-h-[64px] items-center justify-between gap-3 border-b border-line py-3">
            <div>
              <p class="text-[15px]">{{ t('settings.records') }}</p>
              <p class="text-xs text-muted">{{ auth.isLoggedIn ? t('settings.recordsCountOnline', { n: charts.history.length }) : t('settings.recordsGuest') }}</p>
            </div>
            <button
              type="button"
              class="btn-line"
              :disabled="!auth.isLoggedIn || !charts.history.length || clearing"
              @click="clearRecords"
            >
              {{ t('settings.clear') }}
            </button>
          </div>
        </section>

        <section id="set-about" class="scroll-mt-28">
          <h2 class="eyebrow mb-1 block border-b border-line pb-3">{{ t('settings.navAbout') }}</h2>
          <div class="space-y-2 pt-4 text-[13px] leading-[1.85] text-muted">
            <p>{{ t('settings.about1') }}</p>
            <p>{{ t('settings.about2a') }} <code class="rounded-[var(--radius-xs)] bg-bg-subtle px-1 text-ink-2">SM_LLM_API_KEY</code>{{ t('settings.about2b') }}</p>
            <p>{{ t('settings.about3') }}</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
