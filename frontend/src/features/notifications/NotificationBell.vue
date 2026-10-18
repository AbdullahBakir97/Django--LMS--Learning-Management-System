<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { PhBell } from '@phosphor-icons/vue'
import { useNotificationsStore } from '@/stores/notifications'

const store = useNotificationsStore()
const label = computed(() => (store.unread ? `Notifications, ${store.unread} unread` : 'Notifications'))
</script>

<template>
  <RouterLink
    :to="{ name: 'notifications' }"
    class="relative grid size-10 place-items-center rounded-md text-muted transition-colors duration-quick hover:bg-surface-2 hover:text-ink"
    active-class="text-accent"
    :aria-label="label"
    :title="label"
  >
    <PhBell :size="22" weight="light" />
    <span
      v-if="store.unread"
      class="absolute top-1 right-1 grid h-4 min-w-4 place-items-center rounded-full bg-accent px-1 font-mono text-[10px] leading-none font-medium text-accent-ink"
      aria-hidden="true"
      >{{ store.unread > 99 ? '99+' : store.unread }}</span
    >
  </RouterLink>
</template>
