/** The service worker (public/sw.js) and the online state the app shows. */
import { onScopeDispose, ref } from 'vue'

export function registerServiceWorker() {
  // Dev builds change every save; a worker there would serve stale code.
  if (import.meta.env.PROD && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js'))
  }
}

/** Forget the course pages kept for offline reading, e.g. on sign-out. */
export function clearOfflineData() {
  navigator.serviceWorker?.controller?.postMessage('sign-out')
}

export function useOnline() {
  const online = ref(navigator.onLine)
  const update = () => (online.value = navigator.onLine)
  window.addEventListener('online', update)
  window.addEventListener('offline', update)
  onScopeDispose(() => {
    window.removeEventListener('online', update)
    window.removeEventListener('offline', update)
  })
  return online
}
