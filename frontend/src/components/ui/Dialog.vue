<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhX } from '@phosphor-icons/vue'

const props = defineProps<{ title: string }>()
const open = defineModel<boolean>('open', { default: false })
const el = ref<HTMLDialogElement>()

watch(open, (v) => (v ? el.value?.showModal() : el.value?.close()))
</script>

<template>
  <dialog
    ref="el"
    class="m-auto w-[min(92vw,32rem)] rounded-lg bg-surface p-0 text-ink shadow-pop ring-1 ring-line backdrop:bg-ink/40 backdrop:backdrop-blur-[2px]"
    @close="open = false"
    @click.self="open = false"
  >
    <div class="flex items-center justify-between border-b border-line px-5 py-4">
      <h2 class="text-lg font-semibold">{{ props.title }}</h2>
      <button
        type="button"
        class="grid size-9 cursor-pointer place-items-center rounded-md text-muted hover:bg-surface-2"
        aria-label="Close"
        @click="open = false"
      >
        <PhX :size="18" weight="light" />
      </button>
    </div>
    <div class="px-5 py-4"><slot /></div>
  </dialog>
</template>
