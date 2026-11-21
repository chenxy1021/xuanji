import type { OptionField } from '@/api/types'
import { t } from '@/i18n'
import { fieldText } from '@/i18n/terms'

const pad = (n: number) => String(n).padStart(2, '0')

/** datetime-local / date / time → 后端要的字符串；空值返回 undefined（不提交该 key） */
export function toOptionValue(field: OptionField, raw: unknown): unknown {
  if (raw === '' || raw === null || raw === undefined) return undefined
  if (field.kind === 'datetime') return String(raw).replace('T', ' ').slice(0, 16)
  if (field.kind === 'number') {
    const n = Number(raw)
    return Number.isFinite(n) ? n : undefined
  }
  return raw
}

/** 表单初始值：优先 field.default，否则空 */
export function initialValues(fields: OptionField[]): Record<string, string | number | boolean> {
  const values: Record<string, string | number | boolean> = Object.fromEntries(
    fields.filter((f) => f.kind === 'toggle').map((f) => [f.key, Boolean(f.default)]),
  )
  for (const f of fields) {
    if (f.default === null || f.default === undefined) continue
    if (f.kind === 'datetime') values[f.key] = String(f.default).replace(' ', 'T').slice(0, 16)
    else if (f.kind !== 'toggle') values[f.key] = String(f.default)
  }
  return values
}

/** 只保留有值的 key；缺必填返回错误文案 */
export function collectOptions(
  fields: OptionField[],
  values: Record<string, unknown>,
): { options: Record<string, unknown>; error?: string } {
  const options: Record<string, unknown> = {}
  for (const f of fields) {
    const v = toOptionValue(f, values[f.key])
    if (v === undefined) {
      if (f.required) return { options, error: t('option.required', { label: fieldText(f).label }) }
      continue
    }
    options[f.key] = v
  }
  return { options }
}

export function nowLocalDatetime() {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function todayLabel() {
  return nowLocalDatetime().slice(0, 10)
}
