/** Soft non-intrusive chime via Web Audio (no asset file). */

let sharedCtx: AudioContext | null = null

function getCtx(): AudioContext | null {
  const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AC) return null
  if (!sharedCtx || sharedCtx.state === 'closed') sharedCtx = new AC()
  return sharedCtx
}

export async function playNotifySound(volumePercent: number): Promise<void> {
  const vol = Math.min(1, Math.max(0, volumePercent / 100)) * 0.22
  if (vol <= 0) return

  const ctx = getCtx()
  if (!ctx) return
  if (ctx.state === 'suspended') {
    try {
      await ctx.resume()
    } catch {
      return
    }
  }

  const now = ctx.currentTime
  const master = ctx.createGain()
  master.gain.setValueAtTime(0, now)
  master.gain.linearRampToValueAtTime(vol, now + 0.02)
  master.gain.exponentialRampToValueAtTime(0.0008, now + 0.55)
  master.connect(ctx.destination)

  // Soft major third — short, calm, not alarm-like.
  const tones = [
    { freq: 523.25, start: 0, dur: 0.28 },
    { freq: 659.25, start: 0.08, dur: 0.34 },
  ]

  for (const tone of tones) {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(tone.freq, now + tone.start)
    gain.gain.setValueAtTime(0, now + tone.start)
    gain.gain.linearRampToValueAtTime(1, now + tone.start + 0.025)
    gain.gain.exponentialRampToValueAtTime(0.001, now + tone.start + tone.dur)
    osc.connect(gain)
    gain.connect(master)
    osc.start(now + tone.start)
    osc.stop(now + tone.start + tone.dur + 0.05)
  }
}
