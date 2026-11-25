import { defineStore } from 'pinia'
import { ref } from 'vue'
import { clearRecords, deleteRecord, listRecords } from '@/api/client'
import type { HistoryRecord } from '@/api/types'
import { clearGuestRecords, deleteGuestRecord, findGuestRecord, listGuestRecords } from '@/lib/guestRecords'

export const useChartsStore = defineStore('charts', () => {
  const current = ref<HistoryRecord | null>(null)
  // 登录后从服务端拉取；未登录时只从本浏览器读取
  const history = ref<HistoryRecord[]>([])

  function addRecord(record: HistoryRecord) {
    history.value = [record, ...history.value.filter((r) => r.id !== record.id)]
  }

  async function loadFromServer() {
    history.value = await listRecords()
  }

  /** 未登录：把浏览器里保存的记录读进列表 */
  function loadLocal() {
    history.value = listGuestRecords()
  }

  // 当前这次排盘（含未登录的本地记录）也并进内存列表，保证结果页、记录页、AI 存档都按 id 找得到
  function remember(record: HistoryRecord) {
    current.value = record
    if (!history.value.some((r) => r.id === record.id)) history.value = [record, ...history.value]
  }

  /** 已登录时先删服务端，成功后再动内存；未登录删浏览器缓存 */
  async function remove(id: string, loggedIn: boolean) {
    if (loggedIn) await deleteRecord(id)
    else deleteGuestRecord(id)
    history.value = history.value.filter((r) => r.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function clear(loggedIn: boolean) {
    if (loggedIn) await clearRecords()
    else clearGuestRecords()
    history.value = []
    current.value = null
  }

  function reset() {
    history.value = []
    current.value = null
  }

  function find(id: string) {
    // 未登录刚起的盘不在列表里，也只在内存
    return history.value.find((r) => r.id === id) ?? (current.value?.id === id ? current.value : null)
  }

  /** 未登录直链/刷新时，绕过内存直接读浏览器缓存 */
  function findGuest(id: string) {
    return history.value.find((r) => r.id === id) ?? findGuestRecord(id)
  }

  return { current, history, addRecord, remember, loadFromServer, loadLocal, remove, clear, reset, find, findGuest }
})
