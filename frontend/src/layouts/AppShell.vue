<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  PhHouse,
  PhSignOut,
  PhUserCircle,
  PhList,
  PhX,
  PhBooks,
  PhGraduationCap,
  PhChalkboardTeacher,
  PhUsersThree,
  PhUsersFour,
  PhCalendarBlank,
  PhBriefcase,
  PhChatsCircle,
  PhWifiSlash,
} from '@phosphor-icons/vue'
import BrandMark from '@/components/BrandMark.vue'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'
import Avatar from '@/components/ui/Avatar.vue'
import { useSessionStore } from '@/stores/session'
import { useNotificationsStore } from '@/stores/notifications'
import { useMessagesStore } from '@/stores/messages'
import { useOnline } from '@/lib/offline'
import NotificationBell from '@/features/notifications/NotificationBell.vue'
import NotificationToasts from '@/features/notifications/NotificationToasts.vue'

const session = useSessionStore()
const router = useRouter()
const route = useRoute()
const navOpen = ref(false)
const online = useOnline()

// The shell only renders for a signed-in user, so its lifetime is the live connection's.
const notifications = useNotificationsStore()
const messages = useMessagesStore()
void notifications.start()
void messages.start()
onUnmounted(() => {
  notifications.stop()
  messages.stop()
})

const items = computed(() => [
  { to: { name: 'home' }, label: 'Home', icon: PhHouse, exact: true, also: ['post'] },
  { to: { name: 'courses' }, label: 'Courses', icon: PhBooks, also: ['course', 'lesson'] },
  { to: { name: 'my-learning' }, label: 'My learning', icon: PhGraduationCap },
  { to: { name: 'network' }, label: 'Network', icon: PhUsersThree },
  { to: { name: 'messages' }, label: 'Messages', icon: PhChatsCircle, also: ['conversation'], badge: true },
  { to: { name: 'groups' }, label: 'Groups', icon: PhUsersFour, also: ['group'] },
  { to: { name: 'events' }, label: 'Events', icon: PhCalendarBlank, also: ['event'] },
  {
    to: { name: 'jobs' },
    label: 'Jobs',
    icon: PhBriefcase,
    also: ['job', 'job-applications', 'applications', 'companies', 'company'],
  },
  ...(['instructor', 'admin'].includes(session.user?.role ?? '')
    ? [
        {
          to: { name: 'teach' },
          label: 'Teaching',
          icon: PhChalkboardTeacher,
          also: ['course-new', 'course-editor'],
        },
      ]
    : []),
  { to: { name: 'my-profile' }, label: 'My profile', icon: PhUserCircle },
])

async function signOut() {
  await session.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-dvh bg-page lg:grid lg:grid-cols-[240px_1fr]">
    <aside
      class="fixed inset-y-0 left-0 z-20 flex w-64 -translate-x-full flex-col gap-6 border-r border-line bg-surface px-4 py-5 transition-transform duration-base ease-out lg:static lg:w-auto lg:translate-x-0"
      :class="navOpen && 'translate-x-0 shadow-pop'"
    >
      <div class="flex items-center justify-between">
        <BrandMark />
        <button
          type="button"
          class="grid size-9 place-items-center rounded-md text-muted lg:hidden"
          aria-label="Close menu"
          @click="navOpen = false"
        >
          <PhX :size="20" weight="light" />
        </button>
      </div>
      <nav class="grid gap-1" aria-label="Main">
        <RouterLink
          v-for="item in items"
          :key="item.label"
          :to="item.to"
          class="flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted transition-colors duration-quick hover:bg-surface-2 hover:text-ink"
          :active-class="
            item.exact ? '' : 'bg-accent-soft text-accent hover:bg-accent-soft hover:text-accent'
          "
          exact-active-class="bg-accent-soft text-accent hover:bg-accent-soft hover:text-accent"
          :class="item.also?.includes(String(route.name)) && 'bg-accent-soft text-accent'"
          @click="navOpen = false"
        >
          <component :is="item.icon" :size="20" weight="light" />
          <span class="flex-1">{{ item.label }}</span>
          <span
            v-if="'badge' in item && messages.unread"
            class="grid h-5 min-w-5 place-items-center rounded-full bg-accent px-1.5 font-mono text-[11px] text-accent-ink"
            :aria-label="`${messages.unread} unread`"
            >{{ messages.unread > 99 ? '99+' : messages.unread }}</span
          >
        </RouterLink>
      </nav>
      <div class="mt-auto grid gap-2 border-t border-line pt-4">
        <RouterLink
          :to="{ name: 'my-profile' }"
          class="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-surface-2"
        >
          <Avatar :name="session.displayName" size="sm" />
          <span class="min-w-0">
            <span class="block truncate text-sm font-medium text-ink">{{ session.displayName }}</span>
            <span class="block truncate font-mono text-xs text-muted">@{{ session.user?.username }}</span>
          </span>
        </RouterLink>
        <button
          type="button"
          class="flex h-10 cursor-pointer items-center gap-3 rounded-md px-3 text-sm text-muted hover:bg-surface-2 hover:text-ink"
          @click="signOut"
        >
          <PhSignOut :size="20" weight="light" /> Sign out
        </button>
      </div>
    </aside>
    <div v-if="navOpen" class="fixed inset-0 z-10 bg-ink/30 lg:hidden" @click="navOpen = false" />

    <div class="min-w-0">
      <header
        class="sticky top-0 z-[5] flex h-14 items-center justify-between border-b border-line bg-page/80 px-4 backdrop-blur sm:px-6"
      >
        <button
          type="button"
          class="grid size-10 place-items-center rounded-md text-muted lg:hidden"
          aria-label="Open menu"
          @click="navOpen = true"
        >
          <PhList :size="22" weight="light" />
        </button>
        <span class="hidden lg:block" />
        <div class="flex items-center gap-1">
          <NotificationBell />
          <ThemeToggle />
        </div>
      </header>
      <p
        v-if="!online"
        role="status"
        class="flex items-center justify-center gap-2 border-b border-line bg-surface-2 px-4 py-2 text-center text-sm text-ink"
      >
        <PhWifiSlash :size="18" weight="light" aria-hidden="true" />
        You are offline. Lessons you opened before are still readable; changes need a connection.
      </p>
      <main class="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        <RouterView v-slot="{ Component }">
          <div :key="$route.path" class="animate-page">
            <component :is="Component" />
          </div>
        </RouterView>
      </main>
    </div>
    <NotificationToasts />
  </div>
</template>
