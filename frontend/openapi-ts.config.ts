import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "http://localhost:9003/openapi.json",
  output: {
    path: "src/client",
    postProcess: ["biome:check"],
  },
  plugins: [
    { name: "@hey-api/client-axios", throwOnError: true },
    "@hey-api/typescript",
    "@hey-api/sdk",
  ],
})
