import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // 外部からのアクセスを許可
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // IPv4アドレスを明示的に指定
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000', // IPv4アドレスを明示的に指定
        changeOrigin: true,
      },
    },
  },
})
