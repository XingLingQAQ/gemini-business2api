import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/api'
import type { Settings } from '@/types/api'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Settings | null>(null)
  const isLoading = ref(false)

  async function loadSettings() {
    isLoading.value = true
    try {
      settings.value = await settingsApi.get()
    } finally {
      isLoading.value = false
    }
  }

  async function updateSettings(newSettings: Settings) {
    settings.value = await settingsApi.update(newSettings)
  }

  return {
    settings,
    isLoading,
    loadSettings,
    updateSettings,
  }
})
