import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/signatures': 'http://127.0.0.1:8000',
      '/documents': 'http://127.0.0.1:8000',
      '/verifications': 'http://127.0.0.1:8000',
      // not a bare '/admin' prefix: that also matches the SPA's own /admin page route
      '/admin/audit-log': 'http://127.0.0.1:8000',
      '/admin/ledger': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
