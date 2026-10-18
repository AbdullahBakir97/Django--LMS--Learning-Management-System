import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'
import './styles/tokens.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { router } from './router'
import { applyStoredTheme } from './composables/useTheme'
import { useSessionStore } from './stores/session'
import { registerServiceWorker } from './lib/offline'

applyStoredTheme()
registerServiceWorker()

const app = createApp(App).use(createPinia())

// Restore the session from the refresh cookie before the router runs its first guard.
await useSessionStore().bootstrap()

app.use(router).mount('#app')
