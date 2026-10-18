import { defineStore } from 'pinia'
import { auth, type User } from '@/api/auth'
import { refreshAccessToken, setAccessToken } from '@/api/client'
import { clearOfflineData } from '@/lib/offline'

export const useSessionStore = defineStore('session', {
  state: () => ({ user: null as User | null }),
  getters: {
    isAuthenticated: (s) => s.user !== null,
    displayName: (s) => (s.user ? `${s.user.first_name} ${s.user.last_name}`.trim() || s.user.username : ''),
  },
  actions: {
    /** On app start: the refresh cookie, if present, restores the session silently. */
    async bootstrap() {
      if (await refreshAccessToken()) {
        this.user = await auth.me().catch(() => null)
      } else if (!navigator.onLine) {
        // Offline: the service worker answers with the last signed-in user, if any,
        // so lessons read before stay readable. Writes fail until the network is back.
        this.user = await auth.me().catch(() => null)
      } else {
        // Online with no valid session: what an earlier user left offline must not show later.
        clearOfflineData()
      }
    },
    async login(email: string, password: string) {
      const { access, user } = await auth.login(email, password)
      setAccessToken(access)
      this.user = user
    },
    async logout() {
      await auth.logout().catch(() => undefined)
      setAccessToken(null)
      clearOfflineData()
      this.user = null
    },
    async refreshUser() {
      this.user = await auth.me()
    },
  },
})
