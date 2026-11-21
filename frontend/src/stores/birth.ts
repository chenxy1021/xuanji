import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { BirthInput } from '@/api/types'
import { loadJSON, saveJSON } from '@/lib/storage'

export function defaultBirth(): BirthInput {
  const now = new Date()
  return {
    calendar: 'solar',
    year: 1990,
    month: 1,
    day: 1,
    hour: now.getHours(),
    minute: now.getMinutes(),
    shichen: null,
    is_leap_month: false,
    gender: 'male',
    true_solar_time: true,
    place: null,
  }
}

/** 当前表单生辰，持久化到本地，刷新不丢 */
export const useBirthStore = defineStore('birth', () => {
  const birth = ref<BirthInput>(loadJSON('sm_birth', defaultBirth()))
  watch(birth, (b) => saveJSON('sm_birth', b), { deep: true })
  return { birth }
})

/** 合盘的第二个生辰（单独持久化，不影响主表单） */
export const useSecondaryStore = defineStore('secondaryBirth', () => {
  const birth = ref<BirthInput>(loadJSON('sm_birth_b', defaultBirth()))
  watch(birth, (b) => saveJSON('sm_birth_b', b), { deep: true })
  return { birth }
})
