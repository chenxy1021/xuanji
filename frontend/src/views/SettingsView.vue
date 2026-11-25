<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import LangSwitch from '@/components/layout/LangSwitch.vue'
import {
  ApiError,
  getLlmSettings,
  getMeta,
  resetLlmSettings,
  saveLlmSettings,
  type LlmSettings,
  type MetaInfo,
} from '@/api/client'
import { t } from '@/i18n'
import { clearLocalLlm, loadLocalLlm, saveLocalLlm, type LocalLlmConfig } from '@/lib/llmConfig'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const charts = useChartsStore()
const auth = useAuthStore()

const PROVIDERS = [
  { id: 'deepseek', label: 'DeepSeek', base: 'https://api.deepseek.com', model: 'deepseek-chat' },
  { id: 'openai', label: 'OpenAI', base: 'https://api.openai.com/v1', model: 'gpt-4.1-mini' },
  { id: 'custom', label: '自定义', base: '', model: '' },
] as const

/** 用户自己的配置：只存当前浏览器，未登录也能用 */
const personal = ref<LocalLlmConfig | null>(null)
/** 本站默认：管理员可改，其他用户只经 /meta 看是否可用 */
const defaultInfo = ref<LlmSettings | null>(null)
const server = ref<LlmSettings | null>(null)
const baseUrl = ref('')
const model = ref('')
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const savingDefault = ref(false)
const message = ref('')
const error = ref('')

const provider = computed(() => {
  const url = baseUrl.value.trim().replace(/\/+$/, '')
  if (url === 'https://api.deepseek.com') return 'deepseek'
  if (url === 'https://api.openai.com/v1') return 'openai'
  return 'custom'
})

const configured = computed(() => !!personal.value || !!defaultInfo.value?.configured)
const sourceLabel = computed(() => {
  if (personal.value) return t('settings.aiSourceLocal')
  const source = defaultInfo.value?.source ?? 'default'
  return t(
    source === 'runtime'
      ? 'settings.aiSourceRuntime'
      : source === 'env'
        ? 'settings.aiSourceEnv'
        : 'settings.aiSourceDefault',
  )
})
const personalKeyHint = computed(() => {
  const key = personal.value?.api_key ?? ''
  if (!key) return ''
  return key.length >= 12 ? `••••${key.slice(-4)}` : '••••'
})

function pickProvider(id: (typeof PROVIDERS)[number]['id']) {
  const p = PROVIDERS.find((x) => x.id === id)
  if (!p || id === 'custom') return
  baseUrl.value = p.base
  model.value = p.model
}

function applyMeta(info: MetaInfo) {
  defaultInfo.value = {
    configured: info.llm_configured,
    base_url: info.llm_base_url,
    model: info.llm_model,
    source: info.llm_source,
    key_hint: info.llm_key_hint,
  }
}

function fillForm(info: { base_url: string; model: string } | null) {
  baseUrl.value = info?.base_url ?? ''
  model.value = info?.model ?? ''
}

async function load() {
  await auth.bootstrap()
  personal.value = loadLocalLlm()
  if (auth.isAdmin) {
    try {
      server.value = await getLlmSettings()
      defaultInfo.value = server.value
    } catch (e) {
      error.value = e instanceof ApiError ? e.message : t('err.generic')
    }
  } else {
    try {
      applyMeta(await getMeta())
    } catch {
      /* 状态展示失败就不标已配置 */
    }
  }
  fillForm(personal.value ?? defaultInfo.value)
  if (personal.value) apiKey.value = personal.value.api_key
}

function readForm(): { url: string; model: string; key: string } | null {
  const url = baseUrl.value.trim().replace(/\/+$/, '')
  const name = model.value.trim()
  if (!/^https?:\/\//.test(url) || /\s/.test(url) || !name) {
    error.value = t('settings.aiInvalid')
    return null
  }
  return { url, model: name, key: apiKey.value.trim() }
}

