import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 300000,
        timeout: 300000,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 10000,
        timeout: 10000,
      },
      '/agent': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 60000,
        timeout: 60000,
      },
      '/reset': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 10000,
        timeout: 10000,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      }
    }
  }
})