// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  server: {
    allowedHosts: ['.trycloudflare.com', 'localhost']
  },
  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        '/exercises': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/workouts': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
});