import type { OptionField, SystemSpec } from '@/api/types'
import { useLocale } from './index'

// 后端 name_en/tagline_en/label_en 就绪前的兜底；后端返回英文时优先用后端
const SYSTEM_EN: Record<string, { name: string; tagline: string }> = {
  bazi: { name: 'Four Pillars (Bazi)', tagline: 'Year, month, day and hour pillars with ten gods, luck cycles and annual flows' },
  ziwei: { name: 'Zi Wei Dou Shu', tagline: 'Twelve palaces, fourteen major stars and transformations across life areas' },
  astrology: { name: 'Western Astrology', tagline: 'Sun, Moon and Ascendant — temperament and relationship patterns' },
  qimen: { name: 'Qimen Life Chart', tagline: 'A life-span Qimen chart cast from your birth moment' },
  bazi_hepan: { name: 'Bazi Compatibility', tagline: 'Two Bazi charts compared: day masters, spouse palaces, zodiac and elements' },
  ziwei_hepan: { name: 'Ziwei Compatibility', tagline: 'Two Ziwei charts compared: life and spouse palaces, transformations' },
  liuyao: { name: 'Liuyao (I Ching)', tagline: 'Six-line divination with a primary, changed and nuclear hexagram' },
  tarot: { name: 'Tarot', tagline: 'Single, three, five-card or Celtic Cross spreads' },
  meihua: { name: 'Meihua Yishu', tagline: 'Plum Blossom numerology: body and use of a hexagram' },
  kongming: { name: 'Kongming Oracle', tagline: 'Zhuge Shenshu: three characters drawn by stroke count to one of 384 lots' },
  mbti: { name: 'MBTI Test', tagline: '32 quick questions on the four preference dimensions' },
}

const SYSTEM_ZH = {
  bazi: '四柱八字', ziwei: '紫微斗数', astrology: '西方占星', qimen: '奇门终身局',
  bazi_hepan: '八字合盘', ziwei_hepan: '紫微合盘', liuyao: '六爻纳甲', tarot: '塔罗牌',
  meihua: '梅花易数', kongming: '孔明神卦', mbti: 'MBTI 测试',
} as const

// label_en 缺省时按 key 兜底标签；hint/placeholder 一律用后端 *_en，避免和引擎文案脱节
const FIELD_EN: Record<string, { label: string }> = {
  method: { label: 'Casting method' },
  numbers: { label: 'Two numbers' },
  date: { label: 'Date' },
  hour: { label: 'Hour' },
  question: { label: 'Your question' },
  characters: { label: 'Three characters' },
}

export const isEn = () => useLocale().value === 'en'

export const systemName = (s: SystemSpec) => (isEn() && (s.name_en || SYSTEM_EN[s.id]?.name)) || s.name

export const systemTagline = (s: SystemSpec) => (isEn() && (s.tagline_en || SYSTEM_EN[s.id]?.tagline)) || s.tagline

/** 只有 id 时（如历史记录）用前端映射 */
export const systemNameById = (id: string) =>
  (isEn() ? SYSTEM_EN[id]?.name : SYSTEM_ZH[id as keyof typeof SYSTEM_ZH]) ?? null

// 只放设计文档/任务里明确写过的方法要点；没有资料的体系不显示方法说明
const METHOD_ZH: Record<string, string[]> = {
  bazi: ['以节气定月柱，非农历月份', '真太阳时按经度与均时差校正', '子时换日采用晚子时归次日'],
  qimen: ['以出生时刻起局，看年命、日干、时干三宫的一生格局'],
}
const METHOD_EN: Record<string, string[]> = {
  bazi: ['Month pillar is set by solar terms, not lunar months', 'True solar time corrects for longitude and the equation of time', 'The hour branch rolls over at late Zi hour'],
  qimen: ['Cast from the birth moment; read the year, day-stem and hour-stem palaces across a life'],
}
export const systemMethod = (id: string) => (isEn() ? METHOD_EN[id] : METHOD_ZH[id]) ?? []

export function fieldText(f: OptionField) {
  const en = isEn()
  const e = en ? FIELD_EN[f.key] : undefined
  return {
    label: (en && f.label_en) || e?.label || f.label,
    hint: (en && f.hint_en) || f.hint,
    placeholder: (en && f.placeholder_en) || f.placeholder,
    options: f.options?.map((o) => ({ value: o.value, label: (en && o.label_en) || o.label })),
  }
}

