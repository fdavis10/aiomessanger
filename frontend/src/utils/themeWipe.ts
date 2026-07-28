/** Circular wipe that reveals the new theme — form stays and recolors with the circle. */

export type ThemeMode = 'dark' | 'light'

type ViewTransition = {
  finished: Promise<void>
  ready: Promise<void>
  updateCallbackDone: Promise<void>
}

type DocumentWithVT = Document & {
  startViewTransition?: (updateCallback: () => void | Promise<void>) => ViewTransition
}

export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Applies `update` inside a view transition so the new theme is revealed
 * by an expanding circle (bottom→up for dark, top→down for light).
 * The live UI (form included) is snapshotted on both sides, so it stays put.
 */
export async function playThemeWipe(
  next: ThemeMode,
  update: () => void,
): Promise<void> {
  const doc = document as DocumentWithVT

  if (prefersReducedMotion() || typeof doc.startViewTransition !== 'function') {
    update()
    return
  }

  document.documentElement.dataset.themeWipe = next === 'dark' ? 'from-bottom' : 'from-top'

  try {
    const transition = doc.startViewTransition(() => {
      update()
    })
    await transition.finished
  } finally {
    delete document.documentElement.dataset.themeWipe
  }
}
