<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useLocaleStore } from '@/stores/locale'
import LocaleSwitch from '@/components/LocaleSwitch.vue'
import SnapText from '@/components/SnapText.vue'
import BannerMotifs from '@/components/BannerMotifs.vue'
import ChoiceSheet from '@/components/ChoiceSheet.vue'
import NavGlyph from '@/components/NavGlyph.vue'
import { randomBannerStyle, renderGeneratedAvatarFile } from '@/utils/profileArt'
import { mediaUrl } from '@/utils/mediaUrl'
import NotificationSettings from '@/components/NotificationSettings.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

const auth = useAuthStore()
const locale = useLocaleStore()

type View = 'list' | 'account' | 'notifications'
type EditField = 'name' | 'phone' | 'username' | 'bio' | null
type ChoiceKind = 'banner' | 'avatar' | null

const view = ref<View>('list')
const saving = ref(false)
const editField = ref<EditField>(null)
const draft = ref('')
const choiceKind = ref<ChoiceKind>(null)
const bannerInput = ref<HTMLInputElement | null>(null)
const avatarInput = ref<HTMLInputElement | null>(null)
const inlineInput = ref<HTMLInputElement | null>(null)
const errorText = ref<string | null>(null)
const committing = ref(false)
/** Local blob preview so avatar shows even if `/media` briefly fails. */
const avatarPreview = ref<string | null>(null)

const user = computed(() => auth.user)
const avatarSrc = computed(
  () => avatarPreview.value || mediaUrl(user.value?.avatar) || null,
)

const initials = computed(() => {
  const name = displayName.value || user.value?.username || '?'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0]![0] + parts[1]![0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const displayName = computed(() => {
  const u = user.value
  if (!u) return ''
  const full = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  return full || u.username
})

const bannerBg = computed(() => {
  const style = user.value?.banner_style
  if (style?.from && style?.to) {
    return `linear-gradient(to top, ${style.from}, ${style.to})`
  }
  return 'linear-gradient(160deg, #0d6f7a 0%, #00a8b8 48%, #056874 100%)'
})

const usernameHandle = computed(() => {
  const name = user.value?.username?.replace(/^@/, '') || ''
  return name ? `@${name}` : '@'
})

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      view.value = 'list'
      editField.value = null
      choiceKind.value = null
      errorText.value = null
      if (avatarPreview.value) {
        URL.revokeObjectURL(avatarPreview.value)
        avatarPreview.value = null
      }
      document.body.style.overflow = ''
      return
    }
    document.body.style.overflow = 'hidden'
    void auth.refreshMe().catch(() => undefined)
  },
)

