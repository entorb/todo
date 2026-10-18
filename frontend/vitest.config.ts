import { fileURLToPath } from "node:url"

import { quasar, transformAssetUrls } from "@quasar/vite-plugin"
import vue from "@vitejs/plugin-vue"
import { configDefaults, defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [vue({ template: { transformAssetUrls } }), quasar()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    globals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      include: ["src/**/*.{ts,vue}"],
      exclude: [
        "src/client/**",
        "**/*.spec.ts",
        "src/__tests__/**",
        "src/main.ts",
        "src/plugins/**",
        "src/utils/clipboard.ts",
      ],
    },
    environment: "jsdom",
    exclude: [...configDefaults.exclude, "e2e/**"],
    root: fileURLToPath(new URL("./", import.meta.url)),
    setupFiles: ["./src/__tests__/setup.ts"],
  },
})
