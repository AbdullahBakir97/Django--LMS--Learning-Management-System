<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PhGlobe, PhPlus } from '@phosphor-icons/vue'
import { careers, type Company, type CompanyMember, type CompanyUpdate, type Job } from '@/api/careers'
import { ApiError } from '@/api/client'
import Alert from '@/components/ui/Alert.vue'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tag from '@/components/ui/Tag.vue'
import CompanyLogo from '@/features/careers/CompanyLogo.vue'
import CompanyForm from '@/features/careers/CompanyForm.vue'
import CompanyUpdateItem from '@/features/careers/CompanyUpdate.vue'
import JobCard from '@/features/careers/JobCard.vue'
import JobForm from '@/features/careers/JobForm.vue'

const props = defineProps<{ slug: string }>()
const router = useRouter()
const company = ref<Company | null>(null)
const jobs = ref<Job[]>([])
const members = ref<CompanyMember[]>([])
const missing = ref(false)
const posting = ref(false)
const editing = ref(false)
const invite = ref({ username: '', role: 'recruiter' as 'admin' | 'recruiter' })
const inviteError = ref('')
const updates = ref<CompanyUpdate[]>([])
const news = ref('')

async function postUpdate() {
  updates.value.unshift(await careers.postCompanyUpdate(props.slug, news.value.trim()))
  news.value = ''
}
async function removeUpdate(u: CompanyUpdate) {
  await careers.deleteCompanyUpdate(u.id)
  updates.value = updates.value.filter((x) => x.id !== u.id)
}

async function load() {
  missing.value = false
  try {
    company.value = await careers.company(props.slug)
  } catch {
    missing.value = true
    return
  }
  ;[jobs.value, updates.value] = await Promise.all([
    careers.jobs({ company: props.slug }).then((p) => p.results),
    careers.companyUpdates(props.slug).then((p) => p.results),
  ])
  members.value = company.value.my_role ? await careers.members(props.slug) : []
}
watch(() => props.slug, load, { immediate: true })

async function toggleFollow() {
  company.value = company.value?.following
    ? await careers.unfollow(props.slug)
    : await careers.follow(props.slug)
}
async function addMember() {
  inviteError.value = ''
  try {
    await careers.addMember(props.slug, invite.value.username.replace(/^@/, ''), invite.value.role)
    invite.value.username = ''
    members.value = await careers.members(props.slug)
  } catch (e) {
    inviteError.value =
      e instanceof ApiError && e.problem.status === 404 ? 'No one with that username.' : 'Could not add them.'
  }
}
async function removeMember(m: CompanyMember) {
  try {
    await careers.removeMember(props.slug, m.user_id)
    members.value = members.value.filter((x) => x.user_id !== m.user_id)
  } catch (e) {
    inviteError.value = e instanceof ApiError ? (e.nonField ?? 'Could not remove.') : 'Network error.'
  }
}
function posted(job: Job) {
  posting.value = false
  router.push({ name: 'job', params: { id: job.id } })
}
function saved(c: Company) {
  editing.value = false
  if (c.slug !== props.slug) router.push({ name: 'company', params: { slug: c.slug } })
  else load()
}
</script>

