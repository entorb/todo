/** Copy plain text to clipboard. */
export async function copyText(text: string): Promise<void> {
  await navigator.clipboard.writeText(text)
}

/** Copy html (with plain text fallback flavor) to clipboard. */
export async function copyHtml(html: string): Promise<void> {
  const item = new ClipboardItem({
    "text/html": new Blob([html], { type: "text/html" }),
    "text/plain": new Blob([html], { type: "text/plain" }),
  })
  await navigator.clipboard.write([item])
}
