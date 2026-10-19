import {
  PhArrowBendUpLeft,
  PhBell,
  PhBriefcase,
  PhFileText,
  PhCalendarCheck,
  PhCalendarDots,
  PhDoorOpen,
  PhUsersFour,
  PhCertificate,
  PhChatCircleText,
  PhHandshake,
  PhHandsClapping,
  PhMedal,
  PhQuotes,
  PhRepeat,
  PhShieldCheck,
  PhUserCirclePlus,
  PhUserPlus,
  PhUsersThree,
} from '@phosphor-icons/vue'
import type { NotificationKind } from '@/api/notifications'

export const kindIcon: Record<NotificationKind, typeof PhBell> = {
  enrolment: PhUserPlus,
  course_completed: PhCertificate,
  endorsement: PhHandsClapping,
  follow: PhUserCirclePlus,
  connection_request: PhHandshake,
  connection_accepted: PhUsersThree,
  comment: PhChatCircleText,
  reply: PhArrowBendUpLeft,
  group_request: PhDoorOpen,
  group_approved: PhUsersFour,
  event_rsvp: PhCalendarCheck,
  application_received: PhFileText,
  application_update: PhBriefcase,
  recommendation_request: PhQuotes,
  recommendation: PhQuotes,
  achievement: PhMedal,
  interview: PhCalendarDots,
  interview_reply: PhCalendarCheck,
  post_shared: PhRepeat,
  report_reviewed: PhShieldCheck,
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
