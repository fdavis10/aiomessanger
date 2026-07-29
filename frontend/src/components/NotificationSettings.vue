<script setup lang="ts">
import { computed } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import { useNotificationStore } from '@/stores/notifications'
import SettingsToggle from '@/components/SettingsToggle.vue'
import SnapText from '@/components/SnapText.vue'

const locale = useLocaleStore()
const notif = useNotificationStore()

const masterOff = computed(() => !notif.prefs.showOnDevice)

const preview = computed(() => {
  const { previewName, previewText } = notif.prefs
  if (!previewName) {
    return {
      sender: locale.t('notifHiddenSender'),
      body: locale.t('notifHiddenBodyNoName'),
      brand: true as const,
    }
  }
  return {
    sender: locale.t('notifDemoSender'),
    body: previewText ? locale.t('notifDemoBody') : locale.t('notifHiddenBodyNoText'),
    brand: false as const,
  }
})

async function onBrowserPush(value: boolean) {
  if (value) {
    const permission = await notif.ensureBrowserPermission()
    if (permission === 'denied' || permission === 'unsupported') {
      notif.set('browserPush', false)
      return
    }
  }
  notif.set('browserPush', value)
}
</script>

<template>
  <div class="notif-view" :class="{ 'is-master-off': masterOff }">
    <section class="notif-section">
      <h3 class="notif-section__title"><SnapText k="notifSectionShow" /></h3>
      <div class="notif-card">
        <SettingsToggle
          :model-value="notif.prefs.showOnDevice"
          :label="locale.t('notifShowDevice')"
          @update:model-value="notif.set('showOnDevice', $event)"
        />
        <p class="notif-hint"><SnapText k="notifShowDeviceHint" /></p>
      </div>
    </section>

    <section class="notif-section" :aria-disabled="masterOff">
      <h3 class="notif-section__title"><SnapText k="notifSectionGeneral" /></h3>
      <div class="notif-card">
        <SettingsToggle
          :model-value="notif.prefs.browserPush"
          :label="locale.t('notifBrowser')"
          :disabled="masterOff"
          @update:model-value="onBrowserPush"
        />
        <SettingsToggle
          :model-value="notif.prefs.sound"
          :label="locale.t('notifSound')"
          :disabled="masterOff"
          @update:model-value="notif.set('sound', $event)"
        />
        <div class="notif-volume" :class="{ 'is-disabled': masterOff || !notif.prefs.sound }">
          <div class="notif-volume__head">
            <span>{{ locale.t('notifVolume') }}</span>
            <span class="notif-volume__value">{{ notif.prefs.volume }}%</span>
          </div>
          <input
            class="notif-volume__range"
            type="range"
            min="0"
            max="100"
            step="1"
            :value="notif.prefs.volume"
            :disabled="masterOff || !notif.prefs.sound"
            :aria-label="locale.t('notifVolume')"
            @input="notif.set('volume', Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <div class="notif-preview-block" :class="{ 'is-disabled': masterOff }">
          <div class="notif-preview" aria-live="polite">
            <div class="notif-preview__avatar" :class="{ 'is-brand': preview.brand }" aria-hidden="true">
              <svg v-if="!preview.brand" viewBox="0 0 64 64" class="notif-preview__dino">
                <circle cx="32" cy="32" r="32" fill="#f5c542" />
                <ellipse cx="34" cy="36" rx="16" ry="14" fill="#3fad4a" />
                <ellipse cx="22" cy="28" rx="9" ry="8" fill="#3fad4a" />
                <circle cx="19" cy="26" r="2.2" fill="#16301a" />
                <path d="M12 30c4 2 7 2 10 0" stroke="#2d7a36" stroke-width="2" fill="none" stroke-linecap="round" />
                <path d="M44 30c3-6 8-8 12-6-2 5-6 9-12 10z" fill="#2d7a36" />
              </svg>
              <span v-else class="notif-preview__brand">A</span>
            </div>
            <div class="notif-preview__text">
              <p class="notif-preview__name">{{ preview.sender }}</p>
              <p class="notif-preview__body">{{ preview.body }}</p>
            </div>
          </div>

          <div class="notif-chips" role="group" :aria-label="locale.t('notifSectionGeneral')">
            <button
              type="button"
              class="notif-chip"
              :class="{ 'is-on': notif.prefs.previewName }"
              :disabled="masterOff"
              @click="notif.set('previewName', !notif.prefs.previewName)"
            >
              <span class="notif-chip__check" aria-hidden="true">
                <svg viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4" />
                  <path
                    v-if="notif.prefs.previewName"
                    d="M4.5 8.2l2.2 2.2 4.6-4.6"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </span>
              <SnapText k="notifPreviewName" />
            </button>
            <button
              type="button"
              class="notif-chip"
              :class="{ 'is-on': notif.prefs.previewText }"
              :disabled="masterOff"
              @click="notif.set('previewText', !notif.prefs.previewText)"
            >
              <span class="notif-chip__check" aria-hidden="true">
                <svg viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4" />
                  <path
                    v-if="notif.prefs.previewText"
                    d="M4.5 8.2l2.2 2.2 4.6-4.6"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </span>
              <SnapText k="notifPreviewText" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="notif-section" :aria-disabled="masterOff">
      <h3 class="notif-section__title"><SnapText k="notifSectionChats" /></h3>
      <p class="notif-hint notif-hint--block"><SnapText k="notifChatsHint" /></p>
      <div class="notif-card">
        <SettingsToggle
          :model-value="notif.prefs.fromPrivate"
          :label="locale.t('notifFromPrivate')"
          :disabled="masterOff"
          @update:model-value="notif.set('fromPrivate', $event)"
        />
        <SettingsToggle
          :model-value="notif.prefs.fromGroups"
          :label="locale.t('notifFromGroups')"
          :disabled="masterOff"
          @update:model-value="notif.set('fromGroups', $event)"
        />
        <SettingsToggle
          :model-value="notif.prefs.fromSystem"
          :label="locale.t('notifFromSystem')"
          :disabled="masterOff"
          @update:model-value="notif.set('fromSystem', $event)"
        />
      </div>
    </section>
  </div>
</template>
