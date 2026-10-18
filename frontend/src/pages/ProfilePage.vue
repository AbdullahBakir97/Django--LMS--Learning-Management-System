<script setup lang="ts">
import { ref, watch } from 'vue'
import { profiles, type Profile } from '@/api/profiles'
import { ApiError } from '@/api/client'
import ProfileView from '@/features/profile/ProfileView.vue'
import Alert from '@/components/ui/Alert.vue'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ username: string }>()
const session = useSessionStore()
const profile = ref<Profile | null>(null)
const error = ref('')

async function load() {
  error.value = ''
  try {
    profile.value = await profiles.byUsername(props.username)
  } catch (e) {
    error.value =
      e instanceof ApiError && e.problem.status === 404
        ? 'No one with that username.'
        : 'Could not load this profile.'
  }
}
watch(() => props.username, load, { immediate: true })

async function endorse(skillId: number) {
  const skill = profile.value?.skills.find((s) => s.id === skillId)
  if (!skill) return
  await profiles.endorse(props.username, skillId)
  skill.endorsement_count += 1
}
</script>

<template>
  <Alert v-if="error" tone="danger">{{ error }}</Alert>
  <ProfileView
    v-else-if="profile"
    :profile="profile"
    :can-endorse="profile.user.id !== session.user?.id"
    @endorse="endorse"
  />
</template>
