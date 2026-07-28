<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import type { User } from '@/types'
import { useLocaleStore } from '@/stores/locale'
import SnapText from '@/components/SnapText.vue'
import BannerMotifs from '@/components/BannerMotifs.vue'
import { mediaUrl } from '@/utils/mediaUrl'

const props = defineProps<{
  open: boolean
  user: User | null
}>()

const emit = defineEmits<{
  close: []
  edit: []
}>()

const locale = useLocaleStore()

const initials = computed(() => {
  const name = displayName.value.trim() || props.user?.username || '?'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0]![0] + parts[1]![0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const displayName = computed(() => {
  const u = props.user
  if (!u) return ''
  const full = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  return full || u.username
})

const phone = computed(() => props.user?.phone?.trim() || '—')
const bio = computed(() => props.user?.bio?.trim() || '—')
const username = computed(() => (props.user?.username ? `@${props.user.username}` : '—'))

const bannerBg = computed(() => {
  const style = props.user?.banner_style
  if (style?.from && style?.to) return `linear-gradient(to top, ${style.from}, ${style.to})`
  return undefined
})

function onKey(ev: KeyboardEvent) {
  if (ev.key === 'Escape' && props.open) emit('close')
}

watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="profile-card">
      <div
        v-if="open && user"
        class="profile-card-root"
        role="presentation"
        @click.self="emit('close')"
      >
        <article
          class="profile-card"
          role="dialog"
          aria-modal="true"
          :aria-label="locale.t('menuProfile')"
          @click.stop
        >
          <div class="profile-card__hero">
            <div
              class="profile-card__banner"
              :style="bannerBg && !user.banner_image ? { background: bannerBg } : undefined"
            >
              <img
                v-if="user.banner_image"
                :src="mediaUrl(user.banner_image) || ''"
                alt=""
                class="profile-card__banner-img"
              />
              <BannerMotifs
                v-else
                class="profile-card__pattern"
                :motifs="user.banner_style?.motifs?.length ? user.banner_style.motifs : ['bolt', 'orb', 'spark']"
              />

              <button
                type="button"
                class="profile-card__icon-btn profile-card__edit"
                :aria-label="locale.t('profileEdit')"
                :title="locale.t('profileEdit')"
                @click="emit('edit')"
              >
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M14.2 5.4l4.4 4.4M5 19l.7-3.9L15.8 5c.6-.6 1.6-.6 2.2 0l.9.9c.6.6.6 1.6 0 2.2L9 19.2 5 19Z"
                    stroke="currentColor"
                    stroke-width="1.7"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>

              <button
                type="button"
                class="profile-card__icon-btn profile-card__close"
                :aria-label="locale.t('profileClose')"
                :title="locale.t('profileClose')"
                @click="emit('close')"
              >
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M7 7l10 10M17 7L7 17"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>

            <div class="profile-card__avatar">
              <img
                v-if="user.avatar"
                :src="mediaUrl(user.avatar) || ''"
                alt=""
                class="profile-card__avatar-img"
              />
              <span v-else>{{ initials }}</span>
            </div>
          </div>

          <div class="profile-card__identity">
            <h2 class="profile-card__name">{{ displayName }}</h2>
            <p class="profile-card__status">
              <span class="profile-card__status-dot" aria-hidden="true" />
              <SnapText k="live" />
            </p>
          </div>

          <dl class="profile-card__fields">
            <div class="profile-card__field">
              <dt><SnapText k="profilePhone" /></dt>
              <dd>{{ phone }}</dd>
            </div>
            <div class="profile-card__field">
              <dt><SnapText k="profileAccountId" /></dt>
              <dd>{{ user.id }}</dd>
            </div>
            <div class="profile-card__field">
              <dt><SnapText k="profileAbout" /></dt>
              <dd>{{ bio }}</dd>
            </div>
            <div class="profile-card__field">
              <dt><SnapText k="profileUsername" /></dt>
              <dd>{{ username }}</dd>
            </div>
          </dl>
        </article>
      </div>
    </Transition>
  </Teleport>
</template>
