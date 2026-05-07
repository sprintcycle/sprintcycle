import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, loadEnv } from 'vite'

/** 与 ``DashboardPortDefaults``（``sprintcycle/config/runtime_config.py``）约定一致；改默认时请同步 Python 侧。 */
const DEFAULT_BACKEND_ORIGIN = 'http://127.0.0.1:8080'
const DEFAULT_DEV_SERVER_PORT = 5173

function parsePositivePort(raw: string | undefined, fallback: number): number {
  const n = Number.parseInt(raw ?? '', 10)
  if (!Number.isFinite(n) || n <= 0 || n > 65535) return fallback
  return n
}

const projectRoot = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, projectRoot, '')
  const backend =
    process.env.VITE_PROXY_TARGET || fileEnv.VITE_PROXY_TARGET || DEFAULT_BACKEND_ORIGIN
  const devServerPort = parsePositivePort(
    process.env.VITE_DEV_SERVER_PORT || fileEnv.VITE_DEV_SERVER_PORT,
    DEFAULT_DEV_SERVER_PORT,
  )

  return {
    plugins: [
      vue(),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: false,
      }),
    ],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: devServerPort,
      proxy: {
        '/api': {
          target: backend,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: '../sprintcycle/dashboard/static',
      emptyOutDir: true,
      chunkSizeWarningLimit: 950,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('element-plus')) return 'el'
              if (id.includes('vue') || id.includes('@vue')) return 'vue'
              if (id.includes('pinia')) return 'pinia'
              if (id.includes('vue-router')) return 'vue-router'
              if (id.includes('axios')) return 'axios'
            }
          },
        },
      },
    },
  }
})
