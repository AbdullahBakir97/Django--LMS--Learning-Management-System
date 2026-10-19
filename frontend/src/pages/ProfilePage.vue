<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PhQuotes } from '@phosphor-icons/vue'
import { profiles, type Profile } from '@/api/profiles'
import { network, type Recommendation, type Relationship } from '@/api/network'
import { ApiError } from '@/api/client'
import ProfileView from '@/features/profile/ProfileView.vue'
import RecommendationForm from '@/features/profile/RecommendationForm.vue'
import RecommendationList from '@/features/profile/RecommendationList.vue'
import RelationshipActions from '@/features/network/RelationshipActions.vue'
import ReportButton from '@/features/moderation/ReportButton.vue'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import TextField from '@/components/ui/TextField.vue'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ username: string }>()
const route = useRoute()
const session = useSessionStore()
const profile = ref<Profile | null>(null)
const recommendations = ref<Recommendation[]>([])
const error = ref('')
const dialog = ref<'recommend' | 'ask' | null>(null)
const note = ref('')
const notice = ref('')

const displayName = (p: Profile) => `${p.user.first_name} ${p.user.last_name}`.trim() || p.user.username

async function load() {
  error.value = ''
  try {
    ;[profile.value, recommendations.value] = await Promise.all([
      profiles.byUsername(props.username),
      network.recommendations(props.username),
    ])
  } catch (e) {
    error.value =
      e instanceof ApiError && e.problem.status === 404
        ? 'No one with that username.'
        : 'Could not load this profile.'
  }
}
watch(() => props.username, load, { immediate: true })

// A "please recommend me" notification links here with #recommend.
function onRelationship(rel: Relationship) {
  if (route.hash === '#recommend' && rel.connection?.status === 'accepted') dialog.value = 'recommend'
}

async function endorse(skillId: number) {
  const skill = profile.value?.skills.find((s) => s.id === skillId)
  if (!skill) return
  await profiles.endorse(props.username, skillId)
  skill.endorsement_count += 1
}

async function ask() {
  await network.askForRecommendation(props.username, note.value)
  note.value = ''
  dialog.value = null
  notice.value = 'Request sent.'
}

function recommended() {
  dialog.value = null
  notice.value = 'Recommendation sent. It shows on their profile once they approve it.'
}
</script>

<template>
  <Alert v-if="notice" tone="success" class="mb-6" role="status">{{ notice }}</Alert>
  <Alert v-if="error" tone="danger">{{ error }}</Alert>
  <ProfileView
    v-else-if="profile"
    :profile="profile"
    :can-endorse="profile.user.id !== session.user?.id"
    @endorse="endorse"
  >
    <template v-if="profile.user.id !== session.user?.id" #actions>
      <RelationshipActions :username="profile.user.username" @change="onRelationship">
        <template #connected>
          <Button size="sm" variant="secondary" @click="dialog = 'recommend'">
            <PhQuotes :size="18" weight="light" /> Recommend
          </Button>
          <Button size="sm" variant="ghost" @click="dialog = 'ask'">Ask for a recommendation</Button>
        </template>
      </RelationshipActions>
      <div class="mt-2">
        <ReportButton kind="user" :object-id="profile.user.id" label="Report this person" />
      </div>
    </template>
    <template v-if="recommendations.length" #recommendations>
      <Card class="p-5">
        <h2 class="text-lg font-semibold">Recommendations</h2>
        <RecommendationList class="mt-3" :items="recommendations" />
      </Card>
    </template>
  </ProfileView>

  <template v-if="profile">
    <Dialog
      :open="dialog === 'recommend'"
      :title="`Recommend ${displayName(profile)}`"
      @update:open="dialog = null"
    >
      <RecommendationForm
        v-if="dialog === 'recommend'"
        :username="profile.user.username"
        :name="profile.user.first_name || profile.user.username"
        @done="recommended"
      />
    </Dialog>
    <Dialog :open="dialog === 'ask'" title="Ask for a recommendation" @update:open="dialog = null">
      <form v-if="dialog === 'ask'" class="grid gap-4" novalidate @submit.prevent="ask">
        <TextField
          v-model="note"
          label="Note (optional)"
          textarea
          hint="Say what you would like them to mention."
        />
        <Button type="submit">Send request</Button>
      </form>
    </Dialog>
  </template>
</template>
