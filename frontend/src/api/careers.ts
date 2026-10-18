import { api } from './client'
import type { Page } from './learning'
import type { Author } from './community'

export type Workplace = 'onsite' | 'hybrid' | 'remote'
export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'internship'
export type JobLevel = 'entry' | 'mid' | 'senior' | 'lead'
export type ApplicationStatus =
  'submitted' | 'reviewing' | 'interview' | 'offer' | 'hired' | 'rejected' | 'withdrawn'

export interface Company {
  id: number
  slug: string
  name: string
  website: string
  location: string
  industry: string
  size: '' | '1-10' | '11-50' | '51-200' | '201-1000' | '1000+'
  description: string
  logo: string | null
  open_jobs: number
  follower_count: number
  my_role: 'admin' | 'recruiter' | null
  following: boolean
}

export interface CompanyRef {
  slug: string
  name: string
  logo: string | null
  location: string
}

export interface Job {
  id: number
  company: CompanyRef
  title: string
  description: string
  location: string
  workplace: Workplace
  employment_type: EmploymentType
  level: JobLevel
  salary_min: number | null
  salary_max: number | null
  currency: string
  skills: string[]
  status: 'draft' | 'open' | 'closed'
  published_at: string | null
  closes_on: string | null
  created_at: string
  matching_skills: number
  skill_count: number
  saved: boolean
  my_application: ApplicationStatus | null
  my_application_id: number | null
  applicant_count: number | null
  on_team: boolean
}

export type JobInput = Pick<
  Job,
  | 'title'
  | 'description'
  | 'location'
  | 'workplace'
  | 'employment_type'
  | 'level'
  | 'salary_min'
  | 'salary_max'
  | 'currency'
  | 'skills'
  | 'closes_on'
> & { company_slug?: string }

export interface Application {
  id: number
  job: { id: number; title: string; company: CompanyRef }
  applicant: Author
  applicant_headline: string
  cover_letter: string
  status: ApplicationStatus
  status_label: string
  status_changed_at: string | null
  created_at: string
  resume_url: string
}

export interface CompanyMember {
  user_id: number
  person: Author
  role: 'admin' | 'recruiter'
}

export interface JobFilters {
  search?: string
  workplace?: Workplace | ''
  employment_type?: EmploymentType | ''
  level?: JobLevel | ''
  company?: string
  saved?: boolean
  sort?: 'newest' | 'match'
  cursor?: string
}

const qs = (params: Record<string, string | boolean | undefined>) => {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v) q.set(k, String(v))
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const careers = {
  jobs: (f: JobFilters = {}) => api<Page<Job>>(`/jobs/${qs({ ...f })}`),
  job: (id: number) => api<Job>(`/jobs/${id}/`),
  createJob: (body: JobInput) => api<Job>('/jobs/', { method: 'POST', body }),
  updateJob: (id: number, body: Partial<JobInput>) => api<Job>(`/jobs/${id}/`, { method: 'PATCH', body }),
  publish: (id: number) => api<Job>(`/jobs/${id}/publish/`, { method: 'POST' }),
  close: (id: number) => api<Job>(`/jobs/${id}/close/`, { method: 'POST' }),
  save: (id: number) => api<Job>(`/jobs/${id}/save/`, { method: 'POST' }),
  unsave: (id: number) => api<Job>(`/jobs/${id}/save/`, { method: 'DELETE' }),
  apply: (id: number, resume: File, coverLetter: string) => {
    const form = new FormData()
    form.append('resume', resume)
    form.append('cover_letter', coverLetter)
    return api<Application>(`/jobs/${id}/apply/`, { method: 'POST', body: form })
  },
  jobApplications: (id: number) => api<Page<Application>>(`/jobs/${id}/applications/`),
  myApplications: () => api<Page<Application>>('/applications/'),
  setStatus: (id: number, status: ApplicationStatus) =>
    api<Application>(`/applications/${id}/status/`, { method: 'POST', body: { status } }),
  withdraw: (id: number) => api<Application>(`/applications/${id}/withdraw/`, { method: 'POST' }),

  companies: (params: { search?: string; mine?: boolean } = {}) =>
    api<Page<Company>>(`/companies/${qs({ search: params.search, mine: params.mine })}`),
  company: (slug: string) => api<Company>(`/companies/${slug}/`),
  createCompany: (body: Partial<Company>) => api<Company>('/companies/', { method: 'POST', body }),
  updateCompany: (slug: string, body: Partial<Company>) =>
    api<Company>(`/companies/${slug}/`, { method: 'PATCH', body }),
  follow: (slug: string) => api<Company>(`/companies/${slug}/follow/`, { method: 'POST' }),
  unfollow: (slug: string) => api<Company>(`/companies/${slug}/follow/`, { method: 'DELETE' }),
  members: (slug: string) => api<CompanyMember[]>(`/companies/${slug}/members/`),
  addMember: (slug: string, username: string, role: 'admin' | 'recruiter') =>
    api<CompanyMember>(`/companies/${slug}/members/`, { method: 'POST', body: { username, role } }),
  removeMember: (slug: string, userId: number) =>
    api<void>(`/companies/${slug}/members/${userId}/`, { method: 'DELETE' }),
}

export const labels = {
  workplace: { onsite: 'On site', hybrid: 'Hybrid', remote: 'Remote' } as Record<Workplace, string>,
  type: {
    full_time: 'Full time',
    part_time: 'Part time',
    contract: 'Contract',
    internship: 'Internship',
  } as Record<EmploymentType, string>,
  level: { entry: 'Entry', mid: 'Mid', senior: 'Senior', lead: 'Lead' } as Record<JobLevel, string>,
}

/** "1,200–1,800 JOD a month"-style band, or empty when no salary is given. */
export function salary(job: Pick<Job, 'salary_min' | 'salary_max' | 'currency'>): string {
  const f = (n: number) => n.toLocaleString('en')
  const { salary_min: lo, salary_max: hi, currency } = job
  if (lo && hi) return lo === hi ? `${f(lo)} ${currency}` : `${f(lo)}–${f(hi)} ${currency}`
  if (lo) return `from ${f(lo)} ${currency}`
  if (hi) return `up to ${f(hi)} ${currency}`
  return ''
}
