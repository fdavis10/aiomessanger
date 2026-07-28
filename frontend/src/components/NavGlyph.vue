<script setup lang="ts">
/**
 * Custom wayfinding glyphs — not the usual Feather/Heroicons set.
 * Angular stamp / constellation / ribbon handset / vernier dial / eclipse.
 */
defineProps<{ name: 'profile' | 'group' | 'calls' | 'settings' | 'theme' | 'logout' }>()
</script>

<template>
  <svg
    class="nav-glyph"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <!-- Wax-seal bust: angular profile in a broken ring -->
    <g v-if="name === 'profile'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.2 12.2c0-4.1 3.2-7.5 7.3-7.8 1.8-.1 3.5.4 4.9 1.4" />
      <path d="M19.8 11.5c.2 4.4-3 8.2-7.3 8.6-2 .2-3.9-.4-5.4-1.6" />
      <path d="M9.1 10.2c.4-1.6 1.7-2.6 3.2-2.5 1.4.1 2.4 1.1 2.6 2.4.2 1.4-.7 2.5-1.6 3.1-.6.4-.9.9-.9 1.5v.4" />
      <path d="M8.2 18.1c.7-1.8 2.2-2.7 4.1-2.7s3.3.8 4.1 2.5" />
    </g>

    <!-- Constellation triad + wedge join (create group) -->
    <g v-else-if="name === 'group'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="7.2" cy="8.2" r="2.1" />
      <circle cx="16.6" cy="7.6" r="2.1" />
      <circle cx="11.8" cy="16.2" r="2.2" />
      <path d="M9 9.4 L10.6 14.2" />
      <path d="M14.8 9 L12.8 14.1" />
      <path d="M9.2 7.6 L14.5 7.2" />
      <path d="M17.8 12.2 L19.2 10.4 M19.2 10.4 L17.4 10.1" />
    </g>

    <!-- Ribbon handset — continuous folded stroke, not a phone outline -->
    <g v-else-if="name === 'calls'" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <path
        d="M7.2 4.8c1.1.2 2 .9 2.4 1.9l.6 1.6c.3.8 0 1.7-.7 2.2l-1.1.7c.9 2.1 2.6 3.8 4.8 4.6l.8-1c.6-.7 1.5-.9 2.3-.6l1.7.6c1 .4 1.6 1.4 1.5 2.5-.2 1.8-1.9 3.1-3.7 2.9-5.4-.5-9.9-5-10.5-10.4-.2-1.8 1.1-3.4 2.9-3.5Z"
      />
      <path d="M14.6 5.2c2 .5 3.6 2 4.2 3.9" opacity="0.55" />
      <path d="M15.8 3.4c3 .8 5.3 3.1 6.1 6.1" opacity="0.35" />
    </g>

    <!-- Vernier / eccentric dial (settings) -->
    <g v-else-if="name === 'settings'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3.1" />
      <path d="M12 3.4v2.2M12 18.4v2.2M3.4 12h2.2M18.4 12h2.2" />
      <path d="M6.1 6.1l1.5 1.5M16.4 16.4l1.5 1.5M16.4 6.1l1.5-1.5M6.1 17.9l1.5-1.5" opacity="0.45" />
      <path d="M14.6 5.2l1.1-2.1 1.7.9-1 2.1c.6.3 1.1.8 1.4 1.4l2.1-.9.9 1.7-2.1 1.1" />
    </g>

    <!-- Eclipse disc — theme, not sun/moon twins -->
    <g v-else-if="name === 'theme'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11.2" cy="12" r="6.4" />
      <path d="M11.2 5.6c3.5 0 6.4 2.9 6.4 6.4s-2.9 6.4-6.4 6.4" fill="currentColor" fill-opacity="0.18" stroke="none" />
      <path d="M14.8 7.4c2.2 1.1 3.4 3.5 2.9 5.9-.5 2.5-2.5 4.3-5 4.7" />
    </g>

    <!-- Door arrow exit -->
    <g v-else-if="name === 'logout'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10.2 4.5H6.4A2.2 2.2 0 0 0 4.2 6.7v10.6A2.2 2.2 0 0 0 6.4 19.5h3.8" />
      <path d="M10.5 12H20" />
      <path d="M16.2 8.2 L20 12 l-3.8 3.8" />
    </g>
  </svg>
</template>
