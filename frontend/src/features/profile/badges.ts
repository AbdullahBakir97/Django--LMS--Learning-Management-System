import {
  PhCertificate,
  PhChalkboardTeacher,
  PhHandsClapping,
  PhMedal,
  PhQuotes,
  PhUsersThree,
} from '@phosphor-icons/vue'
import type { AchievementCode } from '@/api/profiles'

export const badgeIcon: Record<AchievementCode, typeof PhMedal> = {
  first_course: PhCertificate,
  five_courses: PhMedal,
  first_published: PhChalkboardTeacher,
  first_endorsement: PhHandsClapping,
  ten_connections: PhUsersThree,
  recommended: PhQuotes,
}
