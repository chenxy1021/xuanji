import type { HistoryRecord } from '@/api/types'
import type { StoredReading } from '@/api/client'
import { loadJSON, saveJSON } from './storage'

/** 未登录时记录只留在本浏览器；登录后改由服务端按账号保存。 */
const RECORDS_KEY = 'sm_guest_records'
const READINGS_KEY = 'sm_guest_readings'
export const GUEST_RECORD_LIMIT = 50

function isRecord(value: unknown): value is HistoryRecord {
  if (!value || typeof value !== 'object') return false
  const rec = value as Partial<HistoryRecord>
  return (
    typeof rec.id === 'string' &&
    typeof rec.createdAt === 'number' &&
    typeof rec.system === 'string' &&
    typeof rec.text === 'string' &&
    !!rec.chart &&
    typeof rec.chart === 'object'
  )
}

export function listGuestRecords(): HistoryRecord[] {
  const raw = loadJSON<unknown>(RECORDS_KEY, [])
  return Array.isArray(raw) ? raw.filter(isRecord) : []
}

export function saveGuestRecord(record: HistoryRecord) {
  const next = [record, ...listGuestRecords().filter((r) => r.id !== record.id)].slice(
    0,
    GUEST_RECORD_LIMIT,
  )
  saveJSON(RECORDS_KEY, next)
}

export function deleteGuestRecord(id: string) {
  saveJSON(
    RECORDS_KEY,
    listGuestRecords().filter((r) => r.id !== id),
  )
  clearGuestReading(id)
}

export function clearGuestRecords() {
  saveJSON(RECORDS_KEY, [])
  saveJSON(READINGS_KEY, {})
}

export function findGuestRecord(id: string): HistoryRecord | null {
  return listGuestRecords().find((r) => r.id === id) ?? null
}

function readReadings(): Record<string, StoredReading> {
  const raw = loadJSON<unknown>(READINGS_KEY, {})
  return raw && typeof raw === 'object' && !Array.isArray(raw)
    ? (raw as Record<string, StoredReading>)
    : {}
}

export function getGuestReading(id: string): StoredReading | null {
  const reading = readReadings()[id]
  return reading && typeof reading.text === 'string' ? reading : null
}

export function saveGuestReading(id: string, reading: Omit<StoredReading, 'updatedAt'>) {
  const all = readReadings()
  all[id] = { ...reading, updatedAt: Date.now() }
  // 与记录同上限，避免已淘汰盘面的解读无限堆积
  const kept = Object.entries(all)
    .sort((a, b) => b[1].updatedAt - a[1].updatedAt)
    .slice(0, GUEST_RECORD_LIMIT)
  saveJSON(READINGS_KEY, Object.fromEntries(kept))
}

export function clearGuestReading(id: string) {
  const all = readReadings()
  if (!(id in all)) return
  delete all[id]
  saveJSON(READINGS_KEY, all)
}

export function newGuestId(): string {
  const uuid = globalThis.crypto?.randomUUID?.()
  return uuid ?? `guest-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}
