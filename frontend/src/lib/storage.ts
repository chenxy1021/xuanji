export function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

export function saveJSON(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* 隐私模式/配额满时静默降级 */
  }
}

export function removeJSON(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    /* 隐私模式下同样静默 */
  }
}
