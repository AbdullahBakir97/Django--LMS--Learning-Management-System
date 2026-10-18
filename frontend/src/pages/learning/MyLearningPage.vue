<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { learning, type EnrollmentItem } from '@/api/learning'
import Card from '@/components/ui/Card.vue'
import Tag from '@/components/ui/Tag.vue'

const items = ref<EnrollmentItem[] | null>(null)
onMounted(async () => (items.value = (await learning.myEnrollments()).results))
</script>

<template>
  <h1 class="text-3xl font-semibold">My learning</h1>
  <p class="mt-1 text-muted">Courses you are enrolled in.</p>
  <p v-if="items && !items.length" class="mt-10 text-muted">
    Nothing yet.
    <RouterLink class="text-accent hover:underline" :to="{ name: 'courses' }">Browse courses</RouterLink>
  </p>
  <ul v-else class="mt-6 grid gap-3">
    <li v-for="e in items ?? []" :key="e.id">
      <RouterLink :to="{ name: 'course', params: { slug: e.course.slug } }">
        <Card class="flex items-center gap-4 p-4 transition-shadow duration-base hover:shadow-pop">
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium">{{ e.course.title }}</p>
            <p class="truncate text-sm text-muted">{{ e.course.summary }}</p>
          </div>
          <Tag>{{ e.status === 'completed' ? 'completed' : 'in progress' }}</Tag>
        </Card>
      </RouterLink>
    </li>
  </ul>
</template>
