<script setup lang="ts">
defineProps<{
  motifs: string[]
}>()
</script>

<template>
  <svg class="banner-motifs" viewBox="0 0 320 140" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <g
      v-for="(motif, i) in motifs"
      :key="`${motif}-${i}`"
      :transform="`translate(${40 + (i * 97) % 260} ${28 + (i * 37) % 70}) scale(${0.85 + (i % 3) * 0.12})`"
      fill="currentColor"
      opacity="0.22"
    >
      <!-- Geometric vector “emoji-like” objects, not system emoji -->
      <path v-if="motif === 'bolt'" d="M18 2 L8 22 H16 L10 42 L30 16 H20 L26 2 Z" />
      <path
        v-else-if="motif === 'leaf'"
        d="M24 4 C10 10 4 28 18 40 C32 28 38 10 24 4 Z M18 18 L28 34"
      />
      <circle v-else-if="motif === 'orb'" cx="20" cy="20" r="14" />
      <path
        v-else-if="motif === 'wave'"
        d="M2 22 C8 10 14 10 20 22 C26 34 32 34 38 22"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        stroke-linecap="round"
      />
      <path v-else-if="motif === 'diamond'" d="M20 2 L36 20 L20 38 L4 20 Z" />
      <path
        v-else-if="motif === 'spark'"
        d="M20 2 L23 15 L36 18 L23 21 L20 34 L17 21 L4 18 L17 15 Z"
      />
      <path
        v-else-if="motif === 'arc'"
        d="M4 30 A16 16 0 0 1 36 30"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        stroke-linecap="round"
      />
      <circle v-else cx="12" cy="28" r="5" />
      <circle v-if="motif === 'seed'" cx="22" cy="14" r="7" />
    </g>
  </svg>
</template>
