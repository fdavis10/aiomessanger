/** Apple Color Emoji PNGs via emoji-datasource-apple (same look on Win/Linux/macOS). */

const APPLE_CDN =
  'https://cdn.jsdelivr.net/npm/emoji-datasource-apple@15.1.2/img/apple/64'

/**
 * Prefer glyphs whose Apple sheet key is a single hex code (no FE0F ambiguity).
 * Keys verified against emoji-datasource-apple@15.1.2.
 */
export const AVATAR_EMOJIS = [
  '😀', '😎', '🤩', '🦊', '🐼', '🐯', '🐸', '🐙', '🦄', '🐲',
  '🌈', '🔥', '🌊', '🍀', '🌸', '🍕', '🎧', '🎮', '🚀',
  '💎', '🎯', '🧿', '🪐', '🌙', '🧊', '🎸', '🧠', '👾',
] as const

export function emojiToAppleKey(emoji: string, keepFe0f = false): string {
  const points: string[] = []
  for (const ch of emoji) {
    const cp = ch.codePointAt(0)
    if (cp === undefined) continue
    if (!keepFe0f && cp === 0xfe0f) continue
    points.push(cp.toString(16))
  }
  return points.join('-')
}

export function appleEmojiUrl(emoji: string, keepFe0f = false): string {
  return `${APPLE_CDN}/${emojiToAppleKey(emoji, keepFe0f)}.png`
}

export function loadAppleEmojiImage(emoji: string): Promise<HTMLImageElement> {
  const candidates = [appleEmojiUrl(emoji, false), appleEmojiUrl(emoji, true)]

  return new Promise((resolve, reject) => {
    const tryLoad = (index: number) => {
      if (index >= candidates.length) {
        reject(new Error(`Failed to load Apple emoji: ${emoji}`))
        return
      }
      const img = new Image()
      img.crossOrigin = 'anonymous'
      img.onload = () => resolve(img)
      img.onerror = () => tryLoad(index + 1)
      img.src = candidates[index]!
    }
    tryLoad(0)
  })
}
