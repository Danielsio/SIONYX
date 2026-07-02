import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Load .env from repo root (parent directory) for monorepo support
  envDir: path.resolve(__dirname, '..'),
  build: {
    rollupOptions: {
      output: {
        // Vite 8 bundles with Rolldown: the old object-form `manualChunks`
        // is unsupported ("manualChunks is not a function"); `advancedChunks`
        // groups replace it. First matching group wins — keep router before
        // the react group.
        advancedChunks: {
          groups: [
            { name: 'router', test: /[\\/]node_modules[\\/]react-router(-dom)?[\\/]/ },
            { name: 'vendor', test: /[\\/]node_modules[\\/]react(-dom)?[\\/]/ },
            { name: 'antd', test: /[\\/]node_modules[\\/](antd|@ant-design)[\\/]/ },
            { name: 'firebase', test: /[\\/]node_modules[\\/](firebase|@firebase)[\\/]/ },
            { name: 'framer-motion', test: /[\\/]node_modules[\\/]framer-motion[\\/]/ },
            { name: 'gsap', test: /[\\/]node_modules[\\/]gsap[\\/]/ },
          ],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      'react-router-dom',
      'firebase/app',
      'firebase/auth',
      'firebase/database',
      'framer-motion',
      'zustand',
    ],
  },
});
