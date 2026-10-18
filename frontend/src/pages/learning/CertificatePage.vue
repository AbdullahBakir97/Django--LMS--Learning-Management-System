<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { PhSealCheck, PhDownloadSimple } from '@phosphor-icons/vue'
import { learning, type CertificateRecord } from '@/api/learning'
import BrandMark from '@/components/BrandMark.vue'
import Alert from '@/components/ui/Alert.vue'

const props = defineProps<{ code: string }>()
const record = ref<CertificateRecord | null>(null)
const failed = ref(false)
const date = new Intl.DateTimeFormat(undefined, { dateStyle: 'long' })

onMounted(async () => {
  try {
    record.value = await learning.certificate(props.code)
  } catch {
    failed.value = true
  }
})
</script>

<template>
  <main class="grid min-h-dvh place-items-center bg-page px-4 py-10">
    <div class="w-full max-w-xl">
      <BrandMark />
      <Alert v-if="failed" tone="danger" class="mt-8">No certificate matches this code.</Alert>
      <section
        v-else-if="record"
        class="mt-8 rounded-lg bg-surface p-8 text-center shadow-card ring-1 ring-line"
      >
        <PhSealCheck :size="40" weight="light" class="mx-auto text-accent" />
        <p class="mt-4 font-mono text-xs tracking-widest text-muted uppercase">Verified certificate</p>
        <h1 class="mt-3 text-3xl font-semibold">{{ record.student }}</h1>
        <p class="mt-2 text-muted">completed</p>
        <p class="mt-1 font-display text-xl font-semibold">{{ record.course }}</p>
        <p class="mt-4 text-sm text-muted">
          Instructor {{ record.instructor }} · {{ date.format(new Date(record.completed_at)) }}
        </p>
        <p class="mt-6 font-mono text-xs break-all text-muted">{{ record.code }}</p>
        <a
          v-if="record.pdf"
          :href="record.pdf"
          class="mt-6 inline-flex items-center gap-2 text-sm text-accent hover:underline"
          target="_blank"
          rel="noopener"
        >
          <PhDownloadSimple :size="16" weight="light" /> Download PDF
        </a>
      </section>
    </div>
  </main>
</template>
