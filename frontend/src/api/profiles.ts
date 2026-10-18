import { api } from './client'
import type { User } from './auth'

export interface Experience {
  id: number
  title: string
  company: string
  location: string
  start_date: string
  end_date: string | null
  description: string
}

export interface Education {
  id: number
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string | null
  description: string
}

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert'

export interface ProfileSkill {
  id: number
  name: string
  level: SkillLevel
  endorsement_count: number
}

export interface Profile {
  id: number
  user: User
  headline: string
  bio: string
  avatar: string | null
  location: string
  website: string
  experiences: Experience[]
  educations: Education[]
  skills: ProfileSkill[]
  created_at: string
  updated_at: string
}

type ExperienceInput = Omit<Experience, 'id'>
type EducationInput = Omit<Education, 'id'>

export const profiles = {
  me: () => api<Profile>('/profiles/me/'),
  updateMe: (data: Partial<Pick<Profile, 'headline' | 'bio' | 'location' | 'website'>>) =>
    api<Profile>('/profiles/me/', { method: 'PATCH', body: data }),
  byUsername: (username: string) => api<Profile>(`/profiles/${encodeURIComponent(username)}/`),

  addExperience: (data: ExperienceInput) =>
    api<Experience>('/profiles/me/experiences/', { method: 'POST', body: data }),
  updateExperience: (id: number, data: Partial<ExperienceInput>) =>
    api<Experience>(`/profiles/me/experiences/${id}/`, { method: 'PATCH', body: data }),
  removeExperience: (id: number) => api(`/profiles/me/experiences/${id}/`, { method: 'DELETE' }),

  addEducation: (data: EducationInput) =>
    api<Education>('/profiles/me/educations/', { method: 'POST', body: data }),
  updateEducation: (id: number, data: Partial<EducationInput>) =>
    api<Education>(`/profiles/me/educations/${id}/`, { method: 'PATCH', body: data }),
  removeEducation: (id: number) => api(`/profiles/me/educations/${id}/`, { method: 'DELETE' }),

  addSkill: (name: string, level: SkillLevel) =>
    api<ProfileSkill>('/profiles/me/skills/', { method: 'POST', body: { name, level } }),
  removeSkill: (id: number) => api(`/profiles/me/skills/${id}/`, { method: 'DELETE' }),
  endorse: (username: string, skillId: number) =>
    api(`/profiles/${encodeURIComponent(username)}/skills/${skillId}/endorse/`, { method: 'POST' }),
  withdrawEndorsement: (username: string, skillId: number) =>
    api(`/profiles/${encodeURIComponent(username)}/skills/${skillId}/endorse/`, { method: 'DELETE' }),
  searchSkills: (q: string) =>
    api<{ id: number; name: string }[]>(`/skills/?search=${encodeURIComponent(q)}`),
}
