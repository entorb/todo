# Frontend - Coding Guidelines

Vue 3 + Quasar + Pinia + TypeScript, Vite base `/todo/`. Run commands from `frontend/` (`pnpm exec ...`), or via `../scripts/*.sh`. Biome handles formatting, no need for manual code formatting. This guide covers architectural decisions.

## Layout

| Path | Content |
| ---- | ------- |
| `src/client/` | generated API client (`scripts/gen_api_for_vue.sh`) — DO NOT edit |
| `src/services/apiClient.ts` | client config, `tokenManager` (localStorage), 401 handler, `errorMessage()` |
| `src/config/env.ts` | validated env (`VITE_API_BASE_URL`) |
| `src/router/index.ts` | routes `/` (boards), `/b/:key` (board), `/login`; auth guard |
| `src/stores/auth.ts` | login / logout, user from JWT |
| `src/stores/board.ts` | boards, current board, labels, bulk selection; all board mutations via `run()` |
| `src/views/` | `BoardListView`, `BoardView`, `LoginView` |
| `src/components/` | `BoardColumn`, `TodoCard`, `BulkBar`; drag & drop via `vue-draggable-plus` |
| `src/components/dialogs/` | Quasar Dialog plugin components |
| `src/utils/` | `color`, `jwt`, `clipboard` (pure, unit tested) |
| `e2e/` | Playwright, `helpers.ts` `login(page)`, DB seeded in `global-setup.ts` |

## API calls

```typescript
// generated fn, throws on error (axios), response in .data
const { data } = await getBoard({ path: { key }, query: { touch } })

// board mutation: notify on error + reload board, returns success
await store.run(async () => updateColumn({ path: { column_id: id }, body: { name } }))
```

## Dialogs

Open via `$q.dialog({ component: XyzDialog, componentProps })`. Component uses `useDialogPluginComponent()` and declares `defineEmits<{ ok: [payload?: unknown]; hide: [] }>()`. See `components/dialogs/DeleteCardsDialog.vue`.

## Tests

- Unit: `**/__tests__/*.spec.ts` (vitest, jsdom, `src/__tests__/setup.ts` mocks localStorage).
- Store tests mock `@/client/index.ts` and `quasar` (`Notify`) with `vi.mock`, see `stores/__tests__/board.spec.ts`.
- Component tests: `vi.mock("@/client/index.ts")` + helpers in `src/__tests__/mount.ts`: `mountApp` (Quasar, pinia, memory router, QDialog/QPage stubbed inline), `seedBoard`, `dialogOk` (stub `$q.dialog`), `button`, `menuItem` (QMenu is teleported to body).
- E2E: `scripts/run_e2e.sh` starts BE (`sqlite-e2e.db`) + Vite, login secret `test`.

---

Modern Vue 3 + TypeScript best practices.

## Store Architecture (Pinia)

**Direct mutations, not setters:**

```typescript
// ✅ DO
store.inputText = 'new value'

// ❌ DON'T
function setInputText(text: string) {
  inputText.value = text
}
```

**Return minimal interface:**

```typescript
export const useTextStore = defineStore('text', () => {
  const inputText = ref('')
  const outputText = ref('')

  function clearOutput() {
    outputText.value = ''
    error.value = null
  }

  return { inputText, outputText, clearOutput }
})
```

## Error Handling

**Minimal, user-facing only:**

```typescript
// ✅ DO
try {
  const { data } = await improveText({ body: { text } })
  textStore.outputText = data.text_ai
} catch (err) {
  textStore.error = errorMessage(err)
}

// ❌ DON'T
console.error('Failed:', err) // No logging in catch
```

## Nullability

**Use modern operators:**

```typescript
// ✅ DO
if (token == null) return ''
options.onEscape?.()
const value = model?.trim() ?? ''

// ❌ DON'T
if (!token || token.length === 0) return '' // Over-defensive
```

## Composables

**One responsibility, focused:**

```typescript
// ✅ DO
export function useTextProcessing() {
  const textStore = useTextStore()
  const isProcessing = ref(false)

  async function processText() {
    /* ... */
  }

  return { isProcessing, processText }
}

// ❌ DON'T
function transferAiTextToInput() {
  // Too simple for helper
  textStore.inputText = textStore.outputText
}
```

## Components

**Keep views dumb, extract logic:**

```typescript
// ✅ DO
<script setup lang="ts">
const textStore = useTextStore()
const { isProcessing, processText } = useTextProcessing()

const canSubmit = computed(() => !!textStore.inputText)
</script>

// ❌ DON'T
const username = ref('')  // Unused state
async function handleLogin() {
  console.error('Login failed')  // No logging
}
```

## Code Quality

**Keep functions simple:**

- Cognitive complexity < 20
- Extract repeated strings (4+ occurrences) to constants
- Types use PascalCase, no "I" prefix

**Accessibility:**

- Buttons need `type="button"` or `type="submit"`
- Icon-only buttons need `aria-label`
- Form inputs need labels

## Key Principles

1. **Direct is better** - `store.value = x` not `store.setValue(x)`
2. **Catch only where you handle** - no empty catches
3. **Modern TypeScript** - use `==`, `?.`, `??`
4. **Views are dumb** - logic in stores/composables
5. **One way to do it** - consistency over preference

## Checklist

- [ ] Direct store mutations, no setters
- [ ] No console.error/warn in catch
- [ ] Use `??` and `?.` operators
- [ ] Error messages user-facing (English), via `errorMessage()` from `services/apiClient.ts`
- [ ] Composables focused (one responsibility)
- [ ] Views minimal, logic extracted
- [ ] Buttons have `type` attribute
- [ ] Icon buttons have `aria-label`
- [ ] API calls via generated `@/client/index.ts` (throws on error), never hand-written axios
- [ ] Board mutations via `useBoardStore().run()` (notify on error + reload)
- [ ] Dialogs: Quasar Dialog plugin + `useDialogPluginComponent`, see `components/dialogs/`
- [ ] No `v-html` (JWT in localStorage, XSS = token theft)
- [ ] Run `scripts/run_checks.sh` before commit
