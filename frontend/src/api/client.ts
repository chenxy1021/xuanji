import type { ChartEnvelope, HistoryRecord, MbtiQuiz, Place, SystemSpec } from './types'
import { t } from '@/i18n'

const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code = 'error',
    readonly status = 0,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, init)
  } catch {
    throw new ApiError(t('err.network'), 'network_error')
  }
  // 204 无正文
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) {
    throw new ApiError(data?.error?.message ?? t('err.request', { status: res.status }), data?.error?.code, res.status)
  }
  return data as T
}

export const getSystems = () => request<SystemSpec[]>('/systems')

export interface MetaInfo {
  llm_configured: boolean
  llm_base_url: string
  llm_model: string
  llm_source: LlmSource
  llm_key_hint: string
}

export type LlmSource = 'runtime' | 'env' | 'default'

export interface LlmSettings {
  configured: boolean
  base_url: string
  model: string
  source: LlmSource
  key_hint: string
}

export const getMeta = () => request<MetaInfo>('/meta')

export const getLlmSettings = () => request<LlmSettings>('/settings/llm')

export interface LlmSettingsBody {
  base_url?: string
  api_key?: string
  model?: string
  clear_key?: boolean
}

export const saveLlmSettings = (body: LlmSettingsBody) =>
  request<LlmSettings>('/settings/llm', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const resetLlmSettings = () => request<LlmSettings>('/settings/llm', { method: 'DELETE' })

export interface FocusTopic {
  id: string
  label: string
  label_en?: string
}

export const getFocusTopics = (system: string) =>
  request<{ system: string; topics: FocusTopic[] }>(`/focus/${system}`)

export const searchCities = (q: string, signal?: AbortSignal) =>
  request<Place[]>(`/geo/cities?${new URLSearchParams({ q })}`, { signal })

/* ---------------- 账号 ---------------- */

export interface AuthUser {
  id: number
  username: string
  is_admin: boolean
}

export interface AuthCredentials {
  username: string
  password: string
}

interface AuthResponse {
  user: AuthUser
}

const jsonPost = (body: unknown): RequestInit => ({
  method: 'POST',
  credentials: 'same-origin',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const register = (body: AuthCredentials) => request<AuthResponse>('/auth/register', jsonPost(body))

export const login = (body: AuthCredentials) => request<AuthResponse>('/auth/login', jsonPost(body))

export const logout = () =>
  request<null>('/auth/logout', { method: 'POST', credentials: 'same-origin' })

export const getMe = () => request<{ user: AuthUser | null }>('/auth/me', { credentials: 'same-origin' })

export const getMbtiQuiz = (lang: 'zh' | 'en', signal?: AbortSignal) =>
  request<MbtiQuiz>(`/quizzes/mbti?${new URLSearchParams({ lang })}`, { signal })

/* ---------------- 记录 / 解读存档（按账号隔离） ---------------- */

export interface StoredReading {
  text: string
  focus: string[]
  style: string | null
  question: string | null
  system: string | null
  updatedAt: number
}

export interface RecordBody {
  system: string
  title: string
  engine_version: string
  input: unknown
  chart: unknown
  text: string
  warnings: string[]
}

const send = <T>(method: string, path: string, body?: unknown) =>
  request<T>(path, {
    method,
    credentials: 'same-origin',
    ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  })

export const listRecords = () => send<HistoryRecord[]>('GET', '/records')

export const createRecord = (body: RecordBody) => send<HistoryRecord>('POST', '/records', body)

export const getRecord = (id: string) => send<HistoryRecord>('GET', `/records/${encodeURIComponent(id)}`)

export const deleteRecord = (id: string) => send<null>('DELETE', `/records/${encodeURIComponent(id)}`)

export const clearRecords = () => send<null>('DELETE', '/records')

export const getReading = (id: string) =>
  send<StoredReading | null>('GET', `/records/${encodeURIComponent(id)}/reading`)

export const saveReading = (id: string, body: Omit<StoredReading, 'updatedAt'>) =>
  send<StoredReading>('PUT', `/records/${encodeURIComponent(id)}/reading`, body)

export interface ChartBody {
  birth?: unknown
  secondary?: unknown
  options?: Record<string, unknown>
}

export const createChart = (system: string, body: ChartBody) =>
  request<ChartEnvelope>(`/charts/${system}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export interface InterpretParams {
  system: string
  chart: unknown
  question: string
  style: 'concise' | 'detailed'
  focus?: string[]
}

/** 解析 SSE 流，逐段回调解析出的事件。 */
export async function streamInterpret(
  params: InterpretParams,
  onEvent: (event: string, data: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response
  try {
    res = await fetch(BASE + '/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
      signal,
    })
  } catch {
    throw new ApiError('无法连接服务器，请确认后端已启动', 'network_error')
  }
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null)
    throw new ApiError(body?.error?.message ?? `请求失败（${res.status}）`, body?.error?.code, res.status)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const dispatch = (block: string) => {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
    }
    if (!dataLines.length) return
    try {
      onEvent(event, JSON.parse(dataLines.join('\n')))
    } catch {
      onEvent(event, { text: dataLines.join('\n') })
    }
  }
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      dispatch(buffer.slice(0, idx))
      buffer = buffer.slice(idx + 2)
    }
  }
  if (buffer.trim()) dispatch(buffer)
}
