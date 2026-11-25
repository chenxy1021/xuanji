import { loadJSON, removeJSON, saveJSON } from './storage'

/**
 * 用户自己的模型配置，只存在当前浏览器（localStorage），不写服务端。
 * 有它时 /interpret 会带上这份配置，优先于本站默认。
 */
export interface LocalLlmConfig {
  base_url: string
  model: string
  api_key: string
}

const KEY = 'sm_llm_personal'

export function isValidBaseUrl(value: string): boolean {
  return (
    value.length > 0 &&
    value.length <= 300 &&
    /^https?:\/\//.test(value) &&
    !/\s/.test(value)
  )
}

export function isValidModel(value: string): boolean {
  return value.length > 0 && value.length <= 120 && !/\s/.test(value)
}

export function isValidApiKey(value: string): boolean {
  return value.length <= 500 && !/[\r\n\t]/.test(value)
}

function normalize(raw: unknown): LocalLlmConfig | null {
  if (!raw || typeof raw !== 'object') return null
  const cfg = raw as Partial<LocalLlmConfig>
  if (typeof cfg.base_url !== 'string' || typeof cfg.model !== 'string') return null
  if (typeof cfg.api_key !== 'string') return null
  const base_url = cfg.base_url.trim().replace(/\/+$/, '')
  const model = cfg.model.trim()
  const api_key = cfg.api_key.trim()
  if (!isValidBaseUrl(base_url) || !isValidModel(model) || !api_key) return null
  if (!isValidApiKey(api_key)) return null
  return { base_url, model, api_key }
}

export function loadLocalLlm(): LocalLlmConfig | null {
  return normalize(loadJSON<unknown>(KEY, null))
}

export function saveLocalLlm(cfg: LocalLlmConfig) {
  const clean = normalize(cfg)
  if (clean) saveJSON(KEY, clean)
  return clean
}

export function clearLocalLlm() {
  removeJSON(KEY)
}
