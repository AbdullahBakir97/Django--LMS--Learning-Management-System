<script setup lang="ts">
import type { PostImage } from '@/api/community'

defineProps<{ images: PostImage[] }>()
</script>

<template>
  <a
    v-if="images.length === 1"
    :href="images[0]!.image"
    target="_blank"
    rel="noopener"
    class="block overflow-hidden rounded-md bg-surface-2"
  >
    <img
      :src="images[0]!.image"
      :width="images[0]!.width"
      :height="images[0]!.height"
      alt="Image 1 of 1"
      loading="lazy"
      class="max-h-[28rem] w-full object-cover"
      :style="{ aspectRatio: `${images[0]!.width} / ${images[0]!.height}` }"
    />
  </a>
  <!-- Several images share one fixed-height grid, so the feed keeps its rhythm. -->
  <div
    v-else-if="images.length"
    class="grid h-64 grid-cols-2 gap-1 overflow-hidden rounded-md sm:h-80"
    :class="images.length > 2 ? 'grid-rows-2' : 'grid-rows-1'"
  >
    <a
      v-for="(img, i) in images"
      :key="img.image"
      :href="img.image"
      target="_blank"
      rel="noopener"
      class="block min-h-0 bg-surface-2"
      :class="images.length === 3 && i === 0 ? 'row-span-2' : ''"
    >
      <img
        :src="img.image"
        :alt="`Image ${i + 1} of ${images.length}`"
        loading="lazy"
        class="h-full w-full object-cover"
      />
    </a>
  </div>
</template>
