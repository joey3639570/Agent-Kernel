// Store for managing simulation status and error messages.

import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useSimulationStore = defineStore('simulation', () => {
  const status = ref('stopped')
  const errorMessage = ref('')

  function setStatus(newStatus) {
    status.value = newStatus
  }

  function setErrorMessage(message) {
    errorMessage.value = message
  }

  return { status, errorMessage, setStatus, setErrorMessage }
})
