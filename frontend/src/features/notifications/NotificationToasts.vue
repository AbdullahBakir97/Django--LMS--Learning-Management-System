<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhX } from '@phosphor-icons/vue'
import { useNotificationsStore } from '@/stores/notifications'
import type { AppNotification } from '@/api/notifications'
import { kindIcon } from './format'

const store = useNotificationsStore()
const router = useRouter()

function open(n: AppNotification) {
  store.dismissToast(n.id)
  void store.markRead(n)
  if (n.url) router.push(n.url)
}
</script>

<template>
  <div
    class="pointer-events-none fixed inset-x-4 bottom-4 z-30 grid justify-items-end gap-2 sm:left-auto sm:w-96"
    aria-live="polite"
    aria-relevant="additions"
  >
    <TransitionGroup
      enter-from-class="translate-y-2 opacity-0"
      leave-to-class="opacity-0"
      enter-active-class="transition duration-base ease-out"
      leave-active-class="transition duration-quick"
    >
      <div
        v-for="n in store.toasts"
        :key="n.id"
        class="pointer-events-auto flex w-full items-start gap-3 rounded-lg border border-line bg-surface p-3 shadow-pop"
      >
        <span class="grid size-9 shrink-0 place-items-center rounded-md bg-accent-soft text-accent">
          <component :is="kindIcon[n.kind]" :size="20" weight="light" />
        </span>
        <button type="button" class="min-w-0 flex-1 cursor-pointer text-left" @click="open(n)">
          <span class="block text-sm font-medium text-ink">{{ n.title }}</span>
          <span v-if="n.body" class="mt-0.5 block text-sm text-muted">{{ n.body }}</span>
        </button>
        <button
          type="button"
          class="grid size-8 shrink-0 cursor-pointer place-items-center rounded-md text-muted hover:bg-surface-2 hover:text-ink"
          aria-label="Dismiss"
          @click="store.dismissToast(n.id)"
        >
          <PhX :size="16" weight="light" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
