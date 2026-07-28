/** Thanos-style dust dissolve for locale switches — canvas-free, Range-measured glyphs. */

const targets = new Set<HTMLElement>()

export function registerSnapTarget(el: HTMLElement): void {
  targets.add(el)
}

export function unregisterSnapTarget(el: HTMLElement): void {
  targets.delete(el)
}

export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function isVisible(el: HTMLElement): boolean {
  const rect = el.getBoundingClientRect()
  if (rect.width < 1 || rect.height < 1) return false
  const style = getComputedStyle(el)
  if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') {
    return false
  }
  return true
}

type Glyph = { char: string; rect: DOMRect }

function measureGlyphs(el: HTMLElement): Glyph[] {
  const glyphs: Glyph[] = []
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  let node = walker.nextNode() as Text | null
  while (node) {
    const value = node.nodeValue ?? ''
    const chars = Array.from(value)
    let offset = 0
    for (const char of chars) {
      if (char.trim()) {
        const range = document.createRange()
        range.setStart(node, offset)
        range.setEnd(node, offset + char.length)
        const rect = range.getBoundingClientRect()
        if (rect.width > 0 && rect.height > 0) {
          glyphs.push({ char, rect })
        }
      }
      offset += char.length
    }
    node = walker.nextNode() as Text | null
  }
  return glyphs
}

function createDustLayer(): HTMLElement {
  const layer = document.createElement('div')
  layer.className = 'snap-dust-layer'
  layer.setAttribute('aria-hidden', 'true')
  document.body.appendChild(layer)
  return layer
}

function spawnDust(layer: HTMLElement, el: HTMLElement, glyphs: Glyph[]): void {
  const style = getComputedStyle(el)
  const font = style.font
  const color = style.color

  for (const { char, rect } of glyphs) {
    const span = document.createElement('span')
    span.className = 'snap-dust'
    span.textContent = char
    span.style.left = `${rect.left}px`
    span.style.top = `${rect.top}px`
    span.style.font = font
    span.style.color = color
    span.style.lineHeight = `${rect.height}px`
    layer.appendChild(span)

    const dx = (Math.random() - 0.5) * 110
    const dy = (Math.random() - 0.35) * 90 - 12
    const rot = (Math.random() - 0.5) * 140
    const delay = Math.random() * 160
    const duration = 480 + Math.random() * 220

    // Force layout before transitioning so the first frame stays in place.
    void span.offsetWidth
    span.style.transition = `transform ${duration}ms cubic-bezier(0.2, 0.7, 0.2, 1) ${delay}ms, opacity ${duration * 0.85}ms ease ${delay}ms, filter ${duration}ms ease ${delay}ms`
    span.style.transform = `translate(${dx}px, ${dy}px) rotate(${rot}deg) scale(${0.15 + Math.random() * 0.35})`
    span.style.opacity = '0'
    span.style.filter = 'blur(1.5px)'
  }
}

const MAX_GLYPHS = 420

export async function dissolveTargets(): Promise<void> {
  const els = [...targets].filter(isVisible)
  if (!els.length) return

  let glyphsBudget = MAX_GLYPHS
  const layer = createDustLayer()

  for (const el of els) {
    const glyphs = measureGlyphs(el)
    if (!glyphs.length) {
      el.classList.add('is-snapping')
      continue
    }
    const take =
      glyphs.length <= glyphsBudget
        ? glyphs
        : glyphs.filter((_, i) => i % Math.ceil(glyphs.length / glyphsBudget) === 0).slice(0, glyphsBudget)
    glyphsBudget -= take.length
    spawnDust(layer, el, take)
    el.classList.add('is-snapping')
  }

  await sleep(620)
  layer.remove()
}

export async function appearTargets(): Promise<void> {
  const els = [...targets].filter((el) => el.classList.contains('is-snapping'))
  for (const el of els) {
    el.classList.remove('is-snapping')
    el.classList.add('is-appearing')
  }
  await sleep(420)
  for (const el of els) {
    el.classList.remove('is-appearing')
  }
}
