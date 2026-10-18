<script setup lang="ts">
import { reactive, ref } from 'vue'
import { community, type Group, type Privacy } from '@/api/community'
import { ApiError } from '@/api/client'
import TextField from '@/components/ui/TextField.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ group?: Group }>()
const emit = defineEmits<{ saved: [group: Group] }>()
const form = reactive({
  name: props.group?.name ?? '',
  description: props.group?.description ?? '',
  privacy: (props.group?.privacy ?? 'public') as Privacy,
})
const errors = ref<ApiError | null>(null)
const busy = ref(false)

async function submit() {
  busy.value = true
  errors.value = null
  try {
    emit(
      'saved',
      props.group ? await community.updateGroup(props.group.slug, form) : await community.createGroup(form),
    )
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
    <TextField
      v-model="form.description"
      textarea
      label="What is it about?"
      :error="errors?.field('description')"
    />
    <fieldset class="grid gap-2">
      <legend class="mb-1 text-sm font-medium">Who can see posts</legend>
      <label
        v-for="opt in [
          { v: 'public', t: 'Public', d: 'Anyone signed in can read posts and join.' },
          { v: 'private', t: 'Private', d: 'Only members read posts. Joining needs approval.' },
        ]"
        :key="opt.v"
        class="flex cursor-pointer items-start gap-3 rounded-md p-3 ring-1"
        :class="form.privacy === opt.v ? 'bg-accent-soft ring-accent/40' : 'ring-line'"
      >
        <input v-model="form.privacy" type="radio" :value="opt.v" class="mt-1 accent-[var(--c-accent)]" />
        <span>
          <span class="block text-sm font-medium">{{ opt.t }}</span>
          <span class="block text-sm text-muted">{{ opt.d }}</span>
        </span>
      </label>
    </fieldset>
    <p v-if="errors?.nonField && !errors.field('name')" class="text-sm text-danger" role="alert">
      {{ errors.nonField }}
    </p>
    <div class="flex justify-end">
      <Button type="submit" :loading="busy">{{ group ? 'Save' : 'Create group' }}</Button>
    </div>
  </form>
</template>
