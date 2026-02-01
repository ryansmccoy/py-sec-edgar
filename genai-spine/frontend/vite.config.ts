import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow external connections (for Docker)
    port: 5173,
    watch: {
      usePolling: true, // Enable for Docker volume watching
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://genai-api:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
