import type { Shichen } from '@/api/types'

export const SHICHEN_HOURS: Record<Shichen, [number, number]> = {
  子: [23, 1],
  丑: [1, 3],
  寅: [3, 5],
  卯: [5, 7],
  辰: [7, 9],
  巳: [9, 11],
  午: [11, 13],
  未: [13, 15],
  申: [15, 17],
  酉: [17, 19],
  戌: [19, 21],
  亥: [21, 23],
}

export const SHICHEN_LIST = Object.keys(SHICHEN_HOURS) as Shichen[]

/** 公历小时 → 地支时辰（23 点起为子时） */
export function shichenOfHour(hour: number): Shichen {
  return SHICHEN_LIST[Math.floor(((hour + 1) % 24) / 2)]
}

export function pad(n: number) {
  return String(n).padStart(2, '0')
}

/** 用于提示文案：14:30 → 未时 13:00-15:00；en 时地支保留、单位换英文 */
export function describeTime(hour: number, minute: number, en = false) {
  const zhi = shichenOfHour(hour)
  const [start, end] = SHICHEN_HOURS[zhi]
  const name = en ? `${zhi} hour` : `${zhi}时`
  return `${pad(hour)}:${pad(minute)} → ${name} ${pad(start)}:00-${pad(end)}:00`
}
