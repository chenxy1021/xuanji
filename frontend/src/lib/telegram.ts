interface TgInset {
  top?: number
  bottom?: number
  left?: number
  right?: number
}

interface TgWebApp {
  headerColor?: string
  initData?: string
  platform?: string
  colorScheme?: 'light' | 'dark'
  isExpanded?: boolean
  themeParams?: Record<string, string>
  safeAreaInset?: TgInset
  contentSafeAreaInset?: TgInset
  viewportStableHeight?: number
  ready?(): void
  expand?(): void
  setHeaderColor?(color: string): void
  setBackgroundColor?(color: string): void
  onEvent?(event: string, cb: () => void): void
  disableVerticalSwipes?(): void
}

const wa = () => (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp

// telegram-web-app.js 在普通浏览器里也会定义 WebApp（platform=unknown），
// 只有真正跑在 Telegram 容器里才返回它，避免普通网页被套上 Mini App 的样式。
const activeApp = (): TgWebApp | null => {
  const app = wa()
  if (!app || !app.platform || app.platform === 'unknown') return null
  return app
}

/** Telegram 明确声明的明暗；普通浏览器返回 null（此时跟系统走）。 */
export function telegramColorScheme(): 'light' | 'dark' | null {
  return activeApp()?.colorScheme ?? null
}

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
  const app = activeApp()
  if (!app) return
  const fallback = app.colorScheme === 'dark' ? '#121210' : '#f8f6f1'
  const bg = cssColorHex('--color-bg') ?? fallback
  app.headerColor = bg
  app.setHeaderColor?.(bg)
  app.setBackgroundColor?.(bg)
}

/**
 * 把 Telegram 的两层安全区写进 CSS 变量：
 * - safeAreaInset：刘海 / 状态栏 / home indicator
 * - contentSafeAreaInset：Telegram 自己的顶栏和底栏
 * 两者是叠加关系，展开（expand）后页面会铺到 Telegram 顶栏下面，
 * 必须把两者相加后再给页面留出顶部空间，否则站内 header 会被遮住。
 */
export function syncTelegramInsets() {
  const app = activeApp()
  if (!app) return
  const safe = app.safeAreaInset
  const content = app.contentSafeAreaInset
  const top = Math.max(0, (safe?.top ?? 0) + (content?.top ?? 0))
  const bottom = Math.max(0, (safe?.bottom ?? 0) + (content?.bottom ?? 0))
  const root = document.documentElement
  root.style.setProperty('--tg-safe-top', `${top}px`)
  root.style.setProperty('--tg-safe-bottom', `${bottom}px`)
  root.style.setProperty('--tg-viewport-stable-height', `${app.viewportStableHeight ?? window.innerHeight}px`)
}

export function initTelegram(): boolean {
  const app = activeApp()
  if (!app) return false
  document.documentElement.classList.add('tg-miniapp')
  app.ready?.()
  app.expand?.()
  app.disableVerticalSwipes?.()
  syncTelegramTheme()
  syncTelegramInsets()
  // expand() 之后安全区可能晚一帧才更新；事件之外再兜一次
  setTimeout(syncTelegramInsets, 300)
  window.addEventListener('load', syncTelegramInsets, { once: true })
  app.onEvent?.('themeChanged', () => {
    window.dispatchEvent(new Event('tg-theme-changed'))
    syncTelegramTheme()
  })
  // 展开、旋转、进入全屏都会改变安全区，事件触发后重新写变量
  for (const event of ['safeAreaChanged', 'contentSafeAreaChanged', 'viewportChanged', 'fullscreenChanged']) {
    app.onEvent?.(event, syncTelegramInsets)
  }
  window.addEventListener('resize', syncTelegramInsets, { passive: true })
  return true
}
