<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhMagnifyingGlass, PhPlus } from '@phosphor-icons/vue'
import { careers, type Company } from '@/api/careers'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import CompanyLogo from '@/features/careers/CompanyLogo.vue'
import CompanyForm from '@/features/careers/CompanyForm.vue'

const router = useRouter()
const companies = ref<Company[]>([])
const search = ref('')
const creating = ref(false)
const load = async () =>
  (companies.value = (await careers.companies({ search: search.value || undefined })).results)
onMounted(load)
let timer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})
const created = (c: Company) => router.push({ name: 'company', params: { slug: c.slug } })
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Companies</h1>
      <p class="mt-1 text-muted">Who is hiring, and what they do.</p>
    </div>
    <Button variant="secondary" @click="creating = true"
      ><PhPlus :size="18" weight="light" /> Add your company</Button
    >
  </div>
  <label class="relative mt-6 block max-w-sm">
    <span class="sr-only">Search companies</span>
    <PhMagnifyingGlass
      :size="18"
      weight="light"
      class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted"
    />
    <input
      v-model="search"
      type="search"
      placeholder="Name, industry, place"
      class="h-10 w-full rounded-md bg-surface pr-3 pl-9 text-sm ring-1 ring-line-strong placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
    />
  </label>
  <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <RouterLink
      v-for="c in companies"
      :key="c.slug"
      :to="{ name: 'company', params: { slug: c.slug } }"
      class="min-w-0"
    >
      <Card class="flex h-full gap-4 p-5 transition-shadow duration-base hover:shadow-pop">
        <CompanyLogo :name="c.name" :src="c.logo" />
        <div class="min-w-0">
          <h2 class="truncate font-semibold">{{ c.name }}</h2>
          <p class="truncate text-sm text-muted">
            {{ [c.industry, c.location].filter(Boolean).join(' · ') }}
          </p>
          <p class="mt-2 font-mono text-xs text-accent">
            {{ c.open_jobs }} open job{{ c.open_jobs === 1 ? '' : 's' }}
          </p>
        </div>
      </Card>
    </RouterLink>
  </div>
  <p v-if="!companies.length" class="py-10 text-center text-muted">No companies match.</p>
  <Dialog v-model:open="creating" title="Add your company">
    <CompanyForm @saved="created" />
  </Dialog>
</template>
