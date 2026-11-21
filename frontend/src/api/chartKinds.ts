/**
 * 结果页各体系的 chart 形状与类型收窄。
 * 与 `types.ts` 分开放，避免和并行修改冲突。
 */

/**
 * 结果页只看四柱：与 types.ts 的 isBaziChart（还要求 dayun）分开，避免影响既有判定
 */
export const hasBaziPillars = (c: unknown): c is { pillars: Record<string, { gan: string; zhi: string; shishen: string; canggan: string }>; dayun?: unknown[]; liunian?: unknown[]; shensha?: string[] } =>
  !!c && typeof c === 'object' && 'pillars' in c

export interface MbtiDimension {
  key: string
  left: string
  right: string
  left_name: string
  right_name: string
  score: number
  left_pct: number
  right_pct: number
  dominant: string
  strength: string
}

export interface MbtiChart {
  type: string
  name: string
  summary: string
  strengths: string[]
  blind_spots: string[]
  fit: string
  dimensions: MbtiDimension[]
  answered: number
  disclaimer: string
}

export interface QimenPalace {
  number: number
  trigram: string
  direction: string
  element: string
  earth_stem: string
  hosted_earth_stem?: string | null
  heaven_stems: string[]
  stars: string[]
  door: string
  deity: string
  void_branches: string[]
  is_horse: boolean
}

export interface QimenAnchor {
  key: string
  label: string
  ganzhi: string
  stem: string
  stem_element?: string
  role: string
  basis: string
  palace: QimenPalace | null
  star?: string
  relation?: { name: string; note: string }
  readings: string[]
  summary: string
}

export interface QimenChart {
  method: string
  kind?: 'lifelong'
  lifelong?: {
    year_ming: QimenAnchor
    day: QimenAnchor
    hour: QimenAnchor
    anchors: QimenAnchor[]
    zodiac: string
    note: string
  }
  datetime: string
  four_pillars: Record<string, string>
  solar_term: string
  next_solar_term: string
  lunar_date: string
  dun: string
  yuan: string
  ju: number
  ju_text: string
  xun: { head: string; hidden_stem: string; void_branches: string[] }
  leaders: { star: string; door: string; original_palace: number; star_palace: number; door_palace: number }
  horse: { branch: string; palace: number }
  palaces: QimenPalace[]
  grid: QimenPalace[]
}

export interface AstrologyPoint {
  sign: string
  degree_in_sign: number
  element?: string
  mode?: string
}

export interface AstrologyPlanet {
  name: string
  longitude: number
  sign: string
  degree_in_sign: number
  retrograde: boolean
  house: number | null
}

export interface AstrologyAspect {
  a: string
  b: string
  type: string
  angle: number
  orb: number
}

export interface AstrologyChart {
  engine: string
  utc_time: string
  local_time: string
  timezone: number
  place: string
  zodiac: string
  house_system: string
  sun: AstrologyPoint
  moon: AstrologyPoint
  /** 缺出生地/时刻，或高纬度分宫无解时为 null */
  rising: { sign: string; degree_in_sign: number } | null
  mc: { sign: string; degree_in_sign: number } | null
  planets: AstrologyPlanet[]
  aspects: AstrologyAspect[]
  balance: {
    elements: Record<string, number>
    modes: Record<string, number>
  }
}

export interface MeihuaGua {
  name: string
  symbol?: string
  yixiang?: string
  code?: string
  upper: string
  lower: string
  upper_element?: string
  lower_element?: string
  meaning?: string
}

export interface MeihuaTrigramInfo {
  trigram: string
  element: string
  position: string
}

export interface MeihuaChart {
  method: string
  method_name?: string
  cast?: { detail?: string }
  ben?: MeihuaGua
  ben_gua?: MeihuaGua
  hu?: MeihuaGua
  hu_gua?: MeihuaGua
  bian?: MeihuaGua
  bian_gua?: MeihuaGua
  moving_line?: number
  moving_line_name?: string
  ti_yong?: { ti?: MeihuaTrigramInfo | string; yong?: MeihuaTrigramInfo | string } | string
  relation?: { code?: string; name: string; result: string; explain: string } | string
  judgement?: string
}

export interface KongmingChart {
  method: string
  method_name?: string
  question?: string
  characters: string[]
  counted_characters: string[]
  strokes: number[]
  digits: number[]
  calculation: {
    raw: number
    subtractions: number[]
    number: number
    detail: string
  }
  lot: {
    number: number
    fortune: string
    level: string
    palace: string
    hexagram: string
    changed: string
    line: string
    poem: string
  }
  reading: { tone: string; keywords: string[]; advice: string }
  disclaimer: string
}

const has = (c: unknown, ...keys: string[]) =>
  !!c && typeof c === 'object' && keys.every((k) => k in (c as Record<string, unknown>))

export const isMbtiChart = (c: unknown): c is MbtiChart => has(c, 'type', 'dimensions')

export const isQimenChart = (c: unknown): c is QimenChart => has(c, 'grid', 'ju_text')

export const isMeihuaChart = (c: unknown): c is MeihuaChart =>
  has(c, 'moving_line') && (has(c, 'ben') || has(c, 'ben_gua'))

export const isKongmingChart = (c: unknown): c is KongmingChart =>
  has(c, 'lot', 'calculation', 'characters') && !has(c, 'dimensions')

export const isAstrologyChart = (c: unknown): c is AstrologyChart =>
  has(c, 'planets', 'aspects', 'rising', 'sun', 'moon')
