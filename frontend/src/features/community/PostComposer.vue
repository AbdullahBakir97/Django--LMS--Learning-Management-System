<script setup lang="ts">
import { onUnmounted, ref, useId } from 'vue'
import { PhImage, PhX } from '@phosphor-icons/vue'
import { community, type Group, type Post } from '@/api/community'
import { ApiError } from '@/api/client'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ groups?: Group[]; groupSlug?: string; placeholder?: string }>()
const emit = defineEmits<{ posted: [post: Post] }>()
const session = useSessionStore()
const body = ref('')
const where = ref(props.groupSlug ?? '')
const busy = ref(false)
const error = ref('')
const id = useId()

const MAX_IMAGES = 4
const images = ref<{ file: File; url: string }[]>([])
const picker = ref<HTMLInputElement>()

function pick(event: Event) {
  const files = [...((event.target as HTMLInputElement).files ?? [])]
  const room = MAX_IMAGES - images.value.length
  if (files.length > room) error.value = `Up to ${MAX_IMAGES} images per post.`
  for (const file of files.slice(0, room)) images.value.push({ file, url: URL.createObjectURL(file) })
  if (picker.value) picker.value.value = ''
}

function unpick(i: number) {
  URL.revokeObjectURL(images.value[i]!.url)
  images.value.splice(i, 1)
}
onUnmounted(() => images.value.forEach((img) => URL.revokeObjectURL(img.url)))

const empty = () => !body.value.trim() && !images.value.length

async function submit() {
  if (empty()) return
  busy.value = true
  error.value = ''
  try {
    const files = images.value.map((img) => img.file)
    emit('posted', await community.createPost(body.value.trim(), where.value || null, files))
    body.value = ''
    images.value.forEach((img) => URL.revokeObjectURL(img.url))
    images.value = []
  } catch (e) {
    error.value =
      e instanceof ApiError
        ? (e.field('body') ?? e.field('images') ?? e.nonField ?? 'Could not post.')
        : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="flex gap-3 rounded-lg bg-surface p-4 shadow-card ring-1 ring-line" @submit.prevent="submit">
    <Avatar :name="session.displayName" size="md" class="hidden sm:grid" />
    <div class="grid min-w-0 flex-1 gap-3">
      <label :for="id" class="sr-only">Write a post</label>
      <textarea
        :id="id"
        v-model="body"
        rows="3"
        maxlength="5000"
        :placeholder="placeholder ?? 'Share something you learned, a question, or a win'"
        class="w-full resize-y rounded-md bg-page px-3 py-2 text-sm text-ink ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
        @keydown.meta.enter="submit"
        @keydown.ctrl.enter="submit"
      />
      <ul v-if="images.length" class="grid grid-cols-4 gap-2" aria-label="Images to post">
        <li v-for="(img, i) in images" :key="img.url" class="relative">
          <img :src="img.url" alt="" class="aspect-square w-full rounded-md object-cover" />
          <button
            type="button"
            class="absolute top-1 right-1 grid size-7 cursor-pointer place-items-center rounded-full bg-ink/70 text-page"
            :aria-label="`Remove image ${i + 1}`"
            @click="unpick(i)"
          >
            <PhX :size="14" weight="bold" />
          </button>
        </li>
      </ul>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <select
          v-if="groups?.length && !groupSlug"
          v-model="where"
          aria-label="Where to post"
          class="h-9 max-w-full min-w-0 rounded-md bg-surface px-2 text-sm text-ink ring-1 ring-line-strong"
        >
          <option value="">Your profile</option>
          <option v-for="g in groups" :key="g.slug" :value="g.slug">{{ g.name }}</option>
        </select>
        <span v-else />
        <div class="flex items-center gap-2">
          <input
            :id="`${id}-images`"
            ref="picker"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            class="peer sr-only"
            :disabled="images.length >= MAX_IMAGES"
            @change="pick"
          />
          <label
            :for="`${id}-images`"
            class="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-md px-2.5 text-sm text-muted peer-focus-visible:ring-2 peer-focus-visible:ring-accent hover:bg-surface-2 hover:text-ink"
            :class="{ 'pointer-events-none opacity-50': images.length >= MAX_IMAGES }"
          >
            <PhImage :size="18" weight="light" /> Photo
          </label>
          <Button type="submit" size="sm" :disabled="empty()" :loading="busy">Post</Button>
        </div>
      </div>
      <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
    </div>
  </form>
</template>
