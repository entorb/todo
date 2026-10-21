import { fileURLToPath, URL } from "node:url"

import { quasar, transformAssetUrls } from "@quasar/vite-plugin"
import legacy from "@vitejs/plugin-legacy"
import Vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"
import { VitePWA } from "vite-plugin-pwa"
import vueDevTools from "vite-plugin-vue-devtools"

const BASE = "/todo/"
const TARGETS = ["iOS >= 15", "Safari >= 15", "Chrome >= 87", "Firefox >= 78", "Edge >= 88"]

// https://vite.dev/config/
export default defineConfig({
  // important when deploying not into the webserver root dir
  base: BASE,
  build: {
    assetsInlineLimit: 4096,
    chunkSizeWarningLimit: 500,
    cssCodeSplit: true,
    minify: "esbuild",
    sourcemap: false,
    // target is handled by @vitejs/plugin-legacy below
  },
  optimizeDeps: {
    include: ["vue", "vue-router", "quasar"],
  },
  plugins: [
    Vue({
      template: { transformAssetUrls },
    }),
    quasar({
      sassVariables: fileURLToPath(new URL("./src/styles/quasar-variables.sass", import.meta.url)),
    }),
    vueDevTools(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "apple-touch-icon.png"],
      manifest: {
        name: "Todo",
        short_name: "Todo",
        description: "Kanban todo boards",
        theme_color: "#37474f",
        background_color: "#667eea",
        display: "standalone",
        scope: BASE,
        start_url: BASE,
        icons: [
          { src: `${BASE}favicon.svg`, sizes: "any", type: "image/svg+xml", purpose: "any" },
          { src: `${BASE}apple-touch-icon.png`, sizes: "180x180", type: "image/png" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff,woff2}"],
      },
    }),
    // Support iOS 15+ (Safari 15+)
    legacy({
      modernTargets: TARGETS,
      targets: TARGETS,
      modernPolyfills: true,
      renderLegacyChunks: false,
    }),
  ],
  define: { "process.env": {} },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    extensions: [".js", ".json", ".jsx", ".mjs", ".ts", ".tsx", ".vue"],
  },
  preview: { host: true, port: 4173, strictPort: true },
  server: { host: true, port: 5173, strictPort: true },
})
