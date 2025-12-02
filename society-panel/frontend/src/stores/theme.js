// Store for managing light/dark theme preferences with localStorage persistence.

import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', () => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    const theme = ref(savedTheme)
    const isDark = ref(savedTheme === 'dark')

    const toggleTheme = () => {
        theme.value = theme.value === 'light' ? 'dark' : 'light'
        isDark.value = theme.value === 'dark'
    }

    const setTheme = (newTheme) => {
        theme.value = newTheme
        isDark.value = newTheme === 'dark'
    }

    watch(theme, (newTheme) => {
        document.documentElement.setAttribute('data-theme', newTheme)
        localStorage.setItem('theme', newTheme)
    }, { immediate: true })

    return {
        theme,
        isDark,
        toggleTheme,
        setTheme
    }
})
