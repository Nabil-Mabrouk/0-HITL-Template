import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    // Environnement DOM simulé (jsdom)
    environment: 'jsdom',

    // Fichier de setup global (mocks, matchers supplémentaires)
    setupFiles: ['./src/test/setup.ts'],

    // Inclure les fichiers de test
    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    // Couverture de code
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        lines: 50,
        functions: 50,
        branches: 40,
      },
    },

    // Timeout par test (ms)
    testTimeout: 10000,

    // Affichage des tests
    reporters: ['verbose'],

    // Variables d'environnement de test
    env: {
      VITE_API_URL: 'http://localhost:8000',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
