<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { PhPlus, PhTrash } from '@phosphor-icons/vue'
import { auth } from '@/api/auth'
import { profiles, type Profile, type SkillLevel } from '@/api/profiles'
import { useSessionStore } from '@/stores/session'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import TextField from '@/components/ui/TextField.vue'
import EntryForm, { type Field } from '@/features/profile/EntryForm.vue'
import { dateRange } from '@/features/profile/format'

const session = useSessionStore()
const profile = ref<Profile | null>(null)
const saved = ref(false)
const busy = ref(false)

const about = reactive({ first_name: '', last_name: '', headline: '', location: '', website: '', bio: '' })

onMounted(async () => {
  profile.value = await profiles.me()
  Object.assign(about, {
    first_name: profile.value.user.first_name,
    last_name: profile.value.user.last_name,
    headline: profile.value.headline,
    location: profile.value.location,
    website: profile.value.website,
    bio: profile.value.bio,
  })
})

async function saveAbout() {
  busy.value = true
  saved.value = false
  const { first_name, last_name, ...rest } = about
  await Promise.all([auth.updateMe({ first_name, last_name }), profiles.updateMe(rest)])
  await Promise.all([session.refreshUser(), reload()])
  busy.value = false
  saved.value = true
}

async function reload() {
  profile.value = await profiles.me()
}

const experienceFields: Field[] = [
  { key: 'title', label: 'Title', required: true },
  { key: 'company', label: 'Company', required: true },
  { key: 'location', label: 'Location' },
  { key: 'start_date', label: 'Start date', type: 'date', required: true },
  { key: 'end_date', label: 'End date (empty if current)', type: 'date' },
  { key: 'description', label: 'Description', textarea: true },
]
const educationFields: Field[] = [
  { key: 'institution', label: 'Institution', required: true },
  { key: 'degree', label: 'Degree' },
  { key: 'field_of_study', label: 'Field of study' },
  { key: 'start_date', label: 'Start date', type: 'date', required: true },
  { key: 'end_date', label: 'End date (empty if current)', type: 'date' },
  { key: 'description', label: 'Description', textarea: true },
]

const dialog = ref<'experience' | 'education' | null>(null)
async function closeAndReload() {
  dialog.value = null
  await reload()
}
const submitExperience = (d: Record<string, string | null>) => profiles.addExperience(d as never)
const submitEducation = (d: Record<string, string | null>) => profiles.addEducation(d as never)
const skillName = ref('')
const skillLevel = ref<SkillLevel>('intermediate')
const skillError = ref('')

async function addSkill() {
  skillError.value = ''
  try {
    await profiles.addSkill(skillName.value, skillLevel.value)
    skillName.value = ''
    await reload()
  } catch (e) {
    skillError.value =
      (e as { field?: (k: string) => string })?.field?.('name') ?? 'Could not add that skill.'
  }
}