<template>
  <Alert v-if="missing" tone="danger">No such company.</Alert>
  <template v-else-if="company">
    <header class="flex flex-wrap items-start gap-5">
      <CompanyLogo :name="company.name" :src="company.logo" size="lg" />
      <div class="min-w-0 flex-1">
        <h1 class="text-3xl font-semibold">{{ company.name }}</h1>
        <p class="mt-1 text-muted">
          {{
            [company.industry, company.location, company.size && `${company.size} people`]
              .filter(Boolean)
              .join(' · ')
          }}
        </p>
        <p class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
          <span class="font-mono">{{ company.follower_count }} followers</span>
          <a
            v-if="company.website"
            :href="company.website"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 hover:text-ink"
            ><PhGlobe :size="16" weight="light" />{{ company.website.replace(/^https?:\/\//, '') }}</a
          >
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button v-if="company.my_role" @click="posting = true"
          ><PhPlus :size="18" weight="light" /> Post a job</Button
        >
        <Button v-if="company.my_role === 'admin'" variant="secondary" @click="editing = true">Edit</Button>
        <Button
          v-if="!company.my_role"
          :variant="company.following ? 'secondary' : 'primary'"
          :aria-pressed="company.following"
          @click="toggleFollow"
        >
          {{ company.following ? 'Following' : 'Follow' }}
        </Button>
      </div>
    </header>
    <p v-if="company.description" class="mt-6 max-w-prose whitespace-pre-line text-ink">
      {{ company.description }}
    </p>

    <div class="mt-10 grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
      <section aria-labelledby="jobs-title" class="min-w-0">
        <h2 id="jobs-title" class="mb-3 text-lg font-semibold">
          {{ company.my_role ? 'Jobs' : 'Open jobs' }}
        </h2>
        <div class="grid gap-3">
          <JobCard v-for="(j, i) in jobs" :key="j.id" :job="j" @update="jobs[i] = $event" />
          <p v-if="!jobs.length" class="text-muted">No open jobs right now.</p>
        </div>
      </section>
      <section aria-labelledby="updates-title" class="min-w-0 lg:col-start-1">
        <h2 id="updates-title" class="mb-3 text-lg font-semibold">Updates</h2>
        <Card class="grid gap-5 p-5">
          <form v-if="company.my_role" class="grid gap-2" @submit.prevent="postUpdate">
            <label for="company-news" class="sr-only">Share news from {{ company.name }}</label>
            <textarea
              id="company-news"
              v-model="news"
              rows="2"
              maxlength="3000"
              :placeholder="`News from ${company.name}: a launch, an office, a hiring push`"
              class="w-full resize-y rounded-md bg-page px-3 py-2 text-sm text-ink ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
            />
            <Button type="submit" size="sm" class="w-fit" :disabled="!news.trim()">Post update</Button>
          </form>
          <CompanyUpdateItem v-for="u in updates" :key="u.id" :update="u" @remove="removeUpdate(u)" />
          <p v-if="!updates.length" class="text-sm text-muted">
            {{ company.my_role ? 'Followers see what you post here on their home page.' : 'No updates yet.' }}
          </p>
        </Card>
      </section>
      <aside
        v-if="company.my_role"
        aria-labelledby="team-title"
        class="lg:col-start-2 lg:row-span-2 lg:row-start-1"
      >
        <h2 id="team-title" class="mb-3 text-lg font-semibold">Team</h2>
        <Card class="divide-y divide-line">
          <div v-for="m in members" :key="m.user_id" class="flex items-center gap-3 p-3">
            <Avatar :name="m.person.name" :src="m.person.avatar" size="sm" />
            <span class="min-w-0 flex-1 truncate text-sm">{{ m.person.name }}</span>
            <Tag>{{ m.role }}</Tag>
            <button
              v-if="company.my_role === 'admin'"
              type="button"
              class="h-8 cursor-pointer rounded-md px-2 text-xs text-muted hover:bg-danger-soft hover:text-danger"
              :aria-label="`Remove ${m.person.name}`"
              @click="removeMember(m)"
            >
              Remove
            </button>
          </div>
          <form v-if="company.my_role === 'admin'" class="grid gap-2 p-3" @submit.prevent="addMember">
            <label class="sr-only" for="invite-username">Username</label>
            <input
              id="invite-username"
              v-model="invite.username"
              placeholder="@username"
              class="h-9 rounded-md bg-page px-3 text-sm ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
            />
            <div class="flex gap-2">
              <select
                v-model="invite.role"
                aria-label="Role"
                class="h-9 flex-1 rounded-md bg-surface px-2 text-sm ring-1 ring-line-strong"
              >
                <option value="recruiter">Recruiter</option>
                <option value="admin">Admin</option>
              </select>
              <Button type="submit" size="sm" :disabled="!invite.username">Add</Button>
            </div>
            <p v-if="inviteError" class="text-sm text-danger" role="alert">{{ inviteError }}</p>
          </form>
        </Card>
      </aside>
    </div>

    <Dialog v-model:open="posting" title="Post a job">
      <JobForm v-if="posting" :company-slug="company.slug" @saved="posted" />
    </Dialog>
    <Dialog v-model:open="editing" title="Edit company">
      <CompanyForm v-if="editing" :company="company" @saved="saved" />
    </Dialog>
  </template>
</template>
