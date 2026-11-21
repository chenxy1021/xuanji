#!/usr/bin/env node
/**
 * 零依赖端到端冒烟脚本 —— 用 Chrome DevTools Protocol 直驱 headless Chrome。
 *
 *   node scripts/smoke.mjs
 *
 * 依赖：Node >= 22（原生 WebSocket / fetch）、本机 Google Chrome。
 * 不 npm install 任何包；脚本自己拉起 headless Chrome 并在结束时清理。
 *
 * 设计要点：视觉改造（tokens、紫微环状宫格）在并行进行，所以断言一律走
 * 文本内容或语义属性（section 标题、宫名、柱位标签、href），不依赖 class。
 *
 * 环境变量（都可省）：
 *   SMOKE_BASE    前端地址，默认自动探测 localhost:5173
 *   SMOKE_API     后端地址，默认自动探测 127.0.0.1:8000
 *   SMOKE_CHROME  Chrome 可执行文件路径
 */
import { spawn } from 'node:child_process'
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

const CHROME =
  process.env.SMOKE_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const SHOT_DIR = '/tmp'
const VIEWPORT = { width: 390, height: 844, deviceScaleFactor: 2, mobile: true }

const GAN = '甲乙丙丁戊己庚辛壬癸'
const ZHI = '子丑寅卯辰巳午未申酉戌亥'
const PILLAR_LABELS = ['年柱', '月柱', '日柱', '时柱']
const PALACE_12 = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄', '迁移', '交友', '官禄', '田宅', '福德', '父母']
const TAROT_POSITIONS = ['过去', '现在', '未来']

const results = []
const overflowChecks = []
/** 失败时用来抓现场（正文 + 当前 URL） */
const ctx = { page: null }

// ---------------------------------------------------------------------------
// 小工具
// ---------------------------------------------------------------------------

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function jsonLiteral(value) {
  return JSON.stringify(value)
}

async function pickBase(explicit, candidates, label) {
  const list = explicit ? [explicit, ...candidates] : candidates
  for (const base of list) {
    try {
      const res = await fetch(base + '/', { signal: AbortSignal.timeout(2500) })
      if (res.status < 500) return base.replace(/\/$/, '')
    } catch {
      /* 试下一个 */
    }
  }
  throw new Error(`找不到可用的${label}（试过：${list.join(', ')}）。请确认服务已启动。`)
}

// ---------------------------------------------------------------------------
// CDP 客户端
// ---------------------------------------------------------------------------

class CDP {
  #ws
  #nextId = 1
  #pending = new Map()
  #listeners = new Set()

  constructor(ws) {
    this.#ws = ws
    ws.addEventListener('message', (event) => this.#dispatch(event.data))
  }

  static async connect(url) {
    const ws = new WebSocket(url)
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('连接 DevTools WebSocket 超时')), 10000)
      ws.addEventListener('open', () => {
        clearTimeout(timer)
        resolve()
      })
      ws.addEventListener('error', () => {
        clearTimeout(timer)
        reject(new Error('连接 DevTools WebSocket 失败'))
      })
    })
    return new CDP(ws)
  }

  #dispatch(raw) {
    let msg
    try {
      msg = JSON.parse(typeof raw === 'string' ? raw : Buffer.from(raw).toString('utf8'))
    } catch {
      return
    }
    if (msg.id && this.#pending.has(msg.id)) {
      const { resolve, reject } = this.#pending.get(msg.id)
      this.#pending.delete(msg.id)
      if (msg.error) reject(new Error(`${msg.error.message}${msg.error.data ? `: ${msg.error.data}` : ''}`))
      else resolve(msg.result ?? {})
      return
    }
    for (const listener of this.#listeners) listener(msg)
  }

  send(method, params = {}, sessionId) {
    const id = this.#nextId++
    const payload = { id, method, params }
    if (sessionId) payload.sessionId = sessionId
    return new Promise((resolve, reject) => {
      this.#pending.set(id, { resolve, reject })
      this.#ws.send(JSON.stringify(payload))
      setTimeout(() => {
        if (this.#pending.delete(id)) reject(new Error(`CDP 调用超时：${method}`))
      }, 30000)
    })
  }

  onEvent(listener) {
    this.#listeners.add(listener)
    return () => this.#listeners.delete(listener)
  }

  close() {
    try {
      this.#ws.close()
    } catch {
      /* ignore */
    }
  }
}

// ---------------------------------------------------------------------------
// 启动 / 关闭 Chrome
// ---------------------------------------------------------------------------

function launchChrome() {
  if (!existsSync(CHROME)) {
    throw new Error(`找不到 Chrome：${CHROME}\n可用 SMOKE_CHROME 指定可执行文件路径。`)
  }
  const profileDir = mkdtempSync(path.join(tmpdir(), 'smoke-chrome-'))
  const args = [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profileDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-sync',
    '--mute-audio',
    '--hide-crash-restore-bubble',
    `--window-size=${VIEWPORT.width},${VIEWPORT.height}`,
    'about:blank',
  ]
  const proc = spawn(CHROME, args, { stdio: ['ignore', 'ignore', 'pipe'] })

  // 从 stderr 里捞 "DevTools listening on ws://..."
  const wsUrl = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('等待 Chrome DevTools 端点超时（10s）')), 10000)
    let buffer = ''
    proc.stderr.setEncoding('utf8')
    proc.stderr.on('data', (chunk) => {
      buffer += chunk
      const match = buffer.match(/DevTools listening on (ws:\/\/\S+)/)
      if (match) {
        clearTimeout(timer)
        resolve(match[1])
      }
    })
    proc.once('error', (err) => {
      clearTimeout(timer)
      reject(new Error(`启动 Chrome 失败：${err.message}`))
    })
    proc.once('exit', (code) => {
      clearTimeout(timer)
      reject(new Error(`Chrome 提前退出，code=${code}`))
    })
  })

  return { proc, profileDir, wsUrl }
}

// ---------------------------------------------------------------------------
// 页面会话
// ---------------------------------------------------------------------------

class Page {
  constructor(cdp, sessionId) {
    this.cdp = cdp
    this.sessionId = sessionId
  }

  async init() {
    await this.cdp.send('Page.enable', {}, this.sessionId)
    await this.cdp.send('Runtime.enable', {}, this.sessionId)
    await this.cdp.send('Emulation.setDeviceMetricsOverride', VIEWPORT, this.sessionId)
    await this.cdp.send('Emulation.setTouchEmulationEnabled', { enabled: true }, this.sessionId)
  }

  async evaluate(expression) {
    const res = await this.cdp.send(
      'Runtime.evaluate',
      { expression, returnByValue: true, awaitPromise: true, userGesture: true },
      this.sessionId,
    )
    if (res.exceptionDetails) {
      const detail = res.exceptionDetails.exception?.description || res.exceptionDetails.text
      throw new Error(`页面脚本抛错：${detail}`)
    }
    return res.result?.value
  }

  /** 轮询直到表达式返回真值；页面跳转导致上下文丢失时自动重试。 */
  async waitFor(expression, { timeout = 20000, interval = 150, label } = {}) {
    const started = Date.now()
    let lastError = null
    while (Date.now() - started < timeout) {
      try {
        const value = await this.evaluate(expression)
        if (value) return value
        lastError = null
      } catch (err) {
        lastError = err.message
      }
      await sleep(interval)
    }
    const suffix = lastError ? `（最后一次错误：${lastError}）` : ''
    throw new Error(`等待超时 ${timeout}ms：${label || expression}${suffix}`)
  }

  async goto(url) {
    await this.cdp.send('Page.navigate', { url }, this.sessionId)
    await sleep(200)
    const { pathname } = new URL(url)
    await this.waitFor(`location.pathname === ${jsonLiteral(pathname)}`, {
      label: `页面加载 ${url}（当前 ${pathname}）`,
    })
    await this.waitFor(`document.readyState === 'complete'`, { label: `文档加载完成 ${url}` })
  }

  /** 切换视口并等媒体查询/布局稳定（桌面档用 mobile:false，避免移动端 UA 行为干扰） */
  async setViewport(width, height) {
    await this.cdp.send(
      'Emulation.setDeviceMetricsOverride',
      { width, height, deviceScaleFactor: 2, mobile: width < 768 },
      this.sessionId,
    )
    this.viewport = { width, height }
    await sleep(280)
  }

  async screenshot(name, fullPage = false) {
    const { data } = await this.cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: fullPage }, this.sessionId)
    const file = path.join(SHOT_DIR, `smoke-${name}.png`)
    writeFileSync(file, Buffer.from(data, 'base64'))
    return file
  }

  /** 断言当前页无横向溢出：立即抛错（失败能定位到具体页面），同时留档给用例 6 汇总。 */
  async recordOverflow(label) {
    const metrics = await this.evaluate(`(() => {
      const de = document.documentElement
      return { scrollWidth: de.scrollWidth, innerWidth: window.innerWidth, clientWidth: de.clientWidth }
    })()`)
    const ok = metrics.scrollWidth === metrics.innerWidth
    overflowChecks.push({ label, ok, ...metrics })
    if (!ok) {
      throw new Error(
        `横向溢出：${label} scrollWidth=${metrics.scrollWidth} ≠ innerWidth=${metrics.innerWidth}`,
      )
    }
    return metrics
  }

  text() {
    return this.evaluate('document.body.innerText')
  }
}

// ---------------------------------------------------------------------------
// 用例
// ---------------------------------------------------------------------------

/**
 * 读取四柱。视觉改造中 DOM 从「卡片」变成「表格」，所以两种形态都支持；
 * 定位只用语义：表格首行的 年柱/月柱/日柱/时柱，或栏位标签文本。
 */
const FOUND_PILLARS = `(() => {
  const GAN = ${jsonLiteral(GAN)}
  const ZHI = ${jsonLiteral(ZHI)}
  const LABELS = ${jsonLiteral(PILLAR_LABELS)}
  const isGan = (v) => v.length === 1 && GAN.includes(v)
  const isZhi = (v) => v.length === 1 && ZHI.includes(v)

  // 形态 A：表格（首行是柱位，随后有「天干行」与「地支行」）
  for (const table of document.querySelectorAll('table')) {
    const rows = [...table.rows]
    if (rows.length < 2) continue
    const rawHeader = [...rows[0].cells].map((c) => (c.innerText || '').trim())
    const offset = rawHeader[0] === '' ? 1 : 0
    const header = rawHeader.slice(offset, offset + 4)
    if (header.length !== 4 || !LABELS.every((l, i) => header[i] === l)) continue
    const body = rows.slice(1).map((r) => [...r.cells].map((c) => (c.innerText || '').trim()))
    const pick = (test) => body.find((r) => r.length >= offset + 4 && r.slice(offset, offset + 4).every(test))
    const ganRow = pick(isGan)
    const zhiRow = pick(isZhi)
    if (ganRow && zhiRow) {
      return { kind: 'table', labels: header, gans: ganRow.slice(offset, offset + 4), zhis: zhiRow.slice(offset, offset + 4) }
    }
  }

  // 形态 B：卡片（每张卡首行是柱位标签，第 2/3 行是干支）
  const cards = []
  for (const el of document.querySelectorAll('*')) {
    if (el.children.length) continue
    const label = (el.textContent || '').trim()
    if (!LABELS.includes(label)) continue
    const parts = (el.parentElement.innerText || '').split('\\n').map((s) => s.trim()).filter(Boolean)
    cards.push({ label, parts })
  }
  if (cards.length === 4) {
    return {
      kind: 'cards',
      labels: cards.map((c) => c.label),
      gans: cards.map((c) => c.parts[1] || ''),
      zhis: cards.map((c) => c.parts[2] || ''),
    }
  }
  return null
})()`

/**
 * 读取十二宫。优先用 role="grid" + aria-label="紫微十二宫" + role="gridcell"
 * 这组语义钩子；若改造后钩子没了，退回「按宫名文本计数」。
 */
const FOUND_PALACES = `(() => {
  const NAMES = ${jsonLiteral(PALACE_12)}
  const grid = document.querySelector('[role="grid"][aria-label*="十二宫"]')
  const cells = grid ? [...grid.querySelectorAll('[role="gridcell"]')] : []
  const names = cells
    .map((cell) => ((cell.getAttribute('aria-label') || cell.innerText || '').trim().split(/\\s+/)[0] || ''))
    .filter(Boolean)
  const kind = grid ? 'grid' : 'text'
  let counted = names
  if (!grid) {
    counted = []
    for (const el of document.querySelectorAll('*')) {
      if (el.children.length) continue
      const text = (el.textContent || '').trim()
      if (NAMES.includes(text)) counted.push(text)
    }
  }
  return {
    kind,
    hasGrid: !!grid,
    hasLabelText: document.body.innerText.includes('十二宫'),
    count: counted.length,
    unique: [...new Set(counted)],
  }
})()`

const FOUND_TAROT = `(() => {
  const POSITIONS = ${jsonLiteral(TAROT_POSITIONS)}
  const leaves = [...document.querySelectorAll('*')].filter((el) => !el.children.length)
  return POSITIONS.map((p) => leaves.filter((el) => el.textContent.trim() === p).length)
})()`

// ---------------------------------------------------------------------------
// 表单操作：只靠 aria-label / 表单语义定位，不用 class
// ---------------------------------------------------------------------------

/** 给原生控件赋值并派发 input + change，让 v-model 与 @change 都能收到。 */
const SET_CONTROL = `(selector, value) => {
  const el = document.querySelector(selector)
  if (!el) return { ok: false, reason: 'not-found' }
  if (el.tagName === 'SELECT') {
    const options = [...el.options].map((o) => o.value)
    if (!options.includes(String(value))) return { ok: false, reason: 'no-option', options }
  }
  // 已有焦点时不再 focus()：change 会让输入框失焦，重复 focus 又不触发 focus 事件，下拉就打不开了
  if (document.activeElement !== el) el.focus()
  el.value = String(value)
  el.dispatchEvent(new Event('input', { bubbles: true }))
  el.dispatchEvent(new Event('change', { bubbles: true }))
  return { ok: true, value: el.value }
}`

async function setControl(page, selector, value) {
  const res = await page.evaluate(`(${SET_CONTROL})(${jsonLiteral(selector)}, ${jsonLiteral(String(value))})`)
  if (!res || !res.ok) {
    if (res && res.reason === 'no-option') {
      throw new Error(`控件 ${selector} 没有「${value}」这个选项，可选项：${res.options.slice(0, 12).join(', ')}…`)
    }
    throw new Error(`页面上找不到控件：${selector}`)
  }
  if (res.value !== String(value)) throw new Error(`控件 ${selector} 赋值失败：期望「${value}」实际「${res.value}」`)
  await sleep(60)
  return res.value
}

/** 出生表单的年/月/日/时/分对应 aria-label。 */
const BIRTH_SELECT_LABELS = { year: '年', month: '月', day: '日', hour: '时', minute: '分' }

