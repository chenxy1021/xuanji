export type Calendar = 'solar' | 'lunar'
export type Gender = 'male' | 'female'
export type Shichen = '子' | '丑' | '寅' | '卯' | '辰' | '巳' | '午' | '未' | '申' | '酉' | '戌' | '亥'
export type SystemStatus = 'ready' | 'beta' | 'planned'

export interface Place {
  name: string
  province: string
  longitude: number
  latitude: number
  /** 国外城市或旧数据可能缺省 */
  timezone?: number
}

export interface BirthInput {
  calendar: Calendar
  year: number
  month: number
  day: number
  hour: number | null
  minute: number | null
  shichen: Shichen | null
  is_leap_month: boolean
  gender: Gender
  true_solar_time: boolean
  place: Place | null
}

export type SystemCategory = 'chart' | 'synastry' | 'divination' | 'fortune' | 'fun'
export type OptionFieldKind = 'select' | 'number' | 'text' | 'textarea' | 'date' | 'time' | 'datetime' | 'toggle'
export interface OptionField {
  key: string
  label: string
  label_en?: string
  kind: OptionFieldKind
  required?: boolean
  default?: unknown
  options?: { value: string; label: string; label_en?: string }[]
  placeholder?: string
  hint?: string
  placeholder_en?: string | null
  hint_en?: string | null
}

export interface SystemSpec {
  id: string
  name: string
  tagline: string
  name_en?: string
  tagline_en?: string
  requires_time: boolean
  requires_birth?: boolean
  requires_secondary?: boolean
  category?: SystemCategory
  fields?: OptionField[]
  status: SystemStatus
}

export interface MbtiQuiz {
  text_lang?: 'zh' | 'en'
  scale: { min: number; max: number; labels: string[] }
  questions: { id: string; dim: string; pole: string; text: string }[]
}

export interface BaziPillar {
  gan: string
  zhi: string
  shishen: string
  canggan: string
}

export interface TrueSolarTimeInfo {
  clock_time: string
  longitude_correction_minutes: number
  equation_of_time_minutes: number
  total_correction_minutes: number
  true_solar_time: string
}

export interface BaziChart {
  engine: string
  solar_date: string
  lunar_date: string
  shichen: string
  gender: string
  zishi: string
  pillars: Record<'year' | 'month' | 'day' | 'hour', BaziPillar>
  forward: boolean
  qiyun: string
  dayun: { index: string; age_range: string; ganzhi: string }[]
  liunian: { year: number; ganzhi: string }[]
  shensha: string[]
  jie: string | null
  true_solar_time: TrueSolarTimeInfo | null
}

export interface ChartEnvelope {
  system: string
  engine_version: string
  // 塔罗等不吃生辰的体系，input 结构不同
  input: BirthInput | Record<string, unknown>
  chart: BaziChart | ZiweiChart | TarotChart | LiuyaoChart | SynastryChart | Record<string, unknown>
  text: string
  warnings: string[]
}

export type StarKind = 'major' | 'lucky' | 'sha' | 'minor'

export interface ZiweiStar {
  name: string
  kind: StarKind
  brightness: string | null
  sihua: string | null
}

export interface ZiweiPalace {
  branch: string
  stem: string
  name: string
  is_ming: boolean
  is_shen: boolean
  stars: ZiweiStar[]
}

export interface ZiweiDecade {
  branch: string
  palace: string
  start_age: number
  end_age: number
  direction?: string
}

export interface ZiweiChart {
  engine: string
  solar_date: string
  lunar_date: string
  shichen: string
  gender: string
  bureau: string
  ming_gong: string
  shen_gong: string
  sihua: Record<string, string>
  palaces: ZiweiPalace[]
  decades: ZiweiDecade[]
  current_age: number
  current_decade: ZiweiDecade | null
}

export interface TarotCard {
  position: string
  name: string
  arcana: 'major' | 'minor'
  suit: string
  orientation: '正位' | '逆位'
  keywords: string
}

export interface TarotChart {
  engine: string
  spread: string
  spread_name: string
  spread_description: string
  question: string
  seed: number | null
  cards: TarotCard[]
}

export interface SpreadInfo {
  name: string
  description: string
  count: number
}

export interface LiuyaoLine {
  position: number
  yinyang: string
  moving: boolean
  gan_zhi: string
  branch: string
  wuxing: string
  liuqin: string
  liushen: string
  shi_ying: string | null
}

export interface LiuyaoGua {
  name: string
  full_name: string
  symbol: string
  upper: string
  lower: string
  palace: string
  element: string
  stage: string
  lines: LiuyaoLine[]
}

export interface LiuyaoChart {
  method: string
  method_name: string
  question: string
  cast_at: string
  lunar_date: string
  year_gan_zhi: string
  month_gan_zhi: string
  day_gan_zhi: string
  moving_lines: number[]
  ben_gua: LiuyaoGua
  bian_gua: LiuyaoGua | null
  hu_gua: LiuyaoGua
}

export interface SynastryPerson {
  gender?: string
  solar_date: string
  lunar_date: string
  shichen: string
  pillars?: Record<string, string>
  day_master?: string
  day_master_element?: string
  spouse_palace?: string
  zodiac?: string
  wuxing?: Record<string, number>
  missing?: string[]
  strongest?: string[]
  bureau?: string
  ming_branch?: string
  shen_branch?: string
  ming_stars?: string[]
  spouse_branch?: string
  spouse_stars?: string[]
  fude_branch?: string
  fude_stars?: string[]
  sihua?: Record<string, string>
}

export interface SynastryChart {
  engine: string
  a: SynastryPerson
  b: SynastryPerson
  matches: { scope: string; kind: string; detail: string; effect?: 'positive' | 'neutral' | 'negative' }[]
  complement?: { kind?: string; detail?: string }[]
  score: number
  level: string
  advice: string[]
  disclaimer: string
}

export interface HistoryRecord extends ChartEnvelope {
  id: string
  createdAt: number
  title: string
}

// 按 system 收窄 chart 的判定函数
export const isBaziChart = (c: unknown): c is BaziChart =>
  !!c && typeof c === 'object' && 'pillars' in c && 'dayun' in c
export const isZiweiChart = (c: unknown): c is ZiweiChart =>
  !!c && typeof c === 'object' && 'palaces' in c && 'bureau' in c
export const isTarotChart = (c: unknown): c is TarotChart =>
  !!c && typeof c === 'object' && 'spread_name' in c && 'cards' in c
export const isLiuyaoChart = (c: unknown): c is LiuyaoChart =>
  !!c && typeof c === 'object' && 'ben_gua' in c
export const isSynastryChart = (c: unknown): c is SynastryChart =>
  !!c && typeof c === 'object' && 'matches' in c && 'a' in c && 'score' in c

export const chartSubtitle = (c: unknown) =>
  c && typeof c === 'object' && 'lunar_date' in c ? String(c.lunar_date) : ''
