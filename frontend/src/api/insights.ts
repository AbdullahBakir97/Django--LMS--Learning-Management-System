import { api } from './client'
import type { Revenue } from './learning'

export interface Week {
  week: string
  count: number
}

/** Fields named `new_*` and `recent_*` cover the last 30 days. Money is in cents. */
export interface Overview {
  people: number
  new_people: number
  courses: number
  enrolments: number
  new_enrolments: number
  completion_rate: number
  posts: number
  open_jobs: number
  open_reports: number
  revenue: Revenue[]
  weekly_signups: Week[]
  weekly_enrolments: Week[]
  top_courses: {
    slug: string
    title: string
    instructor: string
    new_enrolments: number
    enrolled: number
  }[]
}

export const insights = {
  overview: () => api<Overview>('/insights/overview/'),
}
