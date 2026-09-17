import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND = process.env.VITE_DEV_BACKEND || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5175,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/media': { target: BACKEND, changeOrigin: true },
      '/health': { target: BACKEND, changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
});
