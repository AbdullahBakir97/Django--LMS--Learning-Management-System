<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { PhBooks, PhUsers } from '@phosphor-icons/vue'
import { price, type CourseSummary } from '@/api/learning'
import Tag from '@/components/ui/Tag.vue'

defineProps<{ course: CourseSummary }>()
</script>

<template>
  <RouterLink
    :to="{ name: 'course', params: { slug: course.slug } }"
    class="group flex h-full flex-col rounded-lg bg-surface p-5 shadow-card ring-1 ring-line transition-[box-shadow,transform] duration-base ease-out hover:-translate-y-0.5 hover:shadow-pop"
  >
    <div class="flex items-center gap-2">
      <Tag>{{ course.level }}</Tag>
      <Tag v-if="course.status === 'draft'">draft</Tag>
      <span class="ml-auto font-mono text-sm" :class="course.price_cents ? 'text-ink' : 'text-muted'">{{
        price(course)
      }}</span>
    </div>
    <h3 class="mt-3 text-lg font-semibold group-hover:text-accent">{{ course.title }}</h3>
    <p class="mt-1 line-clamp-2 text-sm text-muted">{{ course.summary || 'No summary yet.' }}</p>
    <p class="mt-auto flex items-center gap-4 pt-4 font-mono text-xs text-muted">
      <span class="inline-flex items-center gap-1"
        ><PhBooks :size="14" weight="light" />{{ course.lesson_count }} lessons</span
      >
      <span class="inline-flex items-center gap-1"
        ><PhUsers :size="14" weight="light" />{{ course.enrollment_count }}</span
      >
      <span class="ml-auto truncate">{{ course.instructor.first_name || course.instructor.username }}</span>
    </p>
  </RouterLink>
</template>
