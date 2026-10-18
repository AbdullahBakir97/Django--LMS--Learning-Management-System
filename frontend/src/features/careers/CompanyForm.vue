<script setup lang="ts">
import { reactive, ref } from 'vue'
import { careers, type Company } from '@/api/careers'
import { ApiError } from '@/api/client'
import TextField from '@/components/ui/TextField.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ company?: Company }>()
const emit = defineEmits<{ saved: [company: Company] }>()
const c = props.company
const form = reactive({
  name: c?.name ?? '',
  website: c?.website ?? '',
  location: c?.location ?? '',
  industry: c?.industry ?? '',
  size: c?.size ?? '',
  description: c?.description ?? '',
})
const errors = ref<ApiError | null>(null)
const busy = ref(false)

async function submit() {
  busy.value = true
  errors.value = null
  try {
    emit('saved', c ? await careers.updateCompany(c.slug, form) : await careers.createCompany(form))
  } catch (e) {
    if (e instanceof ApiError) errors.value = e
    else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" @submit.prevent="submit">
    <TextField v-model="form.name" label="Name" required :error="errors?.field('name')" />
    <div class="grid gap-4 sm:grid-cols-2">
      <TextField v-model="form.industry" label="Industry" />
      <TextField v-model="form.location" label="Location" />
    </div>
    <div class="grid gap-4 sm:grid-cols-2">
      <TextField v-model="form.website" type="url" label="Website" :error="errors?.field('website')" />
      <label class="grid gap-1.5 text-sm font-medium"
        >Size
        <select v-model="form.size" class="h-11 rounded-md bg-surface px-3 text-sm ring-1 ring-line-strong">
          <option value="">Not said</option>
          <option v-for="s in ['1-10', '11-50', '51-200', '201-1000', '1000+']" :key="s" :value="s">
            {{ s }} people
          </option>
        </select>
      </label>
    </div>
    <TextField v-model="form.description" textarea label="About" />
    <div class="flex justify-end">
      <Button type="submit" :loading="busy">{{ company ? 'Save' : 'Create company' }}</Button>
    </div>
  </form>
</template>
