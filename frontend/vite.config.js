import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
  const isBuild = command === 'build'

  return {
    plugins: [react()],
    // In dev, serve at root '/'; in production build, assets will be served from FastAPI at /static/
    base: isBuild ? '/static/' : '/',
    server: {
      port: 5173,
      host: '0.0.0.0', // This allows external connections

      // Add CORS and origin configuration for WebSocket connections
      hmr: {
        clientPort: 5173,
        host: 'subreverse.fun' // This ensures HMR works with your domain
      },

      proxy: {
        '/search': backend,
        '/health': backend,
        '/upload_file': backend,
        '/upload_zip': backend,
        '/clear': backend,
        '/index_elastic_search': backend,
        '/get_random': backend,
        '/delete_all': backend,
        '/export': backend,
        '/import_ndjson': backend,
        '/stats': backend,
        '/auth': backend,
        '/self': backend,
        '/idioms': backend,
      },
    },
  }
})