function onKey(ev: KeyboardEvent) {
  if (!props.open) return
  if (ev.key !== 'Escape') return
  if (choiceKind.value) {
    choiceKind.value = null
    return
  }
  if (editField.value) {
    editField.value = null
    return
  }
  if (view.value === 'account' || view.value === 'notifications') {
    view.value = 'list'
    return
  }
  emit('close')
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

function openAccount() {
  view.value = 'account'
}

function openNotifications() {
  view.value = 'notifications'
}

function startEdit(field: Exclude<EditField, null>) {
  const u = user.value
  if (!u) return
  editField.value = field
  if (field === 'name') draft.value = [u.first_name, u.last_name].filter(Boolean).join(' ')
  else if (field === 'phone') draft.value = u.phone || ''
  else if (field === 'username') draft.value = u.username.replace(/^@/, '')
  else if (field === 'bio') draft.value = u.bio || ''
  void nextTick(() => {
    inlineInput.value?.focus()
    inlineInput.value?.select()
  })
}

async function commitEdit() {
  const field = editField.value
  if (!field || committing.value) return
  committing.value = true
  saving.value = true
  errorText.value = null
  try {
    if (field === 'name') {
      const parts = draft.value.trim().split(/\s+/).filter(Boolean)
      await auth.updateProfile({
        first_name: parts[0] || '',
        last_name: parts.slice(1).join(' '),
      })
    } else if (field === 'phone') {
      await auth.updateProfile({ phone: draft.value.trim() })
    } else if (field === 'username') {
      await auth.updateProfile({ username: draft.value.trim().replace(/^@/, '') })
    } else if (field === 'bio') {
      await auth.updateProfile({ bio: draft.value.trim() })
    }
    editField.value = null
  } catch (e) {
    errorText.value = e instanceof Error ? e.message : locale.t('menuSoon')
  } finally {
    saving.value = false
    committing.value = false
  }
}

function cancelEdit() {
  editField.value = null
  errorText.value = null
}

async function onGenerateBanner() {
  saving.value = true
  errorText.value = null
  choiceKind.value = null
  try {
    const style = randomBannerStyle()
    await auth.updateProfile({ banner_style: style })
  } catch (e) {
    errorText.value = e instanceof Error ? e.message : locale.t('menuSoon')
  } finally {
    saving.value = false
  }
}

async function onGenerateAvatar() {
  saving.value = true
  errorText.value = null
  choiceKind.value = null
  try {
    const file = await renderGeneratedAvatarFile()
    if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
    avatarPreview.value = URL.createObjectURL(file)
    await auth.updateProfile({ avatar: file })
  } catch (e) {
    if (avatarPreview.value) {
      URL.revokeObjectURL(avatarPreview.value)
      avatarPreview.value = null
    }
    errorText.value = e instanceof Error ? e.message : locale.t('menuSoon')
  } finally {
    saving.value = false
  }
}

function onChoiceGenerate() {
  const kind = choiceKind.value
  if (kind === 'avatar') void onGenerateAvatar()
  else void onGenerateBanner()
}

function onPickUpload() {
  const kind = choiceKind.value
  choiceKind.value = null
  if (kind === 'banner') bannerInput.value?.click()
  if (kind === 'avatar') avatarInput.value?.click()
}

async function onBannerFile(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  saving.value = true
  try {
    await auth.updateProfile({ banner_image: file })
  } catch (e) {
    errorText.value = e instanceof Error ? e.message : locale.t('menuSoon')
  } finally {
    saving.value = false
  }
}

async function onAvatarFile(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  saving.value = true
  try {
    if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
    avatarPreview.value = URL.createObjectURL(file)
    await auth.updateProfile({ avatar: file })
  } catch (e) {
    if (avatarPreview.value) {
      URL.revokeObjectURL(avatarPreview.value)
      avatarPreview.value = null
    }
    errorText.value = e instanceof Error ? e.message : locale.t('menuSoon')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="settings-panel">
      <div
        v-if="open"
        class="settings-root"
        role="presentation"
        @click.self="emit('close')"
      >
        <section
          class="settings-panel glass glass-strong"
          role="dialog"
          aria-modal="true"
          :aria-label="locale.t('settingsTitle')"
          @click.stop
        >
          <header class="settings-panel__head">
            <button
              v-if="view === 'account' || view === 'notifications'"
              type="button"
              class="settings-panel__icon settings-panel__icon--back"
              :aria-label="locale.t('back')"
              @click="view = 'list'"
            >
              ←
            </button>
            <h2 class="settings-panel__title">
              <SnapText
                :k="
                  view === 'list'
                    ? 'settingsTitle'
                    : view === 'notifications'
                      ? 'notifTitle'
                      : 'settingsAccountTitle'
                "
              />
            </h2>
            <button
              type="button"
              class="settings-panel__icon settings-panel__icon--close"
              :aria-label="locale.t('profileClose')"
              @click="emit('close')"
            >
              ×
            </button>
          </header>

          <div v-if="saving" class="settings-panel__saving">
            <SnapText k="saving" />
          </div>
          <p v-if="errorText" class="settings-panel__error">{{ errorText }}</p>

          <!-- Settings list -->
          <div v-if="view === 'list'" class="settings-list">
            <button type="button" class="settings-user-row" @click="openAccount">
              <div class="settings-user-row__avatar">
                <img v-if="avatarSrc" :src="avatarSrc" alt="" />
                <span v-else>{{ initials }}</span>
              </div>
              <div class="settings-user-row__meta">
                <p class="settings-user-row__name">{{ displayName }}</p>
                <p v-if="user?.phone" class="settings-user-row__sub">{{ user.phone }}</p>
                <p class="settings-user-row__sub settings-user-row__handle">{{ usernameHandle }}</p>
              </div>
            </button>

            <nav class="settings-nav">
              <button type="button" class="settings-nav__item" @click="openAccount">
                <NavGlyph name="profile" />
                <span><SnapText k="settingsMyAccount" /></span>
              </button>
              <button type="button" class="settings-nav__item" @click="openNotifications">
                <NavGlyph name="settings" />
                <span><SnapText k="settingsNotifications" /></span>
              </button>
              <button type="button" class="settings-nav__item is-muted" disabled>
                <NavGlyph name="settings" />
                <span><SnapText k="settingsPrivacy" /></span>
                <em><SnapText k="menuSoon" /></em>
              </button>
              <button type="button" class="settings-nav__item is-muted" disabled>
                <NavGlyph name="group" />
                <span><SnapText k="settingsChats" /></span>
                <em><SnapText k="menuSoon" /></em>
              </button>
              <div class="settings-nav__item settings-nav__item--row">
                <NavGlyph name="theme" />
                <span><SnapText k="settingsLanguage" /></span>
                <LocaleSwitch class="settings-nav__locale" />
              </div>
            </nav>
          </div>

          <!-- Notifications -->
          <NotificationSettings v-else-if="view === 'notifications'" />

          <!-- My account -->
          <div v-else class="account-view">
            <div class="account-hero">
              <div
                class="account-banner"
                :style="{ background: user?.banner_image ? undefined : bannerBg }"
                role="button"
                tabindex="0"
                :aria-label="locale.t('choiceBannerTitle')"
                @click="choiceKind = 'banner'"
                @keydown.enter.prevent="choiceKind = 'banner'"
              >
                <img
                  v-if="user?.banner_image"
                  :src="mediaUrl(user.banner_image) || ''"
                  alt=""
                  class="account-banner__img"
                />
                <BannerMotifs
                  v-else-if="user?.banner_style?.motifs?.length"
                  class="account-banner__motifs"
                  :motifs="user.banner_style.motifs"
                />
                <BannerMotifs
                  v-else
                  class="account-banner__motifs"
                  :motifs="['bolt', 'orb', 'spark']"
                />
              </div>

              <div class="account-avatar-wrap">
                <div class="account-avatar">
                  <img v-if="avatarSrc" :src="avatarSrc" alt="" />
                  <span v-else>{{ initials }}</span>
                </div>
                <button
                  type="button"
                  class="account-avatar__cam"
                  :aria-label="locale.t('choiceAvatarTitle')"
                  @click.stop="choiceKind = 'avatar'"
                >
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M4.5 9.2h2.1l1.2-2.2h8.4l1.2 2.2h2.1A2.2 2.2 0 0 1 21.7 11.4v7A2.2 2.2 0 0 1 19.5 20.6h-15A2.2 2.2 0 0 1 2.3 18.4v-7A2.2 2.2 0 0 1 4.5 9.2Z"
                      stroke="currentColor"
                      stroke-width="1.6"
                      stroke-linejoin="round"
                    />
                    <circle cx="12" cy="14.2" r="3.1" stroke="currentColor" stroke-width="1.6" />
                  </svg>
                </button>
              </div>
            </div>

            <div class="account-identity">
              <p class="account-identity__name">{{ displayName }}</p>
              <button
                v-if="editField !== 'bio'"
                type="button"
                class="account-identity__bio"
                @click="startEdit('bio')"
              >
                {{ user?.bio?.trim() || locale.t('settingsBioHint') }}
              </button>
              <div v-else class="account-edit">
                <textarea
                  v-model="draft"
                  class="field account-edit__area"
                  rows="3"
                  maxlength="255"
                  @keydown.ctrl.enter.prevent="commitEdit"
                />
                <div class="account-edit__actions">
                  <button type="button" class="btn btn-ghost" @click="cancelEdit">
                    {{ locale.t('profileClose') }}
                  </button>
                  <button type="button" class="btn btn-primary" @click="commitEdit">
                    OK
                  </button>
                </div>
              </div>
            </div>

            <div class="account-fields">
              <div class="account-field" :class="{ 'is-editing': editField === 'name' }">
                <NavGlyph name="profile" />
                <span class="account-field__label"><SnapText k="settingsDisplayName" /></span>
                <button
                  v-if="editField !== 'name'"
                  type="button"
                  class="account-field__value is-accent"
                  @click="startEdit('name')"
                >
                  {{ displayName || '—' }}
                </button>
                <input
                  v-else
                  ref="inlineInput"
                  v-model="draft"
                  class="account-field__inline"
                  @keydown.enter.prevent="commitEdit"
                  @keydown.esc.prevent="cancelEdit"
                  @blur="commitEdit"
                />
              </div>

              <div class="account-field" :class="{ 'is-editing': editField === 'phone' }">
                <NavGlyph name="calls" />
                <span class="account-field__label"><SnapText k="settingsPhoneNumber" /></span>
                <button
                  v-if="editField !== 'phone'"
                  type="button"
                  class="account-field__value is-accent"
                  @click="startEdit('phone')"
                >
                  {{ user?.phone || '—' }}
                </button>
                <input
                  v-else
                  ref="inlineInput"
                  v-model="draft"
                  class="account-field__inline"
                  inputmode="tel"
                  @keydown.enter.prevent="commitEdit"
                  @keydown.esc.prevent="cancelEdit"
                  @blur="commitEdit"
                />
              </div>

              <div class="account-field" :class="{ 'is-editing': editField === 'username' }">
                <NavGlyph name="group" />
                <span class="account-field__label"><SnapText k="profileUsername" /></span>
                <button
                  v-if="editField !== 'username'"
                  type="button"
                  class="account-field__value is-accent"
                  @click="startEdit('username')"
                >
                  {{ usernameHandle }}
                </button>
                <div v-else class="account-field__inline-user">
                  <span class="account-edit__at">@</span>
                  <input
                    ref="inlineInput"
                    v-model="draft"
                    class="account-field__inline"
                    @keydown.enter.prevent="commitEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="commitEdit"
                  />
                </div>
              </div>

              <p class="account-field__hint"><SnapText k="settingsUsernameHint" /></p>
            </div>
          </div>
        </section>
      </div>
    </Transition>

    <input ref="bannerInput" type="file" accept="image/*" class="hidden" @change="onBannerFile" />
    <input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="onAvatarFile" />

    <ChoiceSheet
      :open="!!choiceKind"
      :title-key="choiceKind === 'avatar' ? 'choiceAvatarTitle' : 'choiceBannerTitle'"
      @close="choiceKind = null"
      @upload="onPickUpload"
      @generate="onChoiceGenerate"
    />
  </Teleport>
</template>
