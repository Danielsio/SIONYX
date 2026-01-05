/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    css: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        'cypress/',
        'dist/',
        'packages/*/test{,s}/',
        '**/*.config.{js,ts}',
        '**/.{eslint,mocha,prettier}rc.{js,cjs,ts}',
      ],
    },
  },
})