async function fillBirthForm(page, birth = {}) {
  const applied = []
  for (const [key, label] of Object.entries(BIRTH_SELECT_LABELS)) {
    if (birth[key] == null) continue
    await setControl(page, `form select[aria-label="${label}"]`, birth[key])
    applied.push(`${label}=${birth[key]}`)
  }
  return applied
}

/** 出生地：PlacePicker 用 @mousedown 选中候选，所以派发 mousedown 而不是 click。 */
/** 像真人一样点开输入框再逐字键入（@focus 才会开下拉，直接设 value 不触发 focus 事件）。 */
async function typePlace(page, keyword) {
  const box = await page.evaluate(`(() => {
    const el = document.querySelector('input[aria-label="出生地"]')
    if (!el) return null
    el.focus()
    el.value = ''
    el.dispatchEvent(new Event('input', { bubbles: true }))
    const r = el.getBoundingClientRect()
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }
  })()`)
  if (!box) throw new Error('页面上找不到出生地输入框')
  const click = { type: 'mousePressed', button: 'left', clickCount: 1, x: box.x, y: box.y }
  await page.cdp.send('Input.dispatchMouseEvent', click, page.sessionId)
  await page.cdp.send('Input.dispatchMouseEvent', { ...click, type: 'mouseReleased' }, page.sessionId)
  await page.cdp.send('Input.insertText', { text: keyword }, page.sessionId)
  await sleep(80)
  const value = await page.evaluate(`document.querySelector('input[aria-label="出生地"]').value`)
  if (value !== keyword) throw new Error(`出生地输入框内容不符：期望「${keyword}」实际「${value}」`)
}

async function pickPlace(page, keyword) {
  await typePlace(page, keyword)
  const picked = await page.waitFor(
    `(() => {
      const btn = document.querySelector('ul li button')
      if (!btn) return null
      const label = btn.innerText.replace(/\\s+/g, ' ').trim()
      btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
      return label
    })()`,
    { timeout: 10000, label: `出生地候选「${keyword}」` },
  )
  // 选中后控件下方会打印经纬度
  await page.waitFor(`document.body.innerText.includes('经度')`, {
    timeout: 6000,
    label: `出生地已选定（${picked}）`,
  })
  return picked
}

/** 按可见文本点击按钮（不依赖 class）。 */
async function clickButton(page, text, { contains = false } = {}) {
  const matcher = contains
    ? `(label) => label.includes(want)`
    : `(label) => label === want`
  const clicked = await page.evaluate(`(() => {
    const want = ${jsonLiteral(text)}
    const matches = ${matcher}
    const btn = [...document.querySelectorAll('button')].find((b) =>
      matches((b.innerText || '').replace(/\\s+/g, ' ').trim()),
    )
    if (!btn || btn.disabled) return false
    btn.click()
    return true
  })()`)
  if (!clicked) throw new Error(`找不到可点击的按钮「${text}」`)
  await sleep(120)
}

/** 提交表单并等待跳到结果页。 */
async function submitAndWaitResult(page, label = '表单') {
  await page.waitFor(`!!document.querySelector('form button[type="submit"]')`, { label: `${label}：提交按钮出现` })
  await page.evaluate(`document.querySelector('form button[type="submit"]').click()`)
  await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: `${label}：跳转 /result` })
}

/** 走 UI 起一个默认八字盘，返回结果页 URL 里的记录 id */
async function chartBazi(page, base) {
  await page.goto(`${base}/chart/bazi`)
  await page.waitFor(`!!document.querySelector('form select[aria-label="年"]')`, { label: '八字生辰表单' })
  await submitAndWaitResult(page, '八字起盘')
  await page.waitFor(`!!document.querySelector('[data-result-hero]')`, { timeout: 20000, label: '结果页盘头' })
  return page.evaluate(`new URL(location.href).searchParams.get('id')`)
}

// ---------------------------------------------------------------------------
// 验收辅助：壳层断点、预置结果、可见元素点击
// ---------------------------------------------------------------------------

/** 壳层三件的可见性。DeskNav/AppHeader 都是 <header>，靠内部 nav[aria-label] 区分。 */
const SHELL_STATE = `(() => {
  const isVisible = (el) => {
    if (!el) return false
    const style = getComputedStyle(el)
    if (style.display === 'none' || style.visibility === 'hidden') return false
    const rect = el.getBoundingClientRect()
    return rect.height > 0 && rect.width > 0
  }
  const headers = [...document.querySelectorAll('header')]
  const deskNav = headers.find((h) => h.querySelector('nav[aria-label]')) || null
  const appHeader = headers.find((h) => h !== deskNav) || null
  const tabBar = [...document.querySelectorAll('nav')].find((n) => !n.getAttribute('aria-label')) || null
  return { deskNav: isVisible(deskNav), appHeader: isVisible(appHeader), tabBar: isVisible(tabBar) }
})()`

/** 断点期望：≥1024 桌面导航；768–1023 顶部栏；<768 顶部栏 + 底部 TabBar */
function expectedShell(width) {
  if (width >= 1024) return { deskNav: true, appHeader: false, tabBar: false }
  if (width >= 768) return { deskNav: false, appHeader: true, tabBar: false }
  return { deskNav: false, appHeader: true, tabBar: true }
}

function shellLabel(state) {
  return `desk=${state.deskNav ? 'on' : 'off'} header=${state.appHeader ? 'on' : 'off'} tab=${state.tabBar ? 'on' : 'off'}`
}

/**
 * 造一条记录再打开结果页，避免每条用例都重走表单。
 * 记录现在按账号存在后端：用 SMOKE_DB（临时库）走 openapi 注册一次性账号并登录，
 * 再把本地 envelope 直接灌进服务端库——不经过 /charts 重复计算，也不碰真实用户。
 */
class SeedError extends Error {
  constructor(message) {
    super(message)
    this.code = 'seed_unavailable'
  }
}

async function seedResult(page, { base, api }, { system, birth, secondary, options = {}, id, title }) {
  if (!process.env.SMOKE_DB) {
    throw new SeedError(
      '结果页改为按账号存储，预置记录需要临时库：用 SM_DB_PATH=/tmp/smoke-$$.db 起 8001 的 uvicorn，并设 SMOKE_BASE / SMOKE_API 指过去',
    )
  }
  const res = await fetch(`${api}/api/v1/charts/${system}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ birth, secondary, options }),
  })
  if (!res.ok) throw new Error(`预置结果失败：${system} → ${res.status} ${await res.text()}`)
  const envelope = await res.json()
  const record = {
    ...envelope,
    id: id || `smoke-seed-${system}`,
    createdAt: Date.now(),
    title: title || system,
  }
  await seedRecord({ api }, record)
  await page.goto(`${base}/`)
  await page.goto(`${base}/result?id=${encodeURIComponent(record.id)}`)
  return record
}

/** 当前套件账号：bootstrap 时自动建/登录；用例 27 会临时切换成别的账号 */
const session = { cookie: null, username: null }

/** 建一个一次性的临时账号并登录，返回 Cookie；记录按账号隔离，套件共用一个账号 */
async function ensureSeedUser({ api }) {
  if (session.cookie) return session.cookie
  // 固定用户名：重跑时第一个 register 会 409，随后登录即可命中原有的第一个用户（管理员）
  const username = 'smoke_seed'
  for (let i = 0; i < 50; i += 1) {
    for (const action of ['register', 'login']) {
      const res = await fetch(`${api}/api/v1/auth/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password: 'smoke-passw0rd' }),
      })
      if (res.ok) {
        setSession(res.headers.get('set-cookie'), username)
        return session.cookie
      }
      // 上一个临时库已注册过就改登录；节流时稍等重试
      if (res.status === 429) {
        await sleep(1500)
        break
      }
      const body = await res.text()
      // register 重名 → 改试 login；其余失败直接报出来
      if (action === 'login') throw new SeedError(`临时账号登录失败：HTTP ${res.status} ${body}`)
    }
  }
  throw new SeedError('临时账号注册被节流，重试次数用尽')
}

function setSession(rawCookie, username) {
  session.cookie = (rawCookie ?? '').split(';')[0]
  session.username = username
}

/** 在浏览器里换成指定账号的会话（Next 只加在 localhost 上） */
/** 走 UI 登录：Cookie 与前端 auth store 同时更新（只靠 CDP 写 Cookie 不会刷新已缓存的 /auth/me） */
async function loginCookie(page, base, { username }) {
  await setBrowserSession(page, base, null)
  await page.goto(`${base}/login`)
  await page.waitFor(`!!document.querySelector('#auth-username')`, { label: '登录表单' })
  await page.evaluate(`(() => {
    const set = (sel, v) => { const el = document.querySelector(sel); el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })) }
    set('#auth-username', ${jsonLiteral(username)})
    set('#auth-password', 'smoke-passw0rd')
  })()`)
  await page.evaluate(`document.querySelector('form button[type=submit]').click()`)
  await page.waitFor(`location.pathname !== '/login'`, { timeout: 15000, label: 'UI 登录跳转' })
  await page.waitFor(`!!document.querySelector('button[aria-label="账号菜单"]')`, { timeout: 10000, label: 'UI 已登录' })
}

async function setBrowserSession(page, base, cookie) {
  await page.cdp.send('Network.enable', {}, page.sessionId)
  // 先删后写：同名 Cookie 已存在时 setCookie 可能被忽略，删掉才能确实换账号
  await page.cdp.send('Network.deleteCookies', { name: 'sm_session', url: base }, page.sessionId)
  if (cookie) {
    const value = cookie.split('=')[1]
    // url 形式在部分 Chrome 版本上不生效；domain 形式靠 Network.enable 就能透传到 fetch
    await page.cdp.send(
      'Network.setCookie',
      { name: 'sm_session', value, domain: 'localhost', path: '/', expires: Math.floor(Date.now() / 1000) + 3600 },
      page.sessionId,
    )
  }
  const jar = await page.cdp.send('Network.getCookies', { urls: [`${base}/`] }, page.sessionId)
  const names = (jar.cookies || []).map((c) => c.name)
  if (cookie ? !names.includes('sm_session') : names.includes('sm_session')) {
    throw new Error(`浏览器会话 Cookie 写入/清除失败：${JSON.stringify(names)}`)
  }
  await page.goto(`${base}/`)
  await sleep(150)
}

/** 直接把 envelope 写进临时库（模拟服务端生成 id / createdAt 的存储结果） */
async function seedRecord({ api }, record) {
  const cookie = await ensureSeedUser({ api })
  const [cookieName, token] = cookie.split('=')
  // token 只用来校验 Cookie 形状；写库按用户名找 user_id
  if (cookieName !== 'sm_session' || !/^[A-Za-z0-9_-]+$/.test(token) || !session.username) {
    throw new SeedError('临时账号 Cookie 异常')
  }
  const { DatabaseSync } = await import('node:sqlite')
  const db = new DatabaseSync(process.env.SMOKE_DB)
  try {
    const row = db.prepare('SELECT id FROM users WHERE username = ?').get(session.username)
    if (!row) throw new SeedError('临时账号不在临时库里')
    const payload = JSON.stringify({
      system: record.system,
      title: record.title,
      engine_version: record.engine_version,
      input: record.input,
      chart: record.chart,
      text: record.text,
      warnings: record.warnings,
    })
    db.prepare('INSERT OR REPLACE INTO records(id, user_id, system, title, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)').run(
      record.id,
      row.id,
      record.system,
      record.title,
      payload,
      record.createdAt,
    )
  } finally {
    db.close()
  }
}

/** 点第一个「可见」的按钮（语言切换/主题切换在桌面与移动壳里各有一份，隐藏的那份别点）。 */
async function clickVisibleButton(page, text) {
  const clicked = await page.evaluate(`(() => {
    const want = ${jsonLiteral(text)}
    const btn = [...document.querySelectorAll('button')].find((b) => {
      const label = (b.innerText || '').replace(/\\s+/g, ' ').trim()
      if (label !== want) return false
      const style = getComputedStyle(b)
      const rect = b.getBoundingClientRect()
      return style.display !== 'none' && rect.width > 0 && rect.height > 0
    })
    if (!btn) return false
    btn.click()
    return true
  })()`)
  if (!clicked) throw new Error(`找不到可见按钮「${text}」`)
  await sleep(260)
}

/** 点第一个「可见」的纯图标按钮（按 aria-label 定位，主题切换只有图标没有文字）。 */
async function clickVisibleByAria(page, ariaLabel) {
  const clicked = await page.evaluate(`(() => {
    const want = ${jsonLiteral(ariaLabel)}
    const btn = [...document.querySelectorAll('button[aria-label]')].find((b) => {
      if (b.getAttribute('aria-label') !== want) return false
      const style = getComputedStyle(b)
      const rect = b.getBoundingClientRect()
      return style.display !== 'none' && rect.width > 0 && rect.height > 0
    })
    if (!btn) return false
    btn.click()
    return true
  })()`)
  if (!clicked) throw new Error(`找不到可见按钮（aria-label）「${ariaLabel}」`)
  await sleep(260)
}

/** 按可见文本点链接（「修改生辰/重新起盘」是 RouterLink 渲染的 <a>，不是 button）。 */
async function clickLink(page, text) {
  const clicked = await page.evaluate(`(() => {
    const want = ${jsonLiteral(text)}
    const link = [...document.querySelectorAll('a')].find(
      (a) => (a.innerText || '').replace(/\\s+/g, ' ').trim() === want,
    )
    if (!link) return false
    link.click()
    return true
  })()`)
  if (!clicked) throw new Error(`找不到可点击的链接「${text}」`)
  await sleep(150)
}

/** 点盘面展开/收起按钮：按钮内是两个 span，innerText 含换行，直接按 aria-expanded 定位。 */
async function clickChartToggle(page) {
  const clicked = await page.evaluate(`(() => {
    const btn = document.querySelector('[data-board-toggle]')
    if (!btn) return false
    btn.click()
    return true
  })()`)
  if (!clicked) throw new Error('找不到盘面展开/收起按钮（button[aria-expanded]）')
  await sleep(220)
}

/** 只把「真的超出视口」当溢出：桌面带滚动条时 scrollWidth 可能小于 innerWidth，不能要求相等。 */
async function noOverflow(page, label) {
  const m = await page.evaluate(
    `({
      sw: document.documentElement.scrollWidth,
      iw: window.innerWidth,
      cw: document.documentElement.clientWidth,
    })`,
  )
  if (m.sw > m.iw) throw new Error(`横向溢出：${label} scrollWidth=${m.sw} > innerWidth=${m.iw}`)
  return m
}

