/** Normalize API media paths for the Vite `/media` proxy. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (path.startsWith('blob:') || path.startsWith('data:')) return path
  const mediaIdx = path.indexOf('/media/')
  const normalized =
    mediaIdx >= 0 ? path.slice(mediaIdx) : path.startsWith('/') ? path : `/media/${path}`
  // Bust stale browser caches after 404s from a previous backend process.
  const sep = normalized.includes('?') ? '&' : '?'
  const stamp = normalized.replace(/\D/g, '').slice(-12) || String(Date.now())
  return `${normalized}${sep}v=${stamp}`
}
