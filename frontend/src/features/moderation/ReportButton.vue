<script setup lang="ts">
import { ref } from 'vue'
import { PhFlag } from '@phosphor-icons/vue'
import { moderation, REASONS, type ReportKind, type ReportReason } from '@/api/moderation'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import Dialog from '@/components/ui/Dialog.vue'

const props = defineProps<{ kind: ReportKind; objectId: number; label?: string; compact?: boolean }>()
const open = ref(false)
const reason = ref<ReportReason | null>(null)
const details = ref('')
const done = ref(false)
const error = ref('')
const busy = ref(false)
const what = { post: 'post', comment: 'comment', user: 'person' }[props.kind]

async function send() {
  if (!reason.value) return
  busy.value = true
  error.value = ''
  try {
    await moderation.report(props.kind, props.objectId, reason.value, details.value.trim())
    done.value = true
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not send the report.') : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <button
    type="button"
    class="inline-flex cursor-pointer items-center gap-1 rounded-md px-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
    :class="compact ? 'h-7' : 'h-8'"
    @click="open = true"
  >
    <PhFlag :size="compact ? 14 : 16" weight="light" aria-hidden="true" />
    {{ label ?? 'Report' }}
  </button>
  <Dialog v-model:open="open" :title="`Report this ${what}`">
    <div v-if="open && done" class="grid gap-3" role="status">
      <p>Thanks. A moderator will look at it, and you will hear back when they have.</p>
      <Button class="w-fit" variant="secondary" @click="open = false">Close</Button>
    </div>
    <form v-else-if="open" class="grid gap-4" @submit.prevent="send">
      <fieldset class="grid gap-2">
        <legend class="mb-2 text-sm font-medium">What is wrong with it?</legend>
        <label v-for="r in REASONS" :key="r.value" class="flex cursor-pointer items-center gap-3 text-sm">
          <input
            v-model="reason"
            type="radio"
            name="reason"
            :value="r.value"
            class="size-4 accent-[var(--c-accent)]"
          />
          {{ r.label }}
        </label>
      </fieldset>
      <label class="grid gap-1.5 text-sm font-medium">
        Anything else a moderator should know (optional)
        <textarea
          v-model="details"
          rows="3"
          maxlength="1000"
          class="w-full resize-y rounded-md bg-page px-3 py-2 font-normal text-ink ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
        />
      </label>
      <p class="text-sm text-muted">The person you report is not told who reported them.</p>
      <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
      <Button type="submit" :disabled="!reason" :loading="busy">Send report</Button>
    </form>
  </Dialog>
</template>