async function remove(kind: 'experience' | 'education' | 'skill', id: number) {
  const fn = {
    experience: profiles.removeExperience,
    education: profiles.removeEducation,
    skill: profiles.removeSkill,
  }[kind]
  await fn(id)
  await reload()
}
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">My profile</h1>
      <p class="mt-1 text-muted">
        What others see at <span class="font-mono">/u/{{ session.user?.username }}</span>
      </p>
    </div>
    <RouterLink
      v-if="session.user"
      :to="{ name: 'profile', params: { username: session.user.username } }"
      class="text-sm text-accent hover:underline"
      >View public profile</RouterLink
    >
  </div>

  <template v-if="profile">
    <Card class="mt-8 p-5">
      <h2 class="text-lg font-semibold">About</h2>
      <form class="mt-4 grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="saveAbout">
        <TextField v-model="about.first_name" label="First name" autocomplete="given-name" />
        <TextField v-model="about.last_name" label="Last name" autocomplete="family-name" />
        <TextField
          v-model="about.headline"
          label="Headline"
          class="sm:col-span-2"
          hint="One line under your name, e.g. “Backend engineer, teaches Django”."
        />
        <TextField v-model="about.location" label="Location" />
        <TextField v-model="about.website" label="Website" type="url" />
        <TextField v-model="about.bio" label="Bio" textarea class="sm:col-span-2" />
        <div class="flex items-center gap-3 sm:col-span-2">
          <Button type="submit" :loading="busy">Save</Button>
          <span v-if="saved" class="text-sm text-success">Saved.</span>
        </div>
      </form>
    </Card>

    <div class="mt-6 grid gap-6 lg:grid-cols-[2fr_1fr]">
      <div class="grid gap-6">
        <Card class="p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Experience</h2>
            <Button size="sm" variant="secondary" @click="dialog = 'experience'"
              ><PhPlus :size="16" weight="light" /> Add</Button
            >
          </div>
          <ul class="mt-3 divide-y divide-line">
            <li
              v-for="e in profile.experiences"
              :key="e.id"
              class="flex items-start justify-between gap-3 py-3"
            >
              <span>
                <span class="block font-medium"
                  >{{ e.title }} <span class="text-muted">· {{ e.company }}</span></span
                >
                <span class="font-mono text-xs text-muted">{{ dateRange(e.start_date, e.end_date) }}</span>
              </span>
              <button
                type="button"
                class="grid size-9 shrink-0 cursor-pointer place-items-center rounded-md text-muted hover:bg-danger-soft hover:text-danger"
                :aria-label="`Remove ${e.title}`"
                @click="remove('experience', e.id)"
              >
                <PhTrash :size="18" weight="light" />
              </button>
            </li>
          </ul>
        </Card>
        <Card class="p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Education</h2>
            <Button size="sm" variant="secondary" @click="dialog = 'education'"
              ><PhPlus :size="16" weight="light" /> Add</Button
            >
          </div>
          <ul class="mt-3 divide-y divide-line">
            <li
              v-for="e in profile.educations"
              :key="e.id"
              class="flex items-start justify-between gap-3 py-3"
            >
              <span>
                <span class="block font-medium">{{ e.institution }}</span>
                <span class="font-mono text-xs text-muted">{{ dateRange(e.start_date, e.end_date) }}</span>
              </span>
              <button
                type="button"
                class="grid size-9 shrink-0 cursor-pointer place-items-center rounded-md text-muted hover:bg-danger-soft hover:text-danger"
                :aria-label="`Remove ${e.institution}`"
                @click="remove('education', e.id)"
              >
                <PhTrash :size="18" weight="light" />
              </button>
            </li>
          </ul>
        </Card>
      </div>
      <Card class="p-5">
        <h2 class="text-lg font-semibold">Skills</h2>
        <form class="mt-3 grid gap-2" novalidate @submit.prevent="addSkill">
          <TextField v-model="skillName" label="Add a skill" placeholder="e.g. Django" :error="skillError" />
          <label class="grid gap-1.5 text-sm font-medium">
            Level
            <select
              v-model="skillLevel"
              class="h-11 rounded-md bg-surface px-3 text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
            >
              <option v-for="l in ['beginner', 'intermediate', 'advanced', 'expert']" :key="l" :value="l">
                {{ l }}
              </option>
            </select>
          </label>
          <Button type="submit" size="sm" variant="secondary" :disabled="!skillName.trim()">Add</Button>
        </form>
        <ul class="mt-4 grid gap-1">
          <li v-for="s in profile.skills" :key="s.id" class="flex items-center justify-between gap-2">
            <span class="min-w-0"
              ><span class="block truncate font-medium">{{ s.name }}</span
              ><span class="font-mono text-xs text-muted"
                >{{ s.level }} · {{ s.endorsement_count }} endorsements</span
              ></span
            >
            <button
              type="button"
              class="grid size-9 shrink-0 cursor-pointer place-items-center rounded-md text-muted hover:bg-danger-soft hover:text-danger"
              :aria-label="`Remove ${s.name}`"
              @click="remove('skill', s.id)"
            >
              <PhTrash :size="18" weight="light" />
            </button>
          </li>
        </ul>
      </Card>
    </div>

    <Dialog :open="dialog === 'experience'" title="Add experience" @update:open="dialog = null">
      <EntryForm
        v-if="dialog === 'experience'"
        :fields="experienceFields"
        :submit="submitExperience"
        @done="closeAndReload"
      />
    </Dialog>
    <Dialog :open="dialog === 'education'" title="Add education" @update:open="dialog = null">
      <EntryForm
        v-if="dialog === 'education'"
        :fields="educationFields"
        :submit="submitEducation"
        @done="closeAndReload"
      />
    </Dialog>
  </template>
</template>