async function save() {
  error.value = ''
  message.value = ''
  const form = readForm()
  if (!form) return
  const key = form.key || personal.value?.api_key || ''
  if (!key) {
    error.value = t('settings.aiKeyRequired')
    return
  }
  saving.value = true
  try {
    const cfg = saveLocalLlm({ base_url: form.url, model: form.model, api_key: key })
    if (!cfg) {
      error.value = t('settings.aiInvalid')
      return
    }
    personal.value = cfg
    apiKey.value = cfg.api_key
    showKey.value = false
    message.value = t('settings.aiSavedLocal')
  } finally {
    saving.value = false
  }
}

function clearPersonal() {
  error.value = ''
  clearLocalLlm()
  personal.value = null
  apiKey.value = ''
  showKey.value = false
  fillForm(defaultInfo.value)
  message.value = t('settings.aiClearedLocal')
}

async function saveAsDefault() {
  error.value = ''
  message.value = ''
  const form = readForm()
  if (!form) return
  if (!form.key && !server.value?.configured) {
    error.value = t('settings.aiKeyRequired')
    return
  }
  savingDefault.value = true
  try {
    const info = await saveLlmSettings({
      base_url: form.url,
      model: form.model,
      ...(form.key ? { api_key: form.key } : {}),
    })
    server.value = info
    defaultInfo.value = info
    message.value = t('settings.aiDefaultSaved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : t('settings.aiSaveFailed')
  } finally {
    savingDefault.value = false
  }
}

async function clearDefault() {
  error.value = ''
  message.value = ''
  try {
    const info = await resetLlmSettings()
    server.value = info
    defaultInfo.value = info
    message.value = t('settings.aiDefaultCleared')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : t('settings.aiSaveFailed')
  }
}

onMounted(load)

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
      <h1 class="title-serif h-h1">{{ t('settings.title') }}</h1>
    </div>

    <div class="settings-grid mt-8">
      <nav class="settings-nav" :aria-label="t('settings.title')">
        <ul class="space-y-3 text-[13px]">
          <li><a href="#set-appearance" class="text-ink-2 hover:text-ink">{{ t('settings.navAppearance') }}</a></li>
          <li><a href="#set-ai" class="text-ink-2 hover:text-ink">{{ t('settings.navAi') }}</a></li>
          <li><a href="#set-data" class="text-ink-2 hover:text-ink">{{ t('settings.navData') }}</a></li>
          <li><a href="#set-about" class="text-ink-2 hover:text-ink">{{ t('settings.navAbout') }}</a></li>
        </ul>
      </nav>

      <div class="settings-body">
        <section id="set-appearance" class="scroll-mt-28">
          <h2 class="label mb-1 block border-b border-line pb-3">{{ t('settings.navAppearance') }}</h2>
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
              :checked="settings.isDark"
              type="checkbox"
              role="switch"
              :aria-label="t('settings.darkAria')"
              class="switch"
              @change="settings.setMode(($event.target as HTMLInputElement).checked ? 'dark' : 'light')"
            />
          </label>
        </section>

        <section id="set-ai" class="scroll-mt-28">
          <div class="mb-3 flex items-center justify-between gap-3 border-b border-line pb-3">
            <h2 class="label">{{ t('settings.navAi') }}</h2>
            <span
              class="inline-flex items-center gap-1.5 text-[13px]"
              :class="configured ? 'text-success' : 'text-muted'"
              data-llm-status
            >
              {{ configured ? t('settings.aiStatusOn') : t('settings.aiStatusOff') }}
              <span v-if="configured" class="text-muted">/ {{ sourceLabel }}</span>
            </span>
          </div>

          <div class="pt-4" data-llm-settings>
            <p class="max-w-[58ch] text-[13px] leading-[1.75] text-muted">{{ t('settings.aiHint') }}</p>
            <p v-if="personal" class="mt-2 text-[12px] text-success" data-llm-personal>
              {{ t('settings.aiPersonalOn', { hint: personalKeyHint }) }}
            </p>

            <div class="mt-5">
              <p class="label mb-2">{{ t('settings.aiProvider') }}</p>
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
              <span class="settings-field__label">{{ t('settings.aiKey') }}</span>
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
                  class="absolute inset-y-0 right-0 px-3 text-[13px] text-muted hover:text-ink"
                  :aria-label="showKey ? t('settings.aiHideKey') : t('settings.aiShowKey')"
                  @click="showKey = !showKey"
                >
                  {{ showKey ? t('settings.aiHideKey') : t('settings.aiShowKey') }}
                </button>
              </span>
              <small v-if="personal" class="settings-field__hint">{{ t('settings.aiKeyKeepLocal', { hint: personalKeyHint }) }}</small>
              <small v-else class="settings-field__hint">{{ t('settings.aiKeyRequiredHint') }}</small>
            </label>

            <div class="mt-5 flex flex-wrap items-center gap-2">
              <button type="button" class="btn-primary" :disabled="saving" @click="save">
                {{ saving ? t('settings.aiSaving') : t('settings.aiSave') }}
              </button>
              <button v-if="personal" type="button" class="btn-line" :disabled="saving" @click="clearPersonal">
                {{ t('settings.aiClearPersonal') }}
              </button>
              <span class="ml-auto text-[13px] text-muted">{{ sourceLabel }}</span>
            </div>

            <p v-if="message" class="mt-3 text-[12px] text-success" role="status" aria-live="polite">{{ message }}</p>
            <p v-if="error" class="mt-3 text-[12px] text-danger" role="alert">{{ error }}</p>

            <p class="mt-4 text-[13px] leading-[1.7] text-muted">{{ t('settings.aiLocalNote') }}</p>

            <!-- 管理员：本站默认，供没有个人配置的访问者使用 -->
            <div v-if="auth.isAdmin" class="mt-6 border-t border-line pt-4" data-llm-default>
              <p class="label mb-2">{{ t('settings.aiServerTitle') }}</p>
              <p class="max-w-[58ch] text-[12px] leading-[1.7] text-muted">{{ t('settings.aiServerHint') }}</p>
              <p class="mt-2 text-[12px]" :class="server?.configured ? 'text-success' : 'text-muted'">
                {{ server?.configured ? t('settings.aiStatusOn') : t('settings.aiStatusOff') }}
                <span v-if="server?.key_hint" class="tabular ml-2 text-muted">{{ server.key_hint }}</span>
              </p>
              <div class="mt-3 flex flex-wrap gap-2">
                <button type="button" class="btn-line" :disabled="savingDefault" @click="saveAsDefault">
                  {{ t('settings.aiSaveDefault') }}
                </button>
                <button
                  type="button"
                  class="btn-line"
                  :disabled="!server?.configured || savingDefault"
                  @click="clearDefault"
                >
                  {{ t('settings.aiClearDefault') }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section id="set-data" class="scroll-mt-28">
          <h2 class="label mb-1 block border-b border-line pb-3">{{ t('settings.navData') }}</h2>
          <div class="flex min-h-[64px] items-center justify-between gap-3 border-b border-line py-3">
            <div>
              <p class="text-[15px]">{{ t('settings.records') }}</p>
              <p class="text-xs text-muted">{{ auth.isLoggedIn ? t('settings.recordsCountOnline', { n: charts.history.length }) : t('settings.recordsCountGuest', { n: charts.history.length }) }}</p>
            </div>
            <button
              type="button"
              class="btn-line"
              :disabled="!charts.history.length || clearing"
              @click="clearRecords"
            >
              {{ t('settings.clear') }}
            </button>
          </div>
        </section>

        <section id="set-about" class="scroll-mt-28">
          <h2 class="label mb-1 block border-b border-line pb-3">{{ t('settings.navAbout') }}</h2>
          <div class="space-y-2 pt-4 text-[13px] leading-[1.85] text-muted">
            <p>{{ t('settings.about1') }}</p>
            <p>{{ t('settings.about2a') }} <code class="border border-line px-1 text-ink-2">SM_LLM_API_KEY</code>{{ t('settings.about2b') }}</p>
            <p>{{ t('settings.about3') }}</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
