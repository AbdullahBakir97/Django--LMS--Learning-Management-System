<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { community, type Post } from '@/api/community'
import Alert from '@/components/ui/Alert.vue'
import PostCard from '@/features/community/PostCard.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const post = ref<Post | null>(null)
const missing = ref(false)

watch(
  () => props.id,
  async (id) => {
    missing.value = false
    post.value = await community.post(Number(id)).catch(() => ((missing.value = true), null))
  },
  { immediate: true },
)
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <h1 class="sr-only">Post</h1>
    <Alert v-if="missing" tone="danger"
      >This post is not available. It may have been deleted, or it is in a private group.</Alert
    >
    <PostCard
      v-else-if="post"
      :post="post"
      open-comments
      @update="Object.assign(post!, $event)"
      @removed="router.push({ name: 'home' })"
    />
  </div>
</template>
