/** Text color with good contrast on a #rgb / #rrggbb background. */
export function contrastColor(hexColor: string): "#222" | "#fff" {
  let hex = hexColor.replace("#", "")
  if (hex.length === 3) {
    hex = [...hex].map((c) => c + c).join("")
  }
  const r = Number.parseInt(hex.slice(0, 2), 16)
  const g = Number.parseInt(hex.slice(2, 4), 16)
  const b = Number.parseInt(hex.slice(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.45 ? "#222" : "#fff"
}

const URL_PATTERN = /https?:\/\/[^\s<>"'\][{}|\\^`]+/

/** First http(s) URL in text, or null. */
export function findUrl(text: string): string | null {
  return URL_PATTERN.exec(text)?.[0] ?? null
}
