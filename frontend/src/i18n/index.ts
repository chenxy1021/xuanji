import { readonly, ref } from 'vue'
import { en } from './en'
import { zh } from './zh'

export type Locale = 'zh' | 'en'
export type MsgKey = keyof typeof zh
type Dict = Record<MsgKey, string>
type Params = Record<string, string | number>

const DICTS: Record<Locale, Dict> = { zh, en }

// 用 ref 让模板里的 t() 随语言自动刷新；不用 computed 是因为要在纯函数里也用
const locale = ref<Locale>('zh')
const listeners = new Set<(l: Locale) => void>()

export function setLocale(l: Locale) {
  locale.value = l
  document.documentElement.lang = l === 'en' ? 'en' : 'zh-CN'
  listeners.forEach((fn) => fn(l))
}

/** 监听语言变化（例如重新拉取系统清单） */
export function onLocaleChange(fn: (l: Locale) => void) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function setLocaleFrom(value: string | null | undefined) {
  setLocale(value === 'en' ? 'en' : 'zh')
}

export const useLocale = () => readonly(locale)

/** 查文案并插值；en 缺 key 时回退中文 */
export function t(key: MsgKey, params?: Params): string {
  const raw = DICTS[locale.value][key] || zh[key] || ''
  if (!params) return raw
  return raw.replace(/\{(\w+)\}/g, (m, k: string) => (params[k] === undefined ? m : String(params[k])))
}

