import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// /api and /ws are proxied to the backend in development so the refresh cookie is first-party.
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000', changeOrigin: false },
      '/ws': { target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000', ws: true },
    },
  },
})
