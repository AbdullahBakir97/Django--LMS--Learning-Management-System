import { PhCertificate, PhHandsClapping, PhUserPlus, PhBell } from '@phosphor-icons/vue'
import type { NotificationKind } from '@/api/notifications'

export const kindIcon: Record<NotificationKind, typeof PhBell> = {
  enrolment: PhUserPlus,
  course_completed: PhCertificate,
  endorsement: PhHandsClapping,
}

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const steps: [Intl.RelativeTimeFormatUnit, number][] = [
  ['second', 60],
  ['minute', 60],
  ['hour', 24],
  ['day', 7],
  ['week', 4.35],
  ['month', 12],
  ['year', Infinity],
]

/** "just now", "5 minutes ago", "yesterday", "3 weeks ago". */
export function timeAgo(iso: string, now = Date.now()): string {
  let value = (new Date(iso).getTime() - now) / 1000
  if (Math.abs(value) < 45) return 'just now'
  for (const [unit, size] of steps) {
    if (Math.abs(value) < size) return rtf.format(Math.round(value), unit)
    value /= size
  }
  return ''
}

/** Group label by calendar day in the viewer's time zone. */
export function dayGroup(iso: string, now = new Date()): 'Today' | 'Yesterday' | 'Earlier' {
  const d = new Date(iso)
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  if (d.getTime() >= start) return 'Today'
  if (d.getTime() >= start - 86_400_000) return 'Yesterday'
  return 'Earlier'
}
