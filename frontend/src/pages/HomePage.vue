<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { PhGraduationCap, PhUsersThree, PhBriefcase } from '@phosphor-icons/vue'
import Card from '@/components/ui/Card.vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const soon: { icon: unknown; title: string; text: string; to?: object }[] = [
  {
    icon: PhGraduationCap,
    title: 'Courses',
    text: 'Lessons, quizzes and a verifiable certificate at the end.',
    to: { name: 'courses' },
  },
  { icon: PhUsersThree, title: 'Network', text: 'Follow people, connect, and see what they share.' },
  { icon: PhBriefcase, title: 'Careers', text: 'Companies, job listings and applications.' },
]
</script>

<template>
  <h1 class="text-3xl font-semibold">Hello, {{ session.user?.first_name || session.user?.username }}</h1>
  <p class="mt-1 max-w-prose text-muted">
    Your account is live. Start with your profile so instructors and peers know who you are.
    <RouterLink class="text-accent hover:underline" :to="{ name: 'my-profile' }">Edit profile</RouterLink>
  </p>
  <div class="mt-8 grid gap-4 sm:grid-cols-3">
    <component :is="item.to ? RouterLink : 'div'" v-for="item in soon" :key="item.title" :to="item.to">
      <Card class="h-full p-5">
        <component :is="item.icon" :size="24" weight="light" class="text-accent" />
        <h2 class="mt-3 text-lg font-semibold">{{ item.title }}</h2>
        <p class="mt-1 text-sm text-muted">{{ item.text }}</p>
      </Card>
    </component>
  </div>
</template>
