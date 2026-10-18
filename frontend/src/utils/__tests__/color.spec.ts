import { describe, expect, it } from "vitest"

import { contrastColor, findUrl } from "@/utils/color.ts"

describe("contrastColor", () => {
  it("dark text on light background", () => {
    expect(contrastColor("#ffffff")).toBe("#222")
    expect(contrastColor("#0f0")).toBe("#222")
  })

  it("light text on dark background", () => {
    expect(contrastColor("#000000")).toBe("#fff")
    expect(contrastColor("#1500ff")).toBe("#fff")
  })
})

describe("findUrl", () => {
  it("finds first http(s) url", () => {
    expect(findUrl("see https://a.b/c?d=1 and http://x.y")).toBe("https://a.b/c?d=1")
  })

  it("ignores other schemes", () => {
    expect(findUrl("javascript:alert(1)")).toBeNull()
  })
})
