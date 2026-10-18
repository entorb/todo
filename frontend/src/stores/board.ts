import { defineStore } from "pinia"
import { Notify } from "quasar"
import { computed, ref } from "vue"

import {
  type BoardPublic,
  type BoardSummary,
  bulkUpdateCards,
  type CardBulkUpdate,
  type CardPublic,
  type CardUpdate,
  type ColumnPublic,
  copyCard,
  createCard,
  createColumn,
  deleteCard,
  deleteColumn,
  getBoard,
  type LabelPublic,
  listBoards,
  listLabels,
  moveCard,
  reorderColumns,
  sortBoard,
  updateCard,
  updateColumn,
} from "@/client/index.ts"
import { errorMessage } from "@/services/apiClient.ts"

export const useBoardStore = defineStore("board", () => {
  const boards = ref<BoardSummary[]>([])
  const board = ref<BoardPublic | null>(null)
  const labels = ref<LabelPublic[]>([])
  const bulkMode = ref(false)
  const selected = ref(new Set<number>())

  const labelById = computed(() => new Map(labels.value.map((lb) => [lb.id, lb])))

  async function loadBoards(): Promise<void> {
    boards.value = (await listBoards()).data
  }

  async function loadLabels(): Promise<void> {
    labels.value = (await listLabels()).data
  }

  async function loadBoard(key: string, touch = false): Promise<void> {
    board.value = (await getBoard({ path: { key }, query: { touch } })).data
  }

  /** Reload current board from server. */
  async function refresh(): Promise<void> {
    if (board.value != null) {
      await loadBoard(board.value.key)
    }
  }

  /** Run API call, show error as notify, reload board. Returns success. */
  async function run(action: () => Promise<unknown>): Promise<boolean> {
    let ok = true
    try {
      await action()
    } catch (err) {
      ok = false
      Notify.create({ type: "warning", message: errorMessage(err) })
    }
    await refresh()
    return ok
  }

  // columns

  async function addColumn(boardId: number) {
    return await run(async () => createColumn({ body: { board_id: boardId } }))
  }

  async function renameColumn(columnId: number, name: string) {
    return await run(async () => updateColumn({ path: { column_id: columnId }, body: { name } }))
  }

  async function removeColumn(columnId: number) {
    return await run(async () => deleteColumn({ path: { column_id: columnId } }))
  }

  async function saveColumnOrder(boardId: number, ids: number[]) {
    return await run(async () => reorderColumns({ path: { board_id: boardId }, body: { ids } }))
  }

  // cards

  /** Local (optimistic) card order of a column, used by drag & drop. */
  function setCards(columnId: number, cards: CardPublic[]): void {
    const column = board.value?.columns.find((c) => c.id === columnId)
    if (column != null) column.cards = cards
  }

  /** Local (optimistic) column order, used by drag & drop. */
  function setColumns(columns: ColumnPublic[]): void {
    if (board.value != null) board.value.columns = columns
  }

  async function addCard(columnId: number, title: string) {
    return await run(async () => createCard({ body: { column_id: columnId, title } }))
  }

  async function patchCard(cardId: number, body: CardUpdate) {
    return await run(async () => updateCard({ path: { card_id: cardId }, body }))
  }

  async function removeCard(cardId: number) {
    return await run(async () => deleteCard({ path: { card_id: cardId } }))
  }

  async function moveCardTo(cardId: number, columnId: number, position?: number) {
    return await run(async () =>
      moveCard({ path: { card_id: cardId }, body: { column_id: columnId, position } }),
    )
  }

  async function copyCardTo(cardId: number, columnId: number) {
    return await run(async () =>
      copyCard({ path: { card_id: cardId }, body: { column_id: columnId } }),
    )
  }

  async function sortCards(by: "prio" | "date") {
    const boardId = board.value?.id
    if (boardId == null) return false
    return await run(async () => sortBoard({ path: { board_id: boardId }, query: { by } }))
  }

  // bulk

  function toggleSelected(cardId: number): void {
    if (selected.value.has(cardId)) {
      selected.value.delete(cardId)
    } else {
      selected.value.add(cardId)
    }
  }

  function toggleBulk(): void {
    if (bulkMode.value) {
      exitBulk()
    } else {
      bulkMode.value = true
    }
  }

  function exitBulk(): void {
    bulkMode.value = false
    selected.value.clear()
  }

  /** Apply update to all selected cards, then leave bulk mode. */
  async function bulkUpdate(body: Omit<CardBulkUpdate, "ids">): Promise<void> {
    const ids = [...selected.value]
    exitBulk()
    if (ids.length === 0) return
    await run(async () => bulkUpdateCards({ body: { ids, ...body } }))
  }

  return {
    boards,
    board,
    labels,
    labelById,
    bulkMode,
    selected,
    loadBoards,
    loadLabels,
    loadBoard,
    refresh,
    run,
    addColumn,
    renameColumn,
    removeColumn,
    saveColumnOrder,
    setCards,
    setColumns,
    addCard,
    patchCard,
    removeCard,
    moveCardTo,
    copyCardTo,
    sortCards,
    toggleSelected,
    toggleBulk,
    exitBulk,
    bulkUpdate,
  }
})