/** 浅色主题下的文字对比度探针（WCAG）：正文 ≥4.5:1，大字/次要 ≥3:1。 */
const CONTRAST_PROBE = `(() => {
  const parseColor = (value) => {
    const nums = String(value).match(/[\\d.]+/g)
    if (!nums || nums.length < 3) return null
    const [r, g, b] = nums.slice(0, 3).map(Number)
    if (nums.length > 3 && Number(nums[3]) === 0) return null
    return [r, g, b]
  }
  const luminance = ([r, g, b]) => {
    const channel = (v) => {
      const x = v / 255
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)
    }
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
  }
  const backgroundOf = (el) => {
    let node = el
    while (node && node !== document.documentElement) {
      const rgb = parseColor(getComputedStyle(node).backgroundColor)
      if (rgb) return rgb
      node = node.parentElement
    }
    return parseColor(getComputedStyle(document.body).backgroundColor) || [255, 255, 255]
  }
  const ratioOf = (el) => {
    const fg = parseColor(getComputedStyle(el).color)
    if (!fg) return 0
    const l1 = luminance(fg)
    const l2 = luminance(backgroundOf(el))
    const high = Math.max(l1, l2)
    const low = Math.min(l1, l2)
    return Math.round(((high + 0.05) / (low + 0.05)) * 100) / 100
  }
  const pick = [
    ['正文段落', document.querySelector('main p'), 4.5],
    ['主标题', document.querySelector('main h1') || document.querySelector('main h2'), 3],
    ['导航项', document.querySelector('nav[aria-label] a'), 4.5],
    ['主按钮', document.querySelector('main form button[type="submit"]') || document.querySelector('main button'), 4.5],
    ['次要文字', document.querySelector('main .text-muted') || document.querySelector('main small'), 3],
  ]
  return pick
    .filter(([, el]) => !!el)
    .map(([label, el, threshold]) => ({
      label,
      ratio: ratioOf(el),
      threshold,
      color: getComputedStyle(el).color,
    }))
})()`

