import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy Firebase Storage requests to bypass CORS in dev
      '/storage-proxy': {
        target: 'https://storage.googleapis.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/storage-proxy/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          router: ['react-router-dom'],
          firebase: ['firebase/app', 'firebase/auth', 'firebase/database'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', 'react-router-dom'],
  },
});
