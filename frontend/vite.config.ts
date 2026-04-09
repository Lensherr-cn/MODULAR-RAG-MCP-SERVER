import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',  // 同时监听 IPv4 和 IPv6
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 使用 IPv4 地址避免 IPv6 解析问题
        changeOrigin: true,
      }
    }
  }
})
