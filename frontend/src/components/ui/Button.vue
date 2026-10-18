<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md'
    type?: 'button' | 'submit'
    loading?: boolean
    disabled?: boolean
  }>(),
  { variant: 'primary', size: 'md', type: 'button' },
)
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    class="inline-flex cursor-pointer items-center justify-center gap-2 rounded-md font-medium transition-[background-color,color,transform] duration-quick ease-out active:translate-y-px disabled:cursor-not-allowed disabled:opacity-60"
    :class="[
      size === 'sm' ? 'h-9 px-3 text-sm' : 'h-11 px-4 text-sm',
      variant === 'primary' && 'bg-accent text-accent-ink hover:brightness-110',
      variant === 'secondary' && 'bg-surface text-ink ring-1 ring-line-strong hover:bg-surface-2',
      variant === 'ghost' && 'text-ink hover:bg-surface-2',
      variant === 'danger' && 'bg-danger-soft text-danger hover:brightness-95',
    ]"
  >
    <span
      v-if="loading"
      class="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
      aria-hidden="true"
    />
    <slot />
  </button>
</template>
