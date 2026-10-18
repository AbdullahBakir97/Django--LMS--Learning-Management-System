<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { network, type Person } from '@/api/network'
import { messaging, type Conversation } from '@/api/messaging'
import { ApiError } from '@/api/client'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'

const emit = defineEmits<{ started: [conversation: Conversation] }>()
const people = ref<Person[]>([])
const picked = ref<string[]>([])
const query = ref('')
const title = ref('')
const error = ref('')
const busy = ref(false)
const loaded = ref(false)

onMounted(async () => {
  try {
    people.value = (await network.connections()).results.map((c) => c.person)
  } catch {
    error.value = 'Could not load your connections.'
  }
  loaded.value = true
})
const shown = computed(() =>
  people.value.filter((p) => `${p.name} ${p.username}`.toLowerCase().includes(query.value.toLowerCase())),
)

async function start() {
  busy.value = true
  error.value = ''
  try {
    emit(
      'started',
      await messaging.start(picked.value, { title: picked.value.length > 1 ? title.value : '' }),
    )
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not start it.') : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="grid gap-4">
    <p class="text-sm text-muted">You can message people you are connected with.</p>
    <input
      v-model="query"
      type="search"
      placeholder="Search your connections"
      aria-label="Search your connections"
      class="h-10 rounded-md bg-page px-3 text-sm ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
    />
    <ul class="grid max-h-72 gap-1 overflow-y-auto">
      <li v-for="p in shown" :key="p.username">
        <label class="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 hover:bg-surface-2">
          <input
            v-model="picked"
            type="checkbox"
            :value="p.username"
            class="size-4 accent-[var(--c-accent)]"
          />
          <Avatar :name="p.name" :src="p.avatar" size="sm" />
          <span class="min-w-0">
            <span class="block truncate text-sm font-medium">{{ p.name }}</span>
            <span class="block truncate text-xs text-muted">{{ p.headline || `@${p.username}` }}</span>
          </span>
        </label>
      </li>
    </ul>
    <p v-if="loaded && !people.length" class="text-sm text-muted">
      No connections yet. Connect with people from the Network page.
    </p>
    <TextField v-if="picked.length > 1" v-model="title" label="Group name" hint="Optional" />
    <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
    <div class="flex justify-end">
      <Button :disabled="!picked.length" :loading="busy" @click="start">
        {{ picked.length > 1 ? `Start group (${picked.length})` : 'Start conversation' }}
      </Button>
    </div>
  </div>
</template>