async function main() {
  const base = await pickBase(process.env.SMOKE_BASE, ['http://localhost:5173', 'http://127.0.0.1:5173'], '前端服务')
  const api = await pickBase(process.env.SMOKE_API, ['http://127.0.0.1:8000', 'http://localhost:8000'], '后端服务')
  if (process.env.SMOKE_DB) {
    // 一次性临时账号：用户名固定，重跑会自动改登录；用完由临时库一起丢弃
    await ensureSeedUser({ api })
  }
  console.log(`前端 ${base}\n后端 ${api}\n视口 ${VIEWPORT.width}×${VIEWPORT.height}（mobile）\n`)

  const { proc, profileDir, wsUrl } = launchChrome()
  let cdp = null

  try {
    cdp = await CDP.connect(await wsUrl)
    const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' })
    const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true })
    const page = new Page(cdp, sessionId)
    await page.init()
    ctx.page = page

    // 界面语言钉死中文：前端把语言存进 localStorage.sm_locale（JSON 字符串），
    // 下面所有用例的文案选择器都按中文写，一旦界面切到英文就会全盘失配。
    await page.goto(`${base}/`)
    await page.evaluate(`localStorage.setItem('sm_locale', '"zh"')`)
    // 临时库模式：浏览器与预置记录共用同一个账号；会话 Cookie 只加在 localhost 上，不污染真实 8000
    if (session.cookie) {
      await page.cdp.send('Network.enable', {}, page.sessionId)
      await page.cdp.send('Network.deleteCookies', { name: 'sm_session', domain: 'localhost' }, page.sessionId)
      await page.cdp.send(
        'Network.setCookie',
        { name: 'sm_session', value: session.cookie.split('=')[1], domain: 'localhost', path: '/' },
        page.sessionId,
      )
      await page.goto(`${base}/`)
      // 移动端 Header 的账号菜单是紧凑态，不显示用户名，只能看登录态
      await page.waitFor(`!!document.querySelector('button[aria-label="账号菜单"]')`, { label: '冒烟账号已登录' })
    }
    await page.goto(`${base}/`)
    await page.waitFor(`document.documentElement.lang.startsWith('zh')`, { label: '界面语言锁定中文' })

    // 1. 后端体系清单（体系数量会随上线增长，故以 /systems 为准；需要锁死时设 SMOKE_EXPECT_SYSTEMS）
    const systems = await (async () => {
      const res = await fetch(`${api}/api/v1/systems`, { signal: AbortSignal.timeout(8000) })
      if (!res.ok) throw new Error(`GET /api/v1/systems 失败：HTTP ${res.status}`)
      return res.json()
    })()

    await run(`1. GET /api/v1/systems 全部 status=ready（当前 ${systems.length} 个体系）`, async () => {
      if (!Array.isArray(systems) || systems.length < 5) {
        throw new Error(`体系数量异常：${Array.isArray(systems) ? systems.length : typeof systems}`)
      }
      const expected = process.env.SMOKE_EXPECT_SYSTEMS
      if (expected && Number(expected) !== systems.length) {
        throw new Error(`期望 ${expected} 个体系，实际 ${systems.length}（SMOKE_EXPECT_SYSTEMS）`)
      }
      const notReady = systems.filter((s) => s.status !== 'ready')
      if (notReady.length) {
        throw new Error(`非 ready 体系：${notReady.map((s) => `${s.id}=${s.status}`).join(', ')}`)
      }
      return systems.map((s) => `${s.name}(${s.id})`).join(' / ')
    })

    // 2. 首页卡片：卡片数必须等于体系数，且每个 ready 体系都能点到 /chart/<id>
    await run(`2. 首页体系卡片数量 = 体系数 ${systems.length}`, async () => {
      await page.goto(`${base}/`)
      await page.waitFor(
        `new Set([...document.querySelectorAll('a[href^="/chart/"]')].map((a) => a.getAttribute('href'))).size === ${systems.length}`,
        { label: `首页出现 ${systems.length} 张体系卡片` },
      )
      const info = await page.evaluate(`(() => {
        const hrefs = [...new Set([...document.querySelectorAll('a[href^="/chart/"]')].map((a) => a.getAttribute('href')))]
        return { count: hrefs.length, hrefs, text: document.body.innerText }
      })()`)
      if (info.count !== systems.length) {
        throw new Error(`卡片数 ${info.count} ≠ 体系数 ${systems.length}`)
      }
      const noCard = systems.filter((s) => !info.hrefs.includes(`/chart/${s.id}`))
      if (noCard.length) throw new Error(`这些体系没有卡片链接：${noCard.map((s) => s.id).join(', ')}`)
      const missing = systems.filter((s) => !info.text.includes(s.name))
      if (missing.length) throw new Error(`首页缺少体系名：${missing.map((s) => s.name).join(', ')}`)
      await page.recordOverflow('首页 /')
      await page.screenshot('home')
      return `卡片 ${info.count} 个：${info.hrefs.join(', ')}`
    })

    // 3. 八字
    await run('3. 八字：提交默认表单 → 结果页含「四柱」且能读到四柱', async () => {
      await page.goto(`${base}/chart/bazi`)
      await page.recordOverflow('起盘页 /chart/bazi')
      await page.waitFor(`!!document.querySelector('form button[type="submit"]')`, { label: '八字表单按钮' })
      await page.screenshot('chart-bazi')
      await page.evaluate(`document.querySelector('form button[type="submit"]').click()`)
      await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: '跳转 /result' })
      await page.waitFor(`document.body.innerText.includes('四柱')`, { label: '结果页出现「四柱」' })
      const found = await page.waitFor(FOUND_PILLARS, { label: '读取四柱（表格或卡片）' })
      if (found.labels.length !== 4) throw new Error(`柱位数量应为 4，实际 ${found.labels.length}`)
      if (found.gans.length !== 4 || found.zhis.length !== 4) {
        throw new Error(`干支列数应为 4，实际 干:${found.gans.length} 支:${found.zhis.length}`)
      }
      const summary = found.labels.map((label, index) => {
        if (label !== PILLAR_LABELS[index]) throw new Error(`第 ${index + 1} 柱标签错：${label}`)
        const gan = found.gans[index] ?? ''
        const zhi = found.zhis[index] ?? ''
        if (gan.length !== 1 || !GAN.includes(gan)) throw new Error(`${label} 天干异常：「${gan}」`)
        if (zhi.length !== 1 || !ZHI.includes(zhi)) throw new Error(`${label} 地支异常：「${zhi}」`)
        return `${label}${gan}${zhi}`
      })
      await page.recordOverflow('八字结果页 /result')
      await page.screenshot('result-bazi')
      return summary.join(' ')
    })

    // 4. 紫微
    await run('4. 紫微：结果页含「十二宫」且宫格单元 = 12', async () => {
      await page.goto(`${base}/chart/ziwei`)
      await page.recordOverflow('起盘页 /chart/ziwei')
      await page.waitFor(`!!document.querySelector('form button[type="submit"]')`, { label: '紫微表单按钮' })
      await page.screenshot('chart-ziwei')
      await page.evaluate(`document.querySelector('form button[type="submit"]').click()`)
      await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: '跳转 /result' })
      const found = await page.waitFor(
        `(() => { const r = ${FOUND_PALACES}; return r && r.unique.length === 12 ? r : null })()`,
        { label: '读取十二宫宫格' },
      )
      // 「含十二宫」：环状宫格容器带 aria-label="紫微十二宫"，或正文出现该词
      if (!found.hasGrid && !found.hasLabelText) {
        throw new Error('结果页既没有 [aria-label*="十二宫"] 的宫格，正文里也没有「十二宫」')
      }
      if (found.count !== 12) throw new Error(`宫格单元应为 12，实际 ${found.count} 个`)
      const unknown = found.unique.filter((name) => !PALACE_12.includes(name))
      if (unknown.length) throw new Error(`出现未知宫名：${unknown.join(', ')}`)
      await page.recordOverflow('紫微结果页 /result')
      await page.screenshot('result-ziwei')
      return `${found.kind === 'grid' ? '环状宫格' : '宫名文本'} 12 宫：${found.unique.join(' ')}`
    })

    // 5. 塔罗
    await run('5. 塔罗：结果页含三张牌位（过去/现在/未来）', async () => {
      await page.goto(`${base}/chart/tarot`)
      await page.recordOverflow('起盘页 /chart/tarot')
      await page.waitFor(`!!document.querySelector('form button[type="submit"]')`, { label: '塔罗表单按钮' })
      await page.screenshot('chart-tarot')
      await page.evaluate(`document.querySelector('form button[type="submit"]').click()`)
      await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: '跳转 /result' })
      const counts = await page.waitFor(
        `(() => { const r = ${FOUND_TAROT}; return r.every((n) => n > 0) ? r : null })()`,
        { label: '三张牌位齐全' },
      )
      await page.recordOverflow('塔罗结果页 /result')
      await page.screenshot('result-tarot')
      return TAROT_POSITIONS.map((p, i) => `${p}×${counts[i]}`).join(' ')
    })

    // 6. 孔明神卦（诸葛亮马前课）：所问 + 三个字（佑咱统 → 第 24 签）
    await run('6. 孔明神卦：填所问 + 三个字（佑咱统）→ 结果页出现「第 24 签」与签文「意孜孜」', async () => {
      await page.goto(`${base}/chart/kongming`)
      await page.recordOverflow('起课页 /chart/kongming')
      await setControl(page, 'textarea[aria-label="所问之事"]', '这次换工作能否顺利？')
      await setControl(page, 'input[aria-label="写三个字"]', '佑咱统')
      await page.screenshot('chart-kongming')
      await submitAndWaitResult(page, '孔明神卦')
      const text = await page.waitFor(
        `(() => { const t = document.body.innerText; return /第\\s*24\\s*签/.test(t) ? t : null })()`,
        { timeout: 20000, label: '结果页出现「第 24 签」' },
      )
      const missing = ['意孜孜', '心戚戚'].filter((word) => !text.includes(word))
      if (missing.length) {
        throw new Error(`签文里找不到：${missing.join('、')}（正文节选：${text.replace(/\s+/g, ' ').slice(0, 160)}）`)
      }
      await page.recordOverflow('孔明神卦结果页 /result')
      await page.screenshot('result-kongming')
      return '第 24 签 · 意孜孜，心戚戚，要平安，防出入。'
    })

    // 7. 奇门终身局：出生表单起局
    await run('7. 奇门终身局：出生表单 → 结果页出现年命宫/日干宫/时干宫 且九宫 9 格', async () => {
      await page.goto(`${base}/chart/qimen`)
      await page.recordOverflow('起局页 /chart/qimen')
      await fillBirthForm(page, { year: 1990, month: 5, day: 15, hour: 14, minute: 30 })
      await page.screenshot('chart-qimen')
      await submitAndWaitResult(page, '奇门终身局')
      const anchors = ['年命宫', '日干宫', '时干宫']
      const info = await page.waitFor(
        `(() => {
          const t = document.body.innerText
          const wanted = ${jsonLiteral(anchors)}
          if (!wanted.every((k) => t.includes(k))) return null
          return { cells: document.querySelectorAll('[data-palace]').length }
        })()`,
        { timeout: 20000, label: '结果页出现年命宫/日干宫/时干宫' },
      )
      if (info.cells !== 9) throw new Error(`九宫应为 9 格，实际 ${info.cells} 个 [data-palace]`)
      await page.recordOverflow('奇门终身局结果页 /result')
      await page.screenshot('result-qimen')
      return `年命宫/日干宫/时干宫 齐全，九宫 ${info.cells} 格`
    })

    // 8. 梅花易数：默认时间起卦
    await run('8. 梅花易数：默认时间起卦 → 结果页出现「本卦」「体用」', async () => {
      await page.goto(`${base}/chart/meihua`)
      await page.recordOverflow('起卦页 /chart/meihua')
      await page.screenshot('chart-meihua')
      await submitAndWaitResult(page, '梅花易数')
      const info = await page.waitFor(
        `(() => {
          const t = document.body.innerText
          if (!t.includes('本卦') || !t.includes('体用')) return null
          const relation = t.match(/生克[：:][^\\n]{0,16}/)
          return {
            hu: t.includes('互卦'),
            bian: t.includes('变卦'),
            relation: relation ? relation[0].replace(/\\s+/g, '') : '',
          }
        })()`,
        { timeout: 20000, label: '结果页出现「本卦」「体用」' },
      )
      if (!info.hu || !info.bian) throw new Error(`互卦/变卦缺：互卦=${info.hu} 变卦=${info.bian}`)
      await page.recordOverflow('梅花易数结果页 /result')
      await page.screenshot('result-meihua')
      return `本卦/互卦/变卦齐全，${info.relation}`
    })

    // 9. MBTI：32 题逐题作答
    await run('9. MBTI：答完 32 题 → 结果页出现四字母类型', async () => {
      await page.goto(`${base}/chart/mbti`)
      await page.recordOverflow('答题页 /chart/mbti')
      const answered = await page.evaluate(`(async () => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
        const bar = () => document.querySelector('[role="progressbar"]')
        const progress = () => {
          const el = bar()
          return el ? Number(el.getAttribute('aria-valuenow')) : -1
        }
        let picks = 0
        for (let i = 0; i < 200; i += 1) {
          if (progress() >= 100) return { picks, done: true, progress: 100 }
          const option = document.querySelector('[role="radio"]')
          if (option) {
            option.click()
            picks += 1
          }
          await sleep(130)
        }
        return { picks, done: false, progress: progress() }
      })()`)
      if (!answered.done) {
        throw new Error(`32 题没答完（点了 ${answered.picks} 次，进度 ${answered.progress}%）`)
      }
      await page.screenshot('chart-mbti')
      await clickButton(page, '查看我的性格类型')
      await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: 'MBTI 跳转 /result' })
      const info = await page.waitFor(
        `(() => {
          const t = document.body.innerText
          const found = t.match(/[EI][NS][TF][JP]/)
          return found ? { type: found[0], dimensions: t.includes('维度') } : null
        })()`,
        { timeout: 20000, label: '结果页出现四字母类型' },
      )
      if (!info.dimensions) throw new Error('结果页没有「维度」分解')
      await page.recordOverflow('MBTI 结果页 /result')
      await page.screenshot('result-mbti')
      return `${info.type}（作答 ${answered.picks} 次点击）`
    })

    // 10. 西方占星：出生表单 + 出生地（有地点才有宫位/上升）
    await run('10. 西方占星：出生表单 + 出生地 → 结果页出现行星与宫位数据', async () => {
      await page.goto(`${base}/chart/astrology`)
      await page.recordOverflow('起盘页 /chart/astrology')
      await fillBirthForm(page, { year: 1990, month: 5, day: 15, hour: 14, minute: 30 })
      const place = await pickPlace(page, '北京')
      await page.screenshot('chart-astrology')
      await submitAndWaitResult(page, '西方占星')
      // 结果页现在是占星盘面板，从表格行上读行星/星座/宫位
      const chart = await page.waitFor(
        `(() => {
          const root = document.querySelector('[data-astrology]')
          if (!root) return null
          const rows = [...root.querySelectorAll('[data-planet]')].map((el) => ({
            name: el.dataset.planet,
            sign: el.dataset.sign,
            house: el.dataset.house === '' ? null : Number(el.dataset.house),
          }))
          if (!rows.length) return null
          return {
            planets: rows,
            rising: { sign: root.dataset.ascendant },
            aspects: Number(root.dataset.aspects),
          }
        })()`,
        { timeout: 20000, label: '结果页出现行星数据' },
      )
      const names = chart.planets.map((p) => p.name).filter(Boolean)
      const required = ['太阳', '月亮', '水星', '金星', '火星']
      const missing = required.filter((name) => !names.includes(name))
      if (missing.length) throw new Error(`行星里找不到：${missing.join('、')}（实际：${names.join('、')}）`)
      const housed = chart.planets.filter((p) => typeof p.house === 'number')
      if (housed.length !== chart.planets.length) {
        throw new Error(`宫位缺失：${chart.planets.length} 颗行星中只有 ${housed.length} 颗落宫`)
      }
      const signs = chart.planets.map((p) => p.sign).filter(Boolean)
      if (signs.length !== chart.planets.length) throw new Error('行星星座信息不完整')
      if (!chart.rising?.sign) throw new Error(`缺上升星座：${JSON.stringify(chart.rising)}`)
      if (!chart.aspects) throw new Error('缺相位（aspects）数据')
      await page.recordOverflow('西方占星结果页 /result')
      await page.screenshot('result-astrology')
      return `${place}｜行星 ${chart.planets.length} 颗全部落宫，上升${chart.rising.sign}，相位 ${chart.aspects} 组`
    })

    // 11. 八字合盘：甲乙方各一份生辰
    await run('11. 八字合盘：甲乙两方生辰 → 结果页出现评分与「合盘」', async () => {
      await page.goto(`${base}/chart/bazi_hepan`)
      await page.recordOverflow('起盘页 /chart/bazi_hepan')
      await page.waitFor(`!!document.querySelector('form button[type="submit"]')`, { label: '合盘表单按钮' })
      // spec 拉回后可能还有一次重渲染，先让 DOM 稳定再点，避免点到被替换的节点
      await sleep(250)
      await clickButton(page, '乙方生辰')
      // 不能只等「乙方生辰」出现在正文里——Tab 本来就有；要等乙方表单自己的提交按钮
      await page.waitFor(
        `[...document.querySelectorAll('form button[type="submit"]')].some((b) => (b.innerText || '').includes('保存乙方生辰'))`,
        { label: '切到乙方生辰表单' },
      )
      await fillBirthForm(page, { year: 1992, month: 8, day: 3, hour: 9, minute: 0 })
      await page.screenshot('chart-bazi-hepan')
      await clickButton(page, '保存乙方生辰')
      // 同理：`form button[type="submit"]` 两边都有，必须等甲方自己的「开始合盘」出现
      await page.waitFor(
        `[...document.querySelectorAll('form button[type="submit"]')].some((b) => (b.innerText || '').includes('开始合盘'))`,
        { label: '回到甲方生辰表单' },
      )
      await sleep(200)
      await clickButton(page, '开始合盘')
      await page.waitFor(`location.pathname === '/result'`, { timeout: 30000, label: '合盘跳转 /result' })
      const info = await page.waitFor(
        `(() => {
          const t = document.body.innerText
          if (!t.includes('合盘')) return null
          const score = t.match(/合盘评分[\\s\\S]{0,40}?(\\d{1,3}(?:\\.\\d+)?)/)
          if (!score) return null
          const level = t.match(/匹配度\\s*[「"]([^」"]+)[」"]/)
          return { score: Number(score[1]), level: level ? level[1] : '' }
        })()`,
        { timeout: 20000, label: '结果页出现合盘评分' },
      )
      if (!(info.score >= 0 && info.score <= 100)) throw new Error(`评分越界：${info.score}`)
      if (!info.level) throw new Error('结果页没有「匹配度「…」」评级')
      await page.recordOverflow('八字合盘结果页 /result')
      await page.screenshot('result-bazi-hepan')
      return `合盘评分 ${info.score} · 匹配度「${info.level}」`
    })

    // 12. 无横向溢出（汇总前面已访问的页面；/history 的溢出由用例 13 就地断言）
    await run('12. 所有页面无横向溢出（scrollWidth === innerWidth）', async () => {
      if (!overflowChecks.length) throw new Error('没有采集到任何页面')
      const bad = overflowChecks.filter((item) => !item.ok)
      if (bad.length) {
        throw new Error(
          bad
            .map((item) => `${item.label}: scrollWidth=${item.scrollWidth} > innerWidth=${item.innerWidth}`)
            .join('; '),
        )
      }
      const labels = overflowChecks.map((item) => item.label).join('、')
      return `${overflowChecks.length} 处全部 ${VIEWPORT.width}px 内不溢出：${labels}`
    })

    // 13. 历史
    await run('13. /history 能列出刚生成的记录', async () => {
      await page.goto(`${base}/history`)
      await page.waitFor(`document.body.innerText.includes('排盘记录')`, { label: '历史页标题' })
      const info = await page.waitFor(
        `(() => {
          const links = [...document.querySelectorAll('a[href*="/result?id="]')]
          return links.length >= 3 ? { count: links.length, text: document.body.innerText } : null
        })()`,
        { label: '历史记录 >= 3 条' },
      )
      // 历史标题形如「1990-01-01 四柱八字」「塔罗 · 三张牌」，故塔罗只匹配「塔罗」
      const wanted = ['四柱八字', '紫微斗数', '塔罗']
      const missing = wanted.filter((name) => !info.text.includes(name))
      if (missing.length) throw new Error(`历史里找不到：${missing.join(', ')}`)
      await page.recordOverflow('历史页 /history')
      await page.screenshot('history')
      return `${info.count} 条记录，含 ${wanted.join('/')}`
    })

    // 14. 占星降级路径：缺出生地 / 高纬度 → 不算上升宫位，但行星照常显示
    await run('14. 西方占星：缺出生地 / 高纬度时降级显示', async () => {
      const cases = [
        {
          label: '缺出生地',
          birth: { calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male' },
          expect: '出生地',
        },
        {
          label: '高纬度',
          birth: {
            calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
            place: { name: '特罗姆瑟', longitude: 18.955, latitude: 69.649, timezone: 1 },
          },
          expect: '纬度',
        },
      ]
      for (const item of cases) {
        const res = await fetch(`${api}/api/v1/charts/astrology`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ birth: item.birth }),
        })
        if (!res.ok) throw new Error(`${item.label}：接口 ${res.status} ${await res.text()}`)
        const envelope = await res.json()
        if (envelope.chart.rising !== null) throw new Error(`${item.label}：上升应为 null`)
        if (!envelope.warnings.some((w) => w.includes(item.expect))) {
          throw new Error(`${item.label}：后端警告未提到「${item.expect}」：${envelope.warnings.join(' / ')}`)
        }
        if (envelope.warnings.some((w) => w.includes('swisseph'))) {
          throw new Error(`${item.label}：警告泄漏内部错误名：${envelope.warnings.join(' / ')}`)
        }

        const record = {
          ...envelope,
          id: `smoke-degraded-${item.label}`,
          createdAt: Date.now(),
          title: `西方占星 · ${item.label}`,
        }
        await seedRecord({ api }, record)
        await page.goto(`${base}/result?id=${encodeURIComponent(record.id)}`)

        const info = await page.waitFor(
          `(() => {
            const root = document.querySelector('[data-astrology]')
            return root ? { asc: root.dataset.ascendant, text: document.body.innerText } : null
          })()`,
          { timeout: 15000, label: `${item.label}：结果页出现占星面板` },
        )
        if (info.asc !== '') throw new Error(`${item.label}：不应标出上升，实际「${info.asc}」`)
        if (!info.text.includes('本命盘')) throw new Error(`${item.label}：标题未降级为「本命盘」`)
        if (!info.text.includes('未算出')) throw new Error(`${item.label}：页面上没有「未算出上升与宫位」提示`)
        const houses = await page.evaluate(
          `[...document.querySelectorAll('[data-planet]')].map((el) => el.dataset.house)`,
        )
        if (houses.length !== 10) throw new Error(`${item.label}：行星行 ${houses.length} 条，应为 10`)
        if (houses.some((h) => h !== '')) throw new Error(`${item.label}：宫位应为空，实际 ${houses.join(',')}`)
        const { sw, iw } = await page.evaluate(
          `({ sw: document.documentElement.scrollWidth, iw: window.innerWidth })`,
        )
        if (sw > iw) throw new Error(`${item.label}：${VIEWPORT.width}px 视口下横向溢出 ${sw} > ${iw}`)
      }
      await page.screenshot('result-astrology-degraded')
      return `${cases.map((c) => c.label).join(' / ')} 均降级正常：本命盘 + 未算出提示 + 10 行星仍显示`
    })

    // 15. 占星逆行标记：表格「是/—」与盘面 R 上标都要跟后端 retrograde 对得上
    await run('15. 西方占星：逆行标记（表格 是/— + 盘面 R）与后端数据逐颗一致', async () => {
      const birth = {
        calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
        place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
      }
      const res = await fetch(`${api}/api/v1/charts/astrology`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ birth }),
      })
      if (!res.ok) throw new Error(`接口 ${res.status} ${await res.text()}`)
      const envelope = await res.json()
      const expected = new Map(envelope.chart.planets.map((p) => [p.name, !!p.retrograde]))
      const retroNames = [...expected].filter(([, v]) => v).map(([name]) => name)
      // 样例盘里逆行/顺行都得有，否则这条用例没有区分度
      if (!retroNames.length || retroNames.length === expected.size) {
        throw new Error(`样例盘逆行分布不具区分度：${retroNames.join('、') || '全部顺行'}`)
      }

      const record = {
        ...envelope,
        id: 'smoke-retrograde',
        createdAt: Date.now(),
        title: '西方占星 · 逆行标记',
      }
      await seedRecord({ api }, record)
      await page.goto(`${base}/result?id=${encodeURIComponent(record.id)}`)

      const info = await page.waitFor(
        `(() => {
          const rows = [...document.querySelectorAll('[data-planet]')]
          if (rows.length !== 10) return null
          return {
            rows: rows.map((el) => {
              // 行上有 data-retrograde 钩子就优先用它，否则退回最后一列（逆行列）的文字
              const hook = el.dataset.retrograde
              const cells = [...el.children]
              return {
                name: el.dataset.planet,
                hook: hook === undefined ? null : hook,
                rendered: hook === undefined ? (cells[cells.length - 1].textContent || '').trim() : hook,
              }
            }),
            hookPath: rows.every((el) => el.dataset.retrograde !== undefined),
            wheelR: [...document.querySelectorAll('svg tspan')]
              .filter((t) => (t.textContent || '').trim() === 'R').length,
          }
        })()`,
        { timeout: 15000, label: '逆行表格出现 10 行星' },
      )

      const problems = []
      for (const row of info.rows) {
        const want = expected.get(row.name)
        const shownYes = row.rendered === 'true' || row.rendered === '是'
        if (want !== shownYes) {
          problems.push(`${row.name}：后端 ${want ? '逆行' : '顺行'}，页面显示「${row.rendered}」`)
        }
      }
      if (problems.length) throw new Error(`逆行列与后端不一致：${problems.join('；')}`)
      if (info.wheelR !== retroNames.length) {
        throw new Error(`盘面 R 上标 ${info.wheelR} 个，应为 ${retroNames.length} 个（${retroNames.join('、')}）`)
      }
      await page.recordOverflow('西方占星逆行标记结果页 /result')
      await page.screenshot('result-astrology-retrograde')
      const source = info.hookPath ? 'data-retrograde 钩子' : '行内最后一列文字'
      return `逆行星 ${retroNames.join('、')}；表格 是/— 与盘面 R 上标（${info.wheelR} 个）均与后端一致（取值来源：${source}）`
    })

    // 16. 视口矩阵：四档视口 × 六页，壳层断点 + 无横向溢出
    await run('16. 视口矩阵：1440/1024/768/390 壳层断点正确、六页无横向溢出', async () => {
      const viewports = [
        [1440, 900],
        [1024, 768],
        [768, 1024],
        [390, 844],
      ]
      const routes = [
        ['/', '首页'],
        ['/chart/bazi', '八字起盘'],
        ['/chart/astrology', '占星起盘'],
        ['/history', '记录'],
        ['/settings', '设置'],
      ]
      const report = []
      for (const [width, height] of viewports) {
        await page.setViewport(width, height)
        await page.goto(`${base}/`)
        const shell = await page.evaluate(SHELL_STATE)
        const want = expectedShell(width)
        const mismatch = ['deskNav', 'appHeader', 'tabBar'].filter((key) => shell[key] !== want[key])
        if (mismatch.length) {
          throw new Error(
            `${width}×${height} 壳层不符：期望 ${shellLabel(want)}，实际 ${shellLabel(shell)}（不符项 ${mismatch.join(',')}）`,
          )
        }
        await page.screenshot(`vp-${width}-home`)
        for (const [route, label] of routes) {
          await page.goto(`${base}${route}`)
          await noOverflow(page, `${width}×${height} ${label} ${route}`)
        }
        report.push(`${width}px ${shellLabel(shell)}`)
      }
      await page.setViewport(VIEWPORT.width, VIEWPORT.height)
      await page.goto(`${base}/`)
      return report.join('｜')
    })

    // 17. 结果页桌面布局（1440）
    await run('17. 结果页桌面 1440：左栏 380 sticky 可滚 + 双 Tab 可切 + AI 友好提示 + 隐藏/修改生辰', async () => {
      await page.setViewport(1440, 900)
      await seedResult(
        page,
        { base, api },
        {
          system: 'bazi',
          id: 'smoke-accept-bazi',
          title: '四柱八字',
          birth: {
            calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
            place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
          },
        },
      )
      await noOverflow(page, '1440 八字结果页')
      const layout = await page.waitFor(
        `(() => {
          const aside = document.querySelector('aside')
          if (!aside) return null
          const style = getComputedStyle(aside)
          const rect = aside.getBoundingClientRect()
          return {
            position: style.position,
            width: Math.round(rect.width),
            overflowY: style.overflowY,
            scrollHeight: aside.scrollHeight,
            clientHeight: aside.clientHeight,
            top: Math.round(rect.top),
          }
        })()`,
        { timeout: 15000, label: '结果页左栏出现' },
      )
      if (layout.position !== 'sticky') throw new Error(`左栏应为 sticky，实际 ${layout.position}`)
      if (Math.abs(layout.width - 380) > 2) throw new Error(`左栏宽度应 380，实际 ${layout.width}`)
      if (!['auto', 'scroll', 'overlay'].includes(layout.overflowY)) {
        throw new Error(`左栏 overflow-y 应可滚，实际 ${layout.overflowY}`)
      }
      await page.screenshot('desktop-1440-result-bazi')

      // 内容高于视口时，左栏必须自己能滚到底（换矮视口逼出溢出）
      await page.setViewport(1440, 560)
      const scrolled = await page.waitFor(
        `(() => {
          const aside = document.querySelector('aside')
          if (!aside) return null
          const needsScroll = aside.scrollHeight > aside.clientHeight + 2
          if (!needsScroll) return { needsScroll: false, scrollHeight: aside.scrollHeight, clientHeight: aside.clientHeight }
          aside.scrollTop = aside.scrollHeight
          const max = aside.scrollTop
          const rect = aside.getBoundingClientRect()
          const last = aside.lastElementChild ? aside.lastElementChild.getBoundingClientRect() : null
          return {
            needsScroll: true,
            max: Math.round(max),
            scrollHeight: aside.scrollHeight,
            clientHeight: aside.clientHeight,
            lastBottom: last ? Math.round(last.bottom) : null,
            asideBottom: Math.round(rect.bottom),
          }
        })()`,
        { timeout: 8000, label: '左栏滚动测试' },
      )
      if (!scrolled.needsScroll) {
        throw new Error(`1440×560 下左栏内容并未超高（${scrolled.scrollHeight}/${scrolled.clientHeight}），无法验证可滚`)
      }
      if (scrolled.max <= 0) throw new Error('左栏 scrollHeight > clientHeight 但 scrollTop 无法移动，说明被裁切')
      if (scrolled.lastBottom != null && scrolled.lastBottom > scrolled.asideBottom + 2) {
        throw new Error(`滚到底后最后一块仍超出左栏可视区：${scrolled.lastBottom} > ${scrolled.asideBottom}`)
      }
      await page.setViewport(1440, 900)

      // 右栏盘头 + 盘面要点卡
      const pane = await page.evaluate(`(() => ({
        hero: !!document.querySelector('[data-result-hero]'),
        seal: !!document.querySelector('.result-seal'),
        facts: document.querySelectorAll('[data-result-facts] .fact-card').length,
        visible: [...document.querySelectorAll('[data-result-facts] .fact-card')]
          .every((el) => el.getBoundingClientRect().height > 40),
      }))()`)
      if (!pane.hero || !pane.seal) throw new Error('右栏盘头或印章未渲染')
      if (pane.facts < 3) throw new Error(`右栏盘面要点卡过少：${pane.facts}`)
      if (!pane.visible) throw new Error('盘面要点卡高度异常')

      // 右栏双 Tab
      await clickButton(page, 'AI 对话')
      await page.waitFor(`document.querySelectorAll('[data-focus-id]').length >= 5`, {
        label: 'AI 解读方向标签',
      })
      const chips = await page.evaluate(`(() => {
        const all = [...document.querySelectorAll('[data-focus-id]')]
        return {
          count: all.length,
          on: all.filter((c) => c.getAttribute('aria-pressed') === 'true').length,
          hasSettingsLink: document.body.innerText.includes('去设置里填写'),
        }
      })()`)
      if (chips.count < 5) throw new Error(`解读方向过少：${chips.count}`)
      if (chips.on !== 1) throw new Error(`默认应选中「命格总览」一个方向，实际 ${chips.on}`)
      if (!chips.hasSettingsLink) throw new Error('未配 key 时 AI 面板缺「去设置里填写」入口')
      await page.evaluate(`(() => {
        const chip = [...document.querySelectorAll('[data-focus-id]')]
          .find((c) => c.getAttribute('aria-pressed') !== 'true')
        chip && chip.click()
      })()`)
      await page.waitFor(
        `(() => {
          const all = [...document.querySelectorAll('[data-focus-id]')]
          return all.filter((c) => c.getAttribute('aria-pressed') === 'true').length === 2
            && document.body.innerText.includes('已选 2 个方向')
        })()`,
        { timeout: 5000, label: '解读方向可多选' },
      )
      // 未配 key 时 /meta 会提前给出提示，并把入口置灰
      const chat = await page.waitFor(
        `(() => {
          const text = document.body.innerText
          const pressed = [...document.querySelectorAll('button[aria-pressed]')]
            .filter((b) => (b.innerText || '').trim() === 'AI 对话')
            .every((b) => b.getAttribute('aria-pressed') === 'true')
          const start = [...document.querySelectorAll('button')].find((b) =>
            ['开始解读', 'AI 解读不可用'].includes((b.innerText || '').trim()),
          )
          const hasFriendly = text.includes('暂不可用')
          const hasError = text.includes('解读失败')
          return pressed && hasFriendly
            ? { pressed, hasFriendly, hasError, startDisabled: start ? start.disabled : null }
            : null
        })()`,
        { timeout: 15000, label: 'AI 对话面板' },
      )
      if (!chat.pressed) throw new Error('点「AI 对话」后 aria-pressed 未切换')
      if (chat.hasError) throw new Error('AI 未配 key 时页面出现「解读失败」错误态')
      if (chat.startDisabled !== true) throw new Error('AI 未配 key 时「开始解读」未置灰')
      await page.screenshot('desktop-1440-result-ai-tab')
      await clickButton(page, '命盘分析')
      await page.waitFor(`document.body.innerText.includes('命盘分析')`, { label: '切回命盘分析' })

      // 隐藏生辰 → 打码；再显示 → 恢复
      const beforeMask = await page.evaluate(`(() => ({
        born: !!document.body.innerText.match(/\\d{4}-\\d{2}-\\d{2}/),
        masked: document.body.innerText.includes('生辰已隐藏'),
      }))()`)
      if (!beforeMask.born) throw new Error('结果页没有出生行日期，无法验证打码')
      if (beforeMask.masked) throw new Error('初始就处于已隐藏状态')
      await clickButton(page, '隐藏生辰')
      const afterMask = await page.waitFor(
        `(() => {
          const text = document.body.innerText
          const bornLine = [...document.querySelectorAll('p')].some((p) => /\\d{4}-\\d{2}-\\d{2}/.test(p.innerText || ''))
          return { masked: text.includes('生辰已隐藏'), bornLine }
        })()`,
        { timeout: 8000, label: '隐藏生辰生效' },
      )
      if (!afterMask.masked) throw new Error('点「隐藏生辰」后没有出现「生辰已隐藏」')
      if (afterMask.bornLine) throw new Error('点「隐藏生辰」后出生行日期仍可见')
      // 右栏长文是后端 text 渲染的，里面的日期/时刻也必须打码
      const textLeak = await page.evaluate(`(() => {
        const text = document.body.innerText
        return {
          date: (text.match(/\\d{4}-\\d{2}-\\d{2}/g) || []).slice(0, 3),
          time: (text.match(/\\b\\d{1,2}:\\d{2}\\b/g) || []).slice(0, 3),
        }
      })()`)
      if (textLeak.date.length || textLeak.time.length) {
        throw new Error(`隐藏生辰后右栏长文仍残留出生日期/时刻：${textLeak.date.join(',')} ${textLeak.time.join(',')}`)
      }
      await page.screenshot('desktop-1440-result-masked')
      await clickButton(page, '显示生辰')
      await page.waitFor(`!document.body.innerText.includes('生辰已隐藏')`, { label: '恢复显示生辰' })

      // 修改生辰 / 重新起盘 回到起盘页
      await clickLink(page, '修改生辰')
      await page.waitFor(`location.pathname === '/chart/bazi'`, { timeout: 10000, label: '修改生辰回到起盘页' })
      const backPath = await page.evaluate(`location.pathname`)
      await page.goto(`${base}/result?id=${encodeURIComponent('smoke-accept-bazi')}`)
      await clickLink(page, '重新起盘')
      await page.waitFor(`location.pathname === '/chart/bazi'`, { timeout: 10000, label: '重新起盘回到起盘页' })
      await page.setViewport(VIEWPORT.width, VIEWPORT.height)
      return `左栏 sticky ${layout.width}px / 可滚到底 ${scrolled.max}px；AI 未配 key 有友好提示无报错；隐藏生辰与修改/重新起盘均正常（回 ${backPath}）`
    })

    // 18. 手机 390 结果页：盘面展开/收起 + TabBar 不遮挡
    await run('18. 结果页手机 390：盘面可展开/收起，TabBar 不遮挡内容', async () => {
      await page.setViewport(390, 844)
      await seedResult(
        page,
        { base, api },
        {
          system: 'kongming',
          id: 'smoke-accept-kongming-mobile',
          title: '孔明神卦',
          birth: {
            calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
          },
          options: { characters: '佑咱统', question: '这次换工作能否顺利？' },
        },
      )
      await noOverflow(page, '390 孔明结果页')
      const shell = await page.evaluate(SHELL_STATE)
      if (!shell.appHeader || !shell.tabBar) throw new Error(`390 壳层不符：${shellLabel(shell)}`)

      const toggle = await page.waitFor(
        `(() => {
          const btn = document.querySelector('[data-board-toggle]')
          if (!btn) return null
          return { expanded: btn.getAttribute('aria-expanded'), label: (btn.innerText || '').trim() }
        })()`,
        { timeout: 10000, label: '盘面展开/收起按钮' },
      )
      const closedLabel = toggle.label
      await clickChartToggle(page)
      const opened = await page.waitFor(
        `(() => {
          const btn = document.querySelector('[data-board-toggle]')
          if (!btn) return null
          if (btn.getAttribute('aria-expanded') === ${jsonLiteral(toggle.expanded)}) return null
          return { expanded: btn.getAttribute('aria-expanded'), label: (btn.innerText || '').trim() }
        })()`,
        { timeout: 8000, label: '盘面展开' },
      )
      if (opened.label === closedLabel) throw new Error('展开后按钮文案没变成「收起盘面」')
      await page.screenshot('mobile-390-result-board-open')
      await clickChartToggle(page)
      await page.waitFor(
        `document.querySelector('[data-board-toggle]').getAttribute('aria-expanded') === ${jsonLiteral(toggle.expanded)}`,
        { label: '盘面收起' },
      )
      await noOverflow(page, '390 孔明结果页（收起态）')

      // TabBar 不遮挡：滚到底后最后一块内容必须在 TabBar 上沿之上
      const cover = await page.evaluate(`(() => {
        window.scrollTo(0, document.documentElement.scrollHeight)
        const tabBar = [...document.querySelectorAll('nav')].find((n) => !n.getAttribute('aria-label'))
        const main = document.querySelector('main')
        if (!tabBar || !main) return null
        const barTop = tabBar.getBoundingClientRect().top
        const kids = [...main.querySelectorAll('section, article, aside, footer')]
          .filter((el) => el.getBoundingClientRect().height > 0)
        const last = kids[kids.length - 1]
        return {
          barTop: Math.round(barTop),
          lastBottom: last ? Math.round(last.getBoundingClientRect().bottom) : null,
          paddingBottom: Math.round(parseFloat(getComputedStyle(main).paddingBottom) || 0),
          barHeight: Math.round(tabBar.getBoundingClientRect().height),
        }
      })()`)
      if (!cover) throw new Error('手机上找不到 TabBar 或 main')
      if (cover.paddingBottom < cover.barHeight) {
        throw new Error(`main 底部留白 ${cover.paddingBottom}px < TabBar 高度 ${cover.barHeight}px，最后内容可能被遮挡`)
      }
      if (cover.lastBottom != null && cover.lastBottom > cover.barTop + 2) {
        throw new Error(`滚到底后最后一块内容压到 TabBar 下：bottom=${cover.lastBottom} > barTop=${cover.barTop}`)
      }
      await page.screenshot('mobile-390-result-bottom')
      return `盘面「${closedLabel}」↔「${opened.label}」切换正常；main padding-bottom ${cover.paddingBottom}px ≥ TabBar ${cover.barHeight}px`
    })

    // 19. 主题：深色默认 + 浅色持久化 + 浅色对比度
    await run('19. 主题：深色默认、切浅色刷新保持、浅色下对比度达标', async () => {
      await page.goto(`${base}/`)
      const initial = await page.evaluate(`({
        theme: document.documentElement.dataset.theme || null,
        injected: !!document.querySelector('style[data-theme-injected]'),
      })`)
      if (initial.theme !== null) throw new Error(`默认应无 data-theme（深色），实际 ${initial.theme}`)
      const darkBg = await page.evaluate(`getComputedStyle(document.documentElement).backgroundColor`)
      await clickVisibleByAria(page, '切换到亮色主题')
      const light = await page.evaluate(`({
        theme: document.documentElement.dataset.theme || null,
        bg: getComputedStyle(document.documentElement).backgroundColor,
        lang: document.documentElement.lang,
      })`)
      if (light.theme !== 'light') throw new Error(`切浅色后 data-theme 应为 light，实际 ${light.theme}`)
      if (light.bg === darkBg) throw new Error(`切浅色后 body 背景未变（仍是 ${light.bg}）`)
      await page.screenshot('theme-light-home')

      await page.goto(`${base}/`)
      const persisted = await page.evaluate(`document.documentElement.dataset.theme || null`)
      if (persisted !== 'light') throw new Error(`刷新后浅色未保持，实际 ${persisted}`)

      const contrast = await page.evaluate(CONTRAST_PROBE)
      const weak = contrast.filter((item) => item.ratio < item.threshold)
      if (weak.length) {
        throw new Error(
          `浅色对比度不足：${weak.map((w) => `${w.label} ${w.ratio}:1（需 ≥${w.threshold}，色值 ${w.color}）`).join('；')}`,
        )
      }
      await page.goto(`${base}/settings`)
      const settingsContrast = await page.evaluate(CONTRAST_PROBE)
      const weakSettings = settingsContrast.filter((item) => item.ratio < item.threshold)
      if (weakSettings.length) {
        throw new Error(
          `设置页浅色对比度不足：${weakSettings.map((w) => `${w.label} ${w.ratio}:1`).join('；')}`,
        )
      }
      await page.screenshot('theme-light-settings')

      // 浅色结果页也要可读
      await seedResult(
        page,
        { base, api },
        {
          system: 'bazi',
          id: 'smoke-theme-light-bazi',
          title: '四柱八字',
          birth: {
            calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
            place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
          },
        },
      )
      const lightResult = await page.evaluate(`document.documentElement.dataset.theme || null`)
      if (lightResult !== 'light') throw new Error(`结果页没有沿用浅色：${lightResult}`)
      const resultContrast = await page.evaluate(CONTRAST_PROBE)
      const weakResult = resultContrast.filter((item) => item.ratio < item.threshold)
      if (weakResult.length) {
        throw new Error(`结果页浅色对比度不足：${weakResult.map((w) => `${w.label} ${w.ratio}:1`).join('；')}`)
      }
      await page.screenshot('theme-light-result-bazi')

      // 切回深色，别影响后续用例
      await page.goto(`${base}/`)
      await clickVisibleByAria(page, '切换到暗色主题')
      await page.waitFor(`!document.documentElement.dataset.theme`, { label: '切回深色' })
      const backToDark = await page.evaluate(`document.documentElement.dataset.theme || 'dark'`)
      return `深色默认 → 浅色 ${light.theme}（bg ${light.bg}）刷新保持 → 对比度最低 ${Math.min(...contrast.map((c) => c.ratio))}:1 → 已切回 ${backToDark}（含设置页）`
    })

    // 20. 英文矩阵：体系名/表单/MBTI 走英文，且不残留中文 UI 文案
    await run('20. 英文矩阵：首页英文名来自后端、表单/题干英文、无中文 UI 残留、刷新保持', async () => {
      const systems = await (await fetch(`${api}/api/v1/systems`)).json()
      await page.setViewport(1440, 900)
      await page.goto(`${base}/`)
      await clickVisibleButton(page, 'EN')
      const firstEn = await page.evaluate(`({
        lang: document.documentElement.lang,
        text: document.body.innerText,
      })`)
      if (!firstEn.lang.startsWith('en')) throw new Error(`切 EN 后 html lang 应为 en，实际 ${firstEn.lang}`)
      await page.waitFor(`document.body.innerText.includes(${jsonLiteral(systems[0].name_en)})`, {
        timeout: 10000,
        label: '首页出现英文体系名',
      })
      const homeText = await page.evaluate(`document.body.innerText`)
      const missingEn = systems.filter((s) => !homeText.includes(s.name_en))
      if (missingEn.length) {
        throw new Error(`首页缺英文名：${missingEn.map((s) => `${s.id}=${s.name_en}`).join('、')}`)
      }
      const leakedZh = systems.filter((s) => homeText.includes(s.name))
      if (leakedZh.length) {
        throw new Error(`英文首页仍出现中文体系名：${leakedZh.map((s) => s.name).join('、')}`)
      }
      // tagline 用后端英文，抽查 3 个（换行差异用前 18 字比对）
      const taglineMiss = systems
        .filter((s) => s.tagline_en)
        .filter((s) => !homeText.replace(/\s+/g, ' ').includes(s.tagline_en.slice(0, 18).replace(/\s+/g, ' ')))
      if (taglineMiss.length) {
        throw new Error(`首页英文 tagline 未来自后端：${taglineMiss.map((s) => s.id).join('、')}`)
      }
      await page.screenshot('en-1440-home')

      // 刷新保持 EN
      await page.goto(`${base}/`)
      const afterReload = await page.evaluate(`({ lang: document.documentElement.lang, hasZhTitle: document.body.innerText.includes('可核对的盘面') })`)
      if (!afterReload.lang.startsWith('en') || afterReload.hasZhTitle) {
        throw new Error(`刷新后英文未保持：lang=${afterReload.lang} 中文标题=${afterReload.hasZhTitle}`)
      }

      // 起盘页按钮英文
      await page.goto(`${base}/chart/bazi_hepan`)
      const btnText = await page.waitFor(
        `(() => { const b = document.querySelector('form button[type="submit"]'); return b ? (b.innerText || '').trim() : null })()`,
        { timeout: 10000, label: '合盘起盘按钮' },
      )
      if (btnText.includes('开始') || !/start/i.test(btnText)) {
        throw new Error(`英文态起盘按钮仍是中文/不是英文：${btnText}`)
      }
      await page.screenshot('en-1440-chart-bazi-hepan')

      // 孔明 / 梅花：placeholder 与 hint 英文
      await page.goto(`${base}/chart/kongming`)
      const kongming = await page.evaluate(`(() => {
        const chars = document.querySelector('input[aria-label]')
        const fields = [...document.querySelectorAll('[aria-label]')].map((el) => ({
          label: el.getAttribute('aria-label'),
          placeholder: el.getAttribute('placeholder') || '',
        }))
        return { fields, text: document.body.innerText }
      })()`)
      const zhLabels = kongming.fields.filter((f) => /[\u4e00-\u9fa5]/.test(f.label))
      if (zhLabels.length) throw new Error(`孔明英文态字段 aria-label 仍是中文：${zhLabels.map((f) => f.label).join('、')}`)
      if (!kongming.text.includes('Chinese characters')) {
        throw new Error('孔明英文态 hint 未显示英文（期望含 “Chinese characters”）')
      }
      await page.screenshot('en-1440-chart-kongming')
      await page.goto(`${base}/chart/meihua`)
      const meihuaHints = await page.evaluate(`document.body.innerText`)
      if (/时间起卦|数字起卦|两个数字/.test(meihuaHints)) {
        throw new Error('梅花英文态仍出现中文选项/字段文案')
      }
      await page.screenshot('en-1440-chart-meihua')

      // MBTI：题干与五级量表英文
      await page.goto(`${base}/chart/mbti`)
      const mbti = await page.waitFor(
        `(() => {
          const radios = [...document.querySelectorAll('[role="radio"]')].map((el) => (el.innerText || '').trim())
          const text = document.body.innerText
          const question = (text.match(/第\\s*\\d+\\s*\\/\\s*\\d+\\s*题/) || [''])[0]
          return { radios, hasZhQuestionIndex: !!question }
        })()`,
        { timeout: 10000, label: 'MBTI 答题页' },
      )
      const zhRadios = mbti.radios.filter((r) => /[\u4e00-\u9fa5]/.test(r))
      if (zhRadios.length) throw new Error(`MBTI 英文态量表标签仍是中文：${zhRadios.join('、')}`)
      const mbtiText = await page.evaluate(`document.body.innerText`)
      if (/完全没有|倾向于|比较同意/.test(mbtiText)) throw new Error('MBTI 英文态仍有中文量表文案')
      const firstQuestionEn = await page.evaluate(`(() => {
        const el = [...document.querySelectorAll('p, h2, h3')].map((n) => (n.innerText || '').trim())
          .find((t) => /^[A-Z][A-Za-z ,.'-]{20,}[.?]$/.test(t))
        return el || null
      })()`)
      if (!firstQuestionEn) throw new Error('MBTI 英文态没找到英文题干')
      await page.screenshot('en-1440-chart-mbti')

      // 英文结果页/历史/设置：关键中文 UI 文案不应残留
      await seedResult(
        page,
        { base, api },
        {
          system: 'bazi',
          id: 'smoke-accept-bazi-en',
          // 模拟在中文态创建、切到英文后回看的历史记录
          title: '四柱八字',
          birth: {
            calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
            place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
          },
        },
      )
      const resultText = await page.evaluate(`document.body.innerText`)
      const leaks = ['命盘分析', 'AI 对话', '隐藏生辰', '修改生辰', '重新起盘', '生辰已隐藏'].filter((w) =>
        resultText.includes(w),
      )
      if (leaks.length) throw new Error(`英文结果页仍有中文 UI 文案：${leaks.join('、')}`)
      for (const want of ['Chart analysis', 'AI chat', 'Hide birth date']) {
        if (!resultText.includes(want)) throw new Error(`英文结果页缺少「${want}」`)
      }
      const resultHeading = await page.evaluate(`(() => {
        const h = document.querySelector('.result-grid h2')
        return h ? (h.innerText || '').trim() : ''
      })()`)
      if (resultHeading !== 'Four Pillars (Bazi)') {
        throw new Error(`英文态历史记录的结果页标题未本地化：「${resultHeading}」`)
      }
      await page.screenshot('en-1440-result-bazi')

      await page.goto(`${base}/history`)
      const historyText = await page.evaluate(`document.body.innerText`)
      if (historyText.includes('排盘记录')) throw new Error('英文历史页标题仍是「排盘记录」')
      if (!historyText.includes('Chart history')) throw new Error('英文历史页缺「Chart history」')
      await page.screenshot('en-1440-history')

      await page.goto(`${base}/settings`)
      const settingsText = await page.evaluate(`document.body.innerText`)
      if (settingsText.includes('设置') && !settingsText.includes('Settings')) {
        throw new Error('英文设置页仍是中文')
      }
      if (!/Settings/.test(settingsText)) throw new Error('英文设置页缺「Settings」')
      await page.screenshot('en-1440-settings')

      // 切回中文，保持套件结净
      await clickVisibleButton(page, '中')
      const backZh = await page.evaluate(`({ lang: document.documentElement.lang, hasZh: document.body.innerText.includes('设置') || document.body.innerText.includes('排盘') })`)
      if (!backZh.lang.startsWith('zh')) throw new Error(`切回中文失败，lang=${backZh.lang}`)
      if (!backZh.hasZh) throw new Error('切回中文后页面仍是英文')
      await page.setViewport(VIEWPORT.width, VIEWPORT.height)
      return `EN 首页 11 个英文名/ tagline 均与后端一致且无中文体系名；合盘按钮「${btnText}」；孔明/梅花英文 placeholder+hint；MBTI 首题「${firstQuestionEn.slice(0, 42)}…」；结果/历史/设置无中文 UI 残留；刷新保持、可切回中文`
    })

    // 21. 桌面 1440 全体系结果页：左栏 / 摘要 / 打码按钮按体系出现
    await run('21. 桌面 1440 全 11 体系结果页：无横向溢出 + 左栏 sticky + 盘面摘要 + 打码按钮按体系出现', async () => {
      const birth = {
        calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
        place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
      }
      const secondary = {
        calendar: 'solar', year: 1992, month: 8, day: 3, hour: 9, minute: 0, gender: 'female',
        place: { name: '上海市', longitude: 121.4737, latitude: 31.2304, timezone: 8 },
      }
      const cases = [
        { system: 'bazi', title: '四柱八字', birth, birthInput: true },
        { system: 'ziwei', title: '紫微斗数', birth, birthInput: true },
        { system: 'astrology', title: '西方占星', birth, birthInput: true },
        { system: 'qimen', title: '奇门终身局', birth, birthInput: true },
        { system: 'bazi_hepan', title: '八字合盘', birth, secondary, birthInput: true },
        { system: 'ziwei_hepan', title: '紫微合盘', birth, secondary, birthInput: true },
        { system: 'liuyao', title: '六爻纳甲', options: { question: '这次能否成？' } },
        { system: 'tarot', title: '塔罗牌', options: {} },
        { system: 'meihua', title: '梅花易数', options: {} },
        { system: 'kongming', title: '孔明神卦', options: { characters: '佑咱统', question: '这次换工作能否顺利？' } },
        { system: 'mbti', title: 'MBTI 测试', options: { answers: Array(32).fill(3) } },
      ]
      const seen = []
      for (const item of cases) {
        await page.setViewport(1440, 900)
        await seedResult(page, { base, api }, {
          system: item.system,
          id: `smoke-desk-${item.system}`,
          title: item.title,
          birth: item.birth,
          secondary: item.secondary,
          options: item.options ?? {},
        })
        await noOverflow(page, `1440 ${item.system} 结果页`)
        const info = await page.evaluate(`(() => {
          const aside = document.querySelector('aside')
          const style = aside ? getComputedStyle(aside) : null
          const rect = aside ? aside.getBoundingClientRect() : null
          const h2 = document.querySelector('.result-grid h2')
          const summary = h2 && h2.nextElementSibling && h2.nextElementSibling.tagName === 'P'
            ? (h2.nextElementSibling.innerText || '').trim() : ''
          return {
            sticky: style ? style.position : null,
            width: rect ? Math.round(rect.width) : 0,
            summary,
            hasMask: document.body.innerText.includes('隐藏生辰'),
            hasModify: document.body.innerText.includes('修改生辰') || document.body.innerText.includes('修改信息'),
          }
        })()`)
        if (info.sticky !== 'sticky') throw new Error(`${item.system}：桌面左栏不是 sticky（${info.sticky}）`)
        if (Math.abs(info.width - 380) > 2) throw new Error(`${item.system}：左栏宽度应 380，实际 ${info.width}`)
        if (!info.summary || info.summary.length < 4) throw new Error(`${item.system}：标题下没有盘面摘要`)
        if (item.birthInput && !info.hasMask) throw new Error(`${item.system}：吃生辰的体系应出现「隐藏生辰」`)
        if (!item.birthInput && info.hasMask) throw new Error(`${item.system}：不吃生辰却出现「隐藏生辰」`)
        if (!info.hasModify) throw new Error(`${item.system}：缺少「修改生辰/修改信息」入口`)
        await page.screenshot(`desktop-1440-all-${item.system}`)
        if (item.system === 'ziwei') {
          // 点宫位应高亮三方四正（4 宫）并展开详情
          await page.evaluate(`(() => { const c = document.querySelector('[role="gridcell"]'); c && c.click() })()`)
          const trine = await page.waitFor(
            `(() => {
              const detail = document.querySelector('[data-ziwei-detail="on"]')
              const related = document.querySelectorAll('[role="gridcell"][data-related="true"]').length
              return detail && related === 4
                ? { related, hasText: (detail.innerText || '').includes('三方四正') }
                : null
            })()`,
            { timeout: 8000, label: '紫微三方四正高亮' },
          )
          if (!trine.hasText) throw new Error('紫微宫位详情没有「三方四正」一行')
          await page.screenshot('desktop-1440-ziwei-trine')
        }
        seen.push(`${item.system}「${info.summary.slice(0, 18)}${info.summary.length > 18 ? '…' : ''}」`)
      }
      // 1024：桌面下沿仍为两栏 + sticky
      await page.setViewport(1024, 768)
      await seedResult(page, { base, api }, { system: 'bazi', id: 'smoke-1024-bazi', title: '四柱八字', birth })
      await noOverflow(page, '1024 八字结果页')
      const mid = await page.evaluate(`(() => {
        const aside = document.querySelector('aside')
        const style = aside ? getComputedStyle(aside) : null
        return { position: style ? style.position : null, width: aside ? Math.round(aside.getBoundingClientRect().width) : 0 }
      })()`)
      if (mid.position !== 'sticky') throw new Error(`1024 下左栏应 sticky，实际 ${mid.position}`)
      await page.screenshot('desktop-1024-result-bazi')

      // 768 平板：单列，左栏不再 sticky
      await page.setViewport(768, 1024)
      await seedResult(page, { base, api }, { system: 'bazi', id: 'smoke-tablet-bazi', title: '四柱八字', birth })
      await noOverflow(page, '768 八字结果页')
      const tablet = await page.evaluate(`(() => {
        const aside = document.querySelector('aside')
        const style = aside ? getComputedStyle(aside) : null
        return { position: style ? style.position : null, width: aside ? Math.round(aside.getBoundingClientRect().width) : 0 }
      })()`)
      if (tablet.position === 'sticky') throw new Error('768 下左栏不应 sticky')
      await page.screenshot('tablet-768-result-bazi')

      await page.setViewport(VIEWPORT.width, VIEWPORT.height)
      return `11 个体系桌面结果页均无溢出、左栏 380 sticky、摘要非空；打码按钮只出现在生辰体系；768 单列非 sticky；${seen.join('；')}`
    })

    // 22. 设置页：AI 接口 / 模型 / 密钥的保存、掩码与清除
    await run('22. 设置页：AI 接口/模型/密钥可保存、只回显尾号、可清除', async () => {
      // 会 DELETE/PUT /settings/llm：只允许在隔离配置（临时库 / 临时 LLM 配置文件）下执行
      if (!process.env.SMOKE_DB && !process.env.SM_LLM_CONFIG_PATH) {
        return SKIP('AI 配置未隔离，为避免清掉真实密钥已跳过；跑 bash scripts/smoke-isolated.sh 可执行本用例')
      }
      const reset = () => fetch(`${api}/api/v1/settings/llm`, { method: 'DELETE' })
      await reset()
      try {
        await page.setViewport(1440, 1000)
        await page.goto(`${base}/settings`)
        await page.waitFor(`document.querySelector('[data-llm-settings]')`, { label: '设置页 AI 表单' })
        const initial = await page.evaluate(`(() => {
          const box = document.querySelector('[data-llm-settings]')
          return {
            status: (document.querySelector('[data-llm-status]')?.innerText || '').trim(),
            url: box.querySelector('input[type=url]')?.value || '',
            model: box.querySelector('input[type=text]')?.value || '',
            keyType: box.querySelector('input[type=password]')?.type || '',
          }
        })()`)
        if (!initial.status.includes('未配置')) throw new Error(`初始状态应未配置：${initial.status}`)
        if (!initial.url.startsWith('http')) throw new Error(`接口地址未回填：${initial.url}`)
        if (!initial.model) throw new Error('模型名未回填')
        if (initial.keyType !== 'password') throw new Error('密钥输入框不是 password 类型')

        await page.evaluate(`(() => {
          const box = document.querySelector('[data-llm-settings]')
          const set = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })) }
          set(box.querySelector('input[type=url]'), 'http://127.0.0.1:9999/v1')
          set(box.querySelector('input[type=text]'), 'smoke-model')
          set(box.querySelector('input[type=password]'), 'sk-smoke-1234')
        })()`)
        await page.evaluate(`(() => {
          const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '保存设置')
          b && b.click()
        })()`)
        const saved = await page.waitFor(
          `(() => {
            const status = (document.querySelector('[data-llm-status]')?.innerText || '').trim()
            return status.includes('已配置')
              ? {
                  status,
                  hint: document.body.innerText.includes('••••1234'),
                  leaked: document.body.innerHTML.includes('sk-smoke-1234'),
                }
              : null
          })()`,
          { timeout: 10000, label: '保存 AI 设置' },
        )
        if (!saved.hint) throw new Error('保存后没有显示密钥尾号')
        if (saved.leaked) throw new Error('密钥明文出现在页面 HTML 中')
        const info = await page.evaluate(`fetch('/api/v1/settings/llm').then((r) => r.json())`)
        if (!info.configured || info.key_hint !== '••••1234' || 'api_key' in info) {
          throw new Error(`接口回显不符合预期：${JSON.stringify(info)}`)
        }
        await page.screenshot('settings-ai-configured')

        await page.evaluate(`(() => {
          const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '清除密钥')
          b && b.click()
        })()`)
        await page.waitFor(
          `(document.querySelector('[data-llm-status]')?.innerText || '').includes('未配置')`,
          { timeout: 10000, label: '清除密钥' },
        )
        const cleared = await page.evaluate(`fetch('/api/v1/settings/llm').then((r) => r.json())`)
        if (cleared.configured) throw new Error('清除后接口仍显示已配置')
        return '保存后只回显 ••••1234、页面无明文密钥；清除后回到未配置，接口地址与模型保留'
      } finally {
        await reset()
      }
    })

    // ---------------------------------------------------------------------
    // 23–26：AI 解读持久化 / 方向全选 / 手动画坐标 / 国外城市
    // ---------------------------------------------------------------------

    /** 结果页切到「AI 对话」并等面板出现 */
    async function openAiTab() {
      await page.waitFor(`[...document.querySelectorAll('button')].some((b) => b.innerText.trim() === 'AI 对话')`, {
        label: '结果页出现「AI 对话」Tab',
      })
      await clickButton(page, 'AI 对话')
      return page.waitFor(`!!document.querySelector('[data-ai-panel]')`, { label: 'AI 面板出现' })
    }

    const SEED_BAZI_BIRTH = {
      calendar: 'solar', year: 1990, month: 5, day: 15, hour: 14, minute: 30, gender: 'male',
      place: { name: '北京市', longitude: 116.4074, latitude: 39.9042, timezone: 8 },
    }

    await run('23. AI 解读方向：一键全选 / 取消全选（DOM aria-pressed 状态）', async () => {
      await page.setViewport(1440, 900)
      await seedResult(page, { base, api }, { system: 'bazi', id: 'smoke-focus-all', birth: SEED_BAZI_BIRTH })
      await openAiTab()
      const before = await page.waitFor(
        `(() => {
          const chips = [...document.querySelectorAll('[data-focus-id]')]
          if (!chips.length) return null
          return {
            total: chips.length,
            on: chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset.focusId),
            text: document.body.innerText,
          }
        })()`,
        { label: '方向 chip 出现' },
      )
      const state = () =>
        page.evaluate(`(() => {
          const chips = [...document.querySelectorAll('[data-focus-id]')]
          const btn = [...document.querySelectorAll('button')].find((b) => ['全选', '取消全选'].includes(b.innerText.trim()))
          return {
            total: chips.length,
            pressed: chips.map((c) => c.getAttribute('aria-pressed') === 'true'),
            btn: btn ? btn.innerText.trim() : '',
            selected: (document.body.innerText.match(/已选 (\\d+) 个方向/) || [])[1] || '',
          }
        })()`)

      if (before.on.length !== 1 || before.on[0] !== 'overview') {
        throw new Error(`默认应只选 overview，实际 [${before.on.join(',')}]`)
      }
      if (!before.text.includes('全选')) throw new Error('未全选时按钮文案应为「全选」')
      await clickButton(page, '全选')
      const all = await state()
      if (!all.pressed.every(Boolean)) throw new Error(`全选后仍有未选中 chip：${all.pressed.join(',')}`)
      if (all.selected !== String(all.total)) throw new Error(`全选后已选数应 ${all.total}，显示「${all.selected}」`)
      if (all.btn !== '取消全选') throw new Error(`全选后按钮文案应「取消全选」，实际「${all.btn}」`)
      await page.screenshot('ai-focus-all')

      await clickButton(page, '取消全选')
      const none = await state()
      if (none.pressed.some(Boolean)) throw new Error('取消全选后仍有 chip 选中')
      if (none.btn !== '全选') throw new Error(`取消全选后按钮文案应「全选」，实际「${none.btn}」`)
      return `chip ${before.total} 个：默认 overview → 全选 ${all.selected}/${all.total}（按钮「${all.btn}」）→ 取消后 0 个（按钮「${none.btn}」）`
    })

    await run('24. AI 解读按记录持久化：存档恢复 + 已保存标识 + 换记录不串内容', async () => {
      const A = 'smoke-persist-a'
      const B = 'smoke-persist-b'
      const MARK = 'PERSIST-CHECK-42'
      try {
        await seedResult(page, { base, api }, { system: 'bazi', id: A, birth: SEED_BAZI_BIRTH })
        await seedResult(page, { base, api }, { system: 'bazi', id: B, birth: SEED_BAZI_BIRTH })
        await page.goto(`${base}/result?id=${A}`)
        // 先确认 A 自己没存档时是空的
        await openAiTab()
        if (await page.evaluate(`!!document.querySelector('[data-ai-output]')`)) {
          throw new Error('没有存档时不应显示解读输出')
        }

        // 存档由服务端按 recordId 存；直接走接口写入（不依赖 LLM）
        const seed = async (id) => {
          const res = await fetch(`${api}/api/v1/records/${id}/reading`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Cookie: session.cookie },
            body: JSON.stringify({
              text: '# 存档标题\n\n' + MARK,
              focus: ['overview', 'career'],
              style: 'detailed',
              question: '存档用问题',
              system: 'bazi',
            }),
          })
          if (!res.ok) throw new Error(`写入存档失败：HTTP ${res.status} ${await res.text()}`)
        }
        await seed(A)
        await page.goto(`${base}/result?id=${A}`)
        await openAiTab()
        const shown = await page.waitFor(
          `(() => {
            const out = document.querySelector('[data-ai-output]')
            if (!out) return null
            const chips = [...document.querySelectorAll('[data-focus-id]')]
            const detail = [...document.querySelectorAll('button')].find((b) => b.innerText.trim() === '详细')
            return {
              text: out.innerText,
              chips: chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset.focusId),
              saved: document.body.innerText.includes('已保存'),
              detailed: detail ? detail.getAttribute('aria-pressed') : null,
            }
          })()`,
          { label: 'A 记录恢复存档输出' },
        )
        if (!shown.text.includes(MARK)) throw new Error(`输出未恢复存档文本`)
        if (!shown.saved) throw new Error('恢复后缺少「已保存」标识')
        if (shown.chips.join(',') !== 'overview,career') throw new Error(`方向未恢复：${shown.chips.join(',')}`)
        if (shown.detailed !== 'true') throw new Error('详略未恢复为「详细」')
        await page.screenshot('ai-persisted')

        // 切到 B：不能串
        await page.goto(`${base}/result?id=${B}`)
        await openAiTab()
        const switched = await page.evaluate(
          `(() => {
            const out = document.querySelector('[data-ai-output]')
            const chips = [...document.querySelectorAll('[data-focus-id]')]
            return {
              hasOut: !!out,
              leaked: (out ? out.innerText : '').includes(${jsonLiteral(MARK)}),
              chips: chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset.focusId),
            }
          })()`,
        )
        if (switched.hasOut || switched.leaked) throw new Error('切到记录 B 后仍显示 A 的解读（串内容）')
        if (switched.chips.join(',') !== 'overview') throw new Error(`B 应回到默认 overview，实际 ${switched.chips.join(',')}`)
        // 同路由切回 A 也要恢复
        await page.goto(`${base}/result?id=${A}`)
        await openAiTab()
        await page.waitFor(
          `(document.querySelector('[data-ai-output]')?.innerText || '').includes(${jsonLiteral(MARK)})`,
          { label: '切回 A 恢复存档' },
        )
        return `${MARK} 恢复成功；方向/详略跟随存档；「已保存」可见；切到 B 无输出、overview 默认；切回 A 再次恢复`
      } finally {
        // 清掉测试注入的存档（记录本身留在临时库里）
        for (const id of [A, B]) {
          await fetch(`${api}/api/v1/records/${id}/reading`, { method: 'DELETE', headers: { Cookie: session.cookie } })
        }
      }
    })

    await run('25. 出生地手动经纬度：东京 → 结果页出现坐标与 UTC+9；经纬度越界就地报错', async () => {
      await page.setViewport(390, 844)
      await page.goto(`${base}/chart/bazi`)
      await page.waitFor(`!!document.querySelector('input[aria-label="出生地"]')`, { label: '出生地输入框' })
      await clickButton(page, '手动输入坐标')
      const manualFields = ['经度', '纬度', 'UTC 时区', '名称（选填）']
      for (const focusLabel of manualFields) {
        await page.waitFor(`!!document.querySelector('input[aria-label=${jsonLiteral(focusLabel)}]')`, {
          label: `手动坐标字段「${focusLabel}」`,
        })
      }

      // 越界：经度 200 必须就地报错且不能确认
      await page.evaluate(`(() => {
        const box = document.querySelector('input[aria-label="经度"]')
        box.value = '200'
        box.dispatchEvent(new Event('input', { bubbles: true }))
        const lat = document.querySelector('input[aria-label="纬度"]')
        lat.value = '35.69'
        lat.dispatchEvent(new Event('input', { bubbles: true }))
      })()`)
      await clickButton(page, '使用这组坐标')
      const invalid = await page.evaluate(`(() => {
        const lon = document.querySelector('input[aria-label="经度"]')
        return {
          stillOpen: !!lon,
          invalid: lon ? lon.getAttribute('aria-invalid') : null,
          text: document.body.innerText,
          coordLine: document.querySelector('[data-manual-place]')?.innerText || '',
        }
      })()`)
      if (!invalid.stillOpen) throw new Error('经度 200 时手动坐标面板被关闭了（不应确认）')
      if (invalid.invalid !== 'true') throw new Error(`经度输入框未标记 aria-invalid，实际 ${invalid.invalid}`)
      if (!invalid.text.includes('经度需在 -180 到 180 之间')) throw new Error('缺少越界错误提示')
      if (invalid.coordLine) throw new Error(`越界时不应写入坐标，实际「${invalid.coordLine}」`)

      // 正确值：东京
      const fill = { 经度: '139.692', 纬度: '35.69', 'UTC 时区': '9', '名称（选填）': 'Tokyo' }
      for (const [labelText, value] of Object.entries(fill)) {
        await setControl(page, `input[aria-label=${jsonLiteral(labelText)}]`, value)
      }
      await clickButton(page, '使用这组坐标')
      const line = await page.waitFor(
        `(() => {
          const el = document.querySelector('[data-manual-place]')
          return el ? { text: el.innerText, input: document.querySelector('input[aria-label="出生地"]')?.value } : null
        })()`,
        { label: '坐标行出现' },
      )
      if (!line.text.includes('139.692') || !line.text.includes('35.690') || !line.text.includes('UTC+9')) {
        throw new Error(`坐标行不符：「${line.text}」`)
      }
      if (line.input !== 'Tokyo') throw new Error(`名称未写入查询框：「${line.input}」`)
      await submitAndWaitResult(page, '坐标起盘')
      const result = await page.waitFor(
        `(() => {
          const text = document.body.innerText
          return text.includes('139.692') && text.includes('UTC+9') ? text : null
        })()`,
        { timeout: 20000, label: '结果页出现经纬度与 UTC+9' },
      )
      await page.waitFor(FOUND_PILLARS, { label: '坐标起盘后读到四柱' })
      if (!result.includes('Tokyo')) throw new Error('结果页出生地未显示名称 Tokyo')
      await page.screenshot('manual-place-result')
      return `越界 200 → aria-invalid +「经度需在 -180 到 180 之间」且不确认；东京 139.692/35.69/UTC+9 → 坐标行与结果页均显示 UTC+9，四柱正常`
    })

    await run('26. 国外城市检索：搜索 Tokyo → 东京/日本（139.692、UTC+9）→ 正常起盘', async () => {
      await page.setViewport(390, 844)
      await page.goto(`${base}/chart/bazi`)
      await typePlace(page, 'Tokyo')
      const candidate = await page.waitFor(
        `(() => {
          const btn = [...document.querySelectorAll('ul li button')].find(
            (b) => b.innerText.includes('东京') && b.innerText.includes('日本'),
          )
          if (!btn) return null
          btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
          return btn.innerText.replace(/\\s+/g, ' ').trim()
        })()`,
        { timeout: 10000, label: 'Tokyo 候选「东京 / 日本」' },
      )
      const line = await page.waitFor(
        `(() => {
          const el = document.querySelector('[data-manual-place]')
          return el ? el.innerText : null
        })()`,
        { label: '选中后坐标行' },
      )
      if (!line.includes('139.692') || !line.includes('UTC+9')) throw new Error(`坐标行不符：「${line}」`)
      await submitAndWaitResult(page, 'Tokyo 起盘')
      const found = await page.waitFor(FOUND_PILLARS, { timeout: 20000, label: 'Tokyo 起盘后读到四柱' })
      await noOverflow(page, '390 Tokyo 结果页')
      return `候选「${candidate}」→ ${line.replace(/\\s+/g, ' ')}；结果页四柱 ${found.gans.join('')} / ${found.zhis.join('')}`
    })

    // 27. 账号隔离：A/B 互不可见（仅临时库模式；对真实 8000 明确跳过）
    await run('27. 账号隔离：A/B 两账号的 API 列表与 UI 历史/直链互不可见', async () => {
      if (!process.env.SMOKE_DB) return SKIP('需要临时库：请用 bash scripts/smoke-isolated.sh（或设 SMOKE_DB + 8001/5183）')
      const original = { ...session }
      const stamp = Date.now().toString(36)
      const users = {}
      const apiJson = async (path, cookie) => {
        const res = await fetch(`${api}${path}`, { headers: { Cookie: cookie } })
        const body = await res.json().catch(() => null)
        return { status: res.status, body }
      }
      const idsOf = (list) => (Array.isArray(list) ? list.map((r) => r.id) : [])
      const historyLinks = () =>
        page.evaluate(`(() => {
          if (!location.pathname.startsWith('/history')) return null
          return [...new Set([...document.querySelectorAll('a[href^="/result?id="]')].map((a) => decodeURIComponent(a.getAttribute('href').split('id=')[1])))]
        })()`)
      try {
        for (const name of ['A', 'B']) {
          const username = `smoke_iso_${name.toLowerCase()}_${stamp}`
          const creds = JSON.stringify({ username, password: 'smoke-passw0rd' })
          let res = await fetch(`${api}/api/v1/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: creds,
          })
          for (let i = 0; i < 10 && res.status === 429; i += 1) {
            await sleep(1500)
            res = await fetch(`${api}/api/v1/auth/register`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: creds,
            })
          }
          if (!res.ok) throw new Error(`注册 ${username} 失败：HTTP ${res.status} ${await res.text()}`)
          const user = (await res.json()).user
          users[name] = { username, cookie: res.headers.get('set-cookie').split(';')[0], id: user.id, recordId: null }
        }
        if (users.A.id === users.B.id) throw new Error('A/B 拿到了同一个用户')

        // 2) A 登录 → UI 起八字 → /history 1 条
        await loginCookie(page, base, users.A)
        users.A.recordId = await chartBazi(page, base)
        await page.goto(`${base}/history`)
        await page.waitFor(`!!document.querySelector('a[href^="/result?id="]')`, { label: 'A 的历史里出现记录' })
        const aLinks = await historyLinks()
        if (aLinks.length !== 1 || aLinks[0] !== users.A.recordId) {
          throw new Error(`A /history 应只有自己的 1 条，实际 ${JSON.stringify(aLinks)}`)
        }

        // 3) API 层：A 含、B 不含、B 直查 A 的记录 404
        const aList = await apiJson('/api/v1/records', users.A.cookie)
        const bList = await apiJson('/api/v1/records', users.B.cookie)
        if (aList.status !== 200 || !idsOf(aList.body).includes(users.A.recordId)) {
          throw new Error(`A 的 GET /records 未包含自己的 ${users.A.recordId}（HTTP ${aList.status}）`)
        }
        if (bList.status !== 200 || idsOf(bList.body).includes(users.A.recordId)) {
          throw new Error(`B 的 GET /records 看到了 A 的记录（HTTP ${bList.status}）`)
        }
        const bGetA = await apiJson(`/api/v1/records/${users.A.recordId}`, users.B.cookie)
        if (bGetA.status !== 404 || bGetA.body?.error?.code !== 'record_not_found') {
          throw new Error(`B 直查 A 的记录应 404 record_not_found，实际 ${bGetA.status} ${JSON.stringify(bGetA.body)}`)
        }
        const anonList = await fetch(`${api}/api/v1/records`)
        if (anonList.status !== 401) throw new Error(`未登录 GET /records 应 401，实际 ${anonList.status}`)

        // 4) UI 退出登录 → 未登录 /history 与直链
        await page.goto(`${base}/history`)
        await page.waitFor(`!!document.querySelector('button[aria-label="账号菜单"]')`, { label: '账号菜单' })
        await page.evaluate(`document.querySelector('button[aria-label="账号菜单"]').click()`)
        await clickButton(page, '退出登录')
        await page.waitFor(`document.body.innerText.includes('登录') && !document.querySelector('button[aria-label="账号菜单"]')`, {
          label: '退出后显示登录入口',
        })
        await page.goto(`${base}/history`)
        await page.waitFor(`!!document.querySelector('[data-history-guest]')`, { label: '未登录 /history 提示' })
        const guest = await page.evaluate(`({
          text: document.querySelector('[data-history-guest]').innerText,
          links: [...document.querySelectorAll('a[href^="/result?id="]')].length,
        })`)
        if (!guest.text.includes('登录后才能保存和查看记录')) throw new Error('未登录 /history 缺少登录提示')
        if (guest.links) throw new Error(`未登录 /history 仍出现记录链接 ${guest.links} 条`)
        const logoutCookie = await page.cdp.send('Network.getCookies', { urls: [`${base}/`] }, page.sessionId)
        if ((logoutCookie.cookies || []).some((c) => c.name === 'sm_session')) {
          throw new Error('UI 退出后浏览器仍带着 sm_session Cookie')
        }
        await page.goto(`${base}/result?id=${users.A.recordId}`)
        await page.waitFor(`!!document.querySelector('[data-result-missing]')`, { label: '未登录直链被拒' })
        if (!(await page.evaluate(`document.querySelector('[data-result-missing]').innerText`)).includes('记录不存在或无权查看')) {
          throw new Error('未登录直链 A 记录时缺少「记录不存在或无权查看」')
        }

        // 5) B 登录：历史为空，直链 A 仍空态；B 起一卦后只有自己 1 条
        await loginCookie(page, base, users.B)
        await page.goto(`${base}/history`)
        await page.waitFor(`document.querySelector('[data-history-guest]') === null`, { label: 'B 进入记录页' })
        await page.waitFor(
          `document.body.innerText.includes('还没有排盘记录') || !!document.querySelector('a[href^="/result?id="]')`,
          { label: 'B 记录页渲染完成' },
        )
        const bEmpty = await historyLinks()
        if (bEmpty.length) throw new Error(`B 的 /history 应是空的，实际 ${JSON.stringify(bEmpty)}`)
        await page.goto(`${base}/result?id=${users.A.recordId}`)
        await page.waitFor(`!!document.querySelector('[data-result-missing]')`, { label: 'B 直链 A 记录被拒' })
        if (await page.evaluate(`!!document.querySelector('[data-result-hero]')`)) throw new Error('B 直链 A 记录时泄露了盘面')
        users.B.recordId = await chartBazi(page, base)
        await page.goto(`${base}/history`)
        await page.waitFor(`!!document.querySelector('a[href^="/result?id="]')`, { label: 'B 的历史里出现记录' })
        const bLinks = await historyLinks()
        if (bLinks.length !== 1 || bLinks[0] !== users.B.recordId) {
          throw new Error(`B /history 应只有自己的 1 条，实际 ${JSON.stringify(bLinks)}`)
        }

        // 6) 回到 A：只看到 A 的
        await loginCookie(page, base, users.A)
        await page.goto(`${base}/history`)
        await page.waitFor(`!!document.querySelector('a[href^="/result?id="]')`, { label: 'A 重新进入记录页' })
        const aBack = await historyLinks()
        if (aBack.length !== 1 || aBack[0] !== users.A.recordId) {
          throw new Error(`A 重新登录后 /history 应只有 ${users.A.recordId}，实际 ${JSON.stringify(aBack)}`)
        }
        const aList2 = await apiJson('/api/v1/records', users.A.cookie)
        if (idsOf(aList2.body).includes(users.B.recordId)) throw new Error('A 的 API 记录列表出现了 B 的记录')
        return `A(${users.A.username}) 与 B(${users.B.username})：A 列表含自己 id、B 列表不含，B 直查 A→404 record_not_found，未登录→401；UI 退出后无 sm_session，未登录 /history 提示登录且无链接、直链 A 空态；B 历史空→起卦后 1 条（A 不可见），A 回来只见自己；API 与 UI 双层一致`
      } finally {
        // 7) 清理：删掉 A/B 的记录与解读存档，浏览器退出登录，并把套件账号换回去
        for (const u of Object.values(users)) {
          if (!u.recordId) continue
          await fetch(`${api}/api/v1/records/${u.recordId}/reading`, { method: 'DELETE', headers: { Cookie: u.cookie } })
          await fetch(`${api}/api/v1/records/${u.recordId}`, { method: 'DELETE', headers: { Cookie: u.cookie } })
          await fetch(`${api}/api/v1/auth/logout`, { method: 'POST', headers: { Cookie: u.cookie } })
        }
        await setBrowserSession(page, base, null)
        Object.assign(session, original)
        if (session.cookie) await loginCookie(page, base, { username: session.username })
      }
    })
  } finally {
    cdp?.close()
    proc.kill('SIGTERM')
    await sleep(300)
    try {
      rmSync(profileDir, { recursive: true, force: true })
    } catch {
      /* ignore */
    }
  }

  // 汇总：逐条列表在上方已实时打印，这里只汇总结果
  const failed = results.filter((item) => !item.ok)
  console.log('\n' + '─'.repeat(72))
  if (failed.length) {
    for (const item of failed) console.log(`❌ ${item.name}\n   ↳ ${item.error}`)
    console.log('─'.repeat(72))
  }
  const skipped = results.filter((item) => item.skipped)
  if (skipped.length) {
    // 对真实后端只跑「无预置记录」的部分；全量请用 bash scripts/smoke-isolated.sh
    const reasons = [...new Set(skipped.map((item) => item.detail.replace(/^SKIP：/, '')))]
    for (const [index, reason] of reasons.entries()) console.log(`⚠️  跳过原因 ${index + 1}：${reason}`)
    console.log(`⚠️  跳过 ${skipped.length} 条：${skipped.map((item) => item.name.split('.')[0]).join('、')}`)
    console.log('   全量请跑：bash scripts/smoke-isolated.sh')
  }
  console.log(
    failed.length === 0
      ? `全部 ${results.length} 条用例通过${skipped.length ? `（其中 ${skipped.length} 条因缺临时库跳过）` : ''}。截图：${SHOT_DIR}/smoke-*.png`
      : `${results.length - failed.length}/${results.length} 通过，${failed.length} 失败。截图：${SHOT_DIR}/smoke-*.png`,
  )
  process.exitCode = failed.length === 0 ? 0 : 1
}

function SKIP(reason) {
  const err = new Error(reason)
  err.code = 'skip'
  return err
}

async function run(name, fn) {
  const started = Date.now()
  try {
    const detail = await fn()
    results.push({ name, ok: true, detail })
    console.log(`✅ PASS  ${name}${detail ? `\n          ${detail}` : ''}  (${Date.now() - started}ms)`)
  } catch (err) {
    if (err.code === 'skip') {
      results.push({ name, ok: true, skipped: true, detail: `SKIP：${err.message}` })
      console.log(`⏭️  SKIP  ${name}\n          ${err.message}  (${Date.now() - started}ms)`)
      return
    }
    results.push({ name, ok: false, error: err.message })
    console.log(`❌ FAIL  ${name}\n          ↳ ${err.message}  (${Date.now() - started}ms)`)
    await dumpFailure(name)
  }
}

/** 失败时把页面正文与 URL 落到 /tmp，便于排查。 */
async function dumpFailure(name) {
  const page = ctx.page
  if (!page) return
  try {
    const info = await page.evaluate(`({ url: location.href, text: document.body.innerText })`)
    const safe = name.replace(/[^\w\u4e00-\u9fa5]+/g, '-').slice(0, 40)
    const file = path.join(SHOT_DIR, `smoke-fail-${safe}.txt`)
    writeFileSync(file, `URL: ${info.url}\n\n${info.text}`)
    const brief = (info.text || '').replace(/\n{2,}/g, '\n').trim().slice(0, 300)
    console.log(`          现场：${info.url}\n          ${brief.replace(/\n/g, ' | ')}\n          详见 ${file}`)
  } catch {
    /* ignore */
  }
}

main().catch((err) => {
  console.error(`\n冒烟脚本异常终止：${err.message}`)
  process.exitCode = 1
})
