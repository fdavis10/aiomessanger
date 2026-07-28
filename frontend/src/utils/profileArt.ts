import { AVATAR_EMOJIS, loadAppleEmojiImage } from '@/utils/appleEmoji'
import type { BannerStyle } from '@/types'

const BANNER_MOTIFS = [
  'bolt',
  'leaf',
  'orb',
  'wave',
  'diamond',
  'spark',
  'arc',
  'seed',
] as const

export type BannerMotif = (typeof BANNER_MOTIFS)[number]

/** Soft gradients (bottom → top = from → to). */
const GRADIENT_PAIRS: Array<[string, string]> = [
  ['#0b3d4a', '#3ec4d0'],
  ['#1b4332', '#74c69d'],
  ['#3d1c54', '#c77dff'],
  ['#4a1942', '#e5989b'],
  ['#1d3557', '#a8dadc'],
  ['#3c1518', '#e76f51'],
  ['#14213d', '#fca311'],
  ['#2b2d42', '#8d99ae'],
  ['#023047', '#ffb703'],
  ['#240046', '#7b2cbf'],
  ['#0f4c5c', '#5f0f40'],
  ['#1a1a2e', '#e94560'],
]

function pick<T>(items: readonly T[]): T {
  return items[Math.floor(Math.random() * items.length)]!
}

function shuffle<T>(items: readonly T[]): T[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j]!, copy[i]!]
  }
  return copy
}

export function randomBannerStyle(): BannerStyle {
  const [from, to] = pick(GRADIENT_PAIRS)
  const motifs = shuffle(BANNER_MOTIFS).slice(0, 3 + Math.floor(Math.random() * 3))
  return { from, to, motifs }
}

export async function renderGeneratedAvatarFile(): Promise<File> {
  const size = 512
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas unavailable')

  // Full-bleed square — circular crop is CSS-only. Canvas arcs leave
  // semi-transparent fringe that shows the avatar container background.
  const [from, to] = pick(GRADIENT_PAIRS)
  const grad = ctx.createLinearGradient(0, size, 0, 0)
  grad.addColorStop(0, from)
  grad.addColorStop(1, to)
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, size, size)

  const emoji = pick(AVATAR_EMOJIS)
  try {
    const img = await loadAppleEmojiImage(emoji)
    const emojiSize = size * 0.52
    ctx.drawImage(img, (size - emojiSize) / 2, (size - emojiSize) / 2, emojiSize, emojiSize)
  } catch {
    // CDN blocked / offline — still produce a usable gradient avatar.
    ctx.fillStyle = 'rgba(255,255,255,0.92)'
    ctx.font = `bold ${Math.floor(size * 0.42)}px "Segoe UI Emoji", "Apple Color Emoji", sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(emoji, size / 2, size / 2 + size * 0.03)
  }

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error('Avatar export failed'))),
      'image/png',
    )
  })
  return new File([blob], `avatar-${Date.now()}.png`, { type: 'image/png' })
}
