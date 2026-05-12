import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://localhost:3002', '/public': 'http://localhost:3002' }
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'element-plus', 'axios', '@element-plus/icons-vue'],
  },
  ssr: { noExternal: ['element-plus'] },
})
