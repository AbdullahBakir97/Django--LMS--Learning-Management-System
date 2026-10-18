import { ref } from 'vue'

export type Theme = 'light' | 'dark'
const KEY = 'lms.theme'
export const theme = ref<Theme>('light')

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function applyTheme(next: Theme) {
  theme.value = next
  document.documentElement.dataset.theme = next
}

export function applyStoredTheme() {
  let stored: string | null = null
  try {
    stored = localStorage.getItem(KEY)
  } catch {
    /* storage unavailable */
  }
  applyTheme(stored === 'dark' || stored === 'light' ? stored : systemTheme())
}

export function toggleTheme() {
  const next: Theme = theme.value === 'dark' ? 'light' : 'dark'
  applyTheme(next)
  try {
    localStorage.setItem(KEY, next)
  } catch {
    /* storage unavailable */
  }
}
