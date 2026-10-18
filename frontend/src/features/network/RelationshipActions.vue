<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhCheck, PhUserPlus, PhPlus, PhHourglassMedium } from '@phosphor-icons/vue'
import { network, type Relationship } from '@/api/network'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ username: string }>()
const rel = ref<Relationship | null>(null)
const busy = ref(false)
const error = ref('')

watch(
  () => props.username,
  async (u) => (rel.value = await network.relationship(u)),
  { immediate: true },
)

async function run(action: () => Promise<unknown>) {
  busy.value = true
  error.value = ''
  try {
    await action()
    rel.value = await network.relationship(props.username)
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Something went wrong.') : 'Network error.'
  } finally {
    busy.value = false
  }
}

const stats = computed(() =>
  rel.value
    ? [
        { label: 'followers', value: rel.value.followers },
        { label: 'following', value: rel.value.following_count },
        { label: 'connections', value: rel.value.connections },
      ]
    : [],
)

const toggleFollow = () =>
  run(() => (rel.value?.following ? network.unfollow(props.username) : network.follow(props.username)))
const connect = () => run(() => network.connect(props.username))
const accept = () => run(() => network.accept(rel.value!.connection!.id))
const withdraw = () => run(() => network.remove(rel.value!.connection!.id))
</script>

<template>
  <div v-if="rel" class="grid gap-3">
    <dl class="flex flex-wrap gap-x-5 gap-y-1 text-sm">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="flex flex-row-reverse items-baseline justify-end gap-1"
      >
        <dt class="text-muted">{{ stat.label }}</dt>
        <dd class="font-semibold text-ink">{{ stat.value }}</dd>
      </div>
    </dl>
    <div class="flex flex-wrap items-center gap-2">
      <Button v-if="!rel.connection" size="sm" :loading="busy" @click="connect">
        <PhUserPlus :size="18" weight="light" /> Connect
      </Button>
      <Button
        v-else-if="rel.connection.status === 'pending' && rel.connection.direction === 'incoming'"
        size="sm"
        :loading="busy"
        @click="accept"
      >
        <PhCheck :size="18" weight="light" /> Accept request
      </Button>
      <Button
        v-else-if="rel.connection.status === 'pending'"
        variant="secondary"
        size="sm"
        :loading="busy"
        title="Withdraw your request"
        @click="withdraw"
      >
        <PhHourglassMedium :size="18" weight="light" /> Pending
      </Button>
      <span v-else class="inline-flex h-9 items-center gap-1.5 px-1 text-sm text-accent">
        <PhCheck :size="18" weight="light" /> Connected
      </span>
      <Button
        :variant="rel.following ? 'secondary' : 'ghost'"
        size="sm"
        :disabled="busy"
        :aria-pressed="rel.following"
        @click="toggleFollow"
      >
        <PhCheck v-if="rel.following" :size="18" weight="light" />
        <PhPlus v-else :size="18" weight="light" />
        {{ rel.following ? 'Following' : 'Follow' }}
      </Button>
      <span v-if="rel.followed_by" class="font-mono text-xs text-muted">follows you</span>
    </div>
    <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
  </div>
</template>
