interface TgWebApp {
  headerColor?: string
  initData?: string
  colorScheme?: 'light' | 'dark'
  isExpanded?: boolean
  themeParams?: Record<string, string>
  ready?(): void
  expand?(): void
  setHeaderColor?(color: string): void
  setBackgroundColor?(color: string): void
  onEvent?(event: string, cb: () => void): void
  disableVerticalSwipes?(): void
}

const wa = () => (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp

// 把 CSS 变量解析成 #rrggbb，Telegram 只认 hex / rgb
function cssColorHex(name: string): string | null {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  if (!raw) return null
  const probe = document.createElement('span')
  probe.style.color = raw
  document.body.append(probe)
  const m = getComputedStyle(probe).color.match(/\d+/g)
  probe.remove()
  if (!m || m.length < 3) return null
  const [r, g, b] = m.map((n) => Math.min(255, Number(n)).toString(16).padStart(2, '0'))
  return `#${r}${g}${b}`
}

export function syncTelegramTheme() {
  const app = wa()
  if (!app) return
  const fallback = app.colorScheme === 'dark' ? '#111418' : '#f5f3ee'
  const bg = cssColorHex('--color-bg') ?? fallback
  app.headerColor = bg
  app.setHeaderColor?.(bg)
  app.setBackgroundColor?.(bg)
}

export function initTelegram(): boolean {
  const app = wa()
  if (!app) return false
  document.documentElement.classList.add('tg-miniapp')
  app.ready?.()
  app.expand?.()
  app.disableVerticalSwipes?.()
  syncTelegramTheme()
  app.onEvent?.('themeChanged', syncTelegramTheme)
  return true
}
