import { api } from './client'
import type { User } from './auth'

export type Level = 'beginner' | 'intermediate' | 'advanced'

export interface Page<T> {
  next: string | null
  previous: string | null
  results: T[]
}

export interface CourseSummary {
  id: number
  slug: string
  title: string
  summary: string
  cover: string | null
  level: Level
  language: string
  status: 'draft' | 'published'
  published_at: string | null
  instructor: User
  lesson_count: number
  enrollment_count: number
  created_at: string
}

export interface LessonSummary {
  id: number
  title: string
  order: number
  is_free_preview: boolean
  video_url: string
  has_quiz: boolean
}

export interface Course extends CourseSummary {
  description: string
  prerequisites: string[]
  lessons: LessonSummary[]
}

export interface Lesson {
  id: number
  title: string
  order: number
  content: string
  video_url: string
  is_free_preview: boolean
  attachments: { id: number; title: string; file: string }[]
  has_quiz: boolean
}

export interface Progress {
  id: number
  status: 'active' | 'completed'
  completed_at: string | null
  completed_lessons: number[]
  passed_quizzes: number[]
  certificate_code: string | null
  created_at: string
}

export interface Choice {
  id?: number
  text: string
  is_correct?: boolean
}

export interface Question {
  id?: number
  text: string
  order: number
  choices: Choice[]
}

export interface Quiz {
  id?: number
  title: string
  pass_score: number
  questions: Question[]
}

export interface QuizResult {
  score: number
  passed: boolean
  pass_score: number
  created_at: string
}

export interface EnrollmentItem {
  id: number
  status: 'active' | 'completed'
  completed_at: string | null
  created_at: string
  course: Pick<CourseSummary, 'id' | 'slug' | 'title' | 'summary' | 'cover' | 'level' | 'instructor'>
}

export interface CertificateRecord {
  code: string
  student: string
  course: string
  instructor: string
  completed_at: string
  pdf: string | null
}

type CourseInput = Pick<Course, 'title' | 'summary' | 'description' | 'level' | 'language'>
type LessonInput = Pick<Lesson, 'title' | 'order' | 'content' | 'video_url' | 'is_free_preview'>

const c = (slug: string) => `/courses/${encodeURIComponent(slug)}`

export const learning = {
  courses: (
    params: {
      search?: string
      level?: Level | ''
      status?: string
      instructor?: string
      cursor?: string
    } = {},
  ) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][])
    return api<Page<CourseSummary>>(`/courses/${q.size ? `?${q}` : ''}`)
  },
  course: (slug: string) => api<Course>(`${c(slug)}/`),
  createCourse: (data: Partial<CourseInput>) => api<Course>('/courses/', { method: 'POST', body: data }),
  updateCourse: (slug: string, data: Partial<CourseInput>) =>
    api<Course>(`${c(slug)}/`, { method: 'PATCH', body: data }),
  deleteCourse: (slug: string) => api(`${c(slug)}/`, { method: 'DELETE' }),
  publish: (slug: string) => api<Course>(`${c(slug)}/publish/`, { method: 'POST' }),
  enroll: (slug: string) => api<Progress>(`${c(slug)}/enroll/`, { method: 'POST' }),
  progress: (slug: string) => api<Progress | undefined>(`${c(slug)}/progress/`),

  lesson: (slug: string, id: number) => api<Lesson>(`${c(slug)}/lessons/${id}/`),
  createLesson: (slug: string, data: Partial<LessonInput>) =>
    api<Lesson>(`${c(slug)}/lessons/`, { method: 'POST', body: data }),
  updateLesson: (slug: string, id: number, data: Partial<LessonInput>) =>
    api<Lesson>(`${c(slug)}/lessons/${id}/`, { method: 'PATCH', body: data }),
  deleteLesson: (slug: string, id: number) => api(`${c(slug)}/lessons/${id}/`, { method: 'DELETE' }),
  completeLesson: (slug: string, id: number) =>
    api<Progress>(`${c(slug)}/lessons/${id}/complete/`, { method: 'POST' }),

  quiz: (lessonId: number) => api<Quiz>(`/lessons/${lessonId}/quiz/`),
  saveQuiz: (lessonId: number, quiz: Quiz) =>
    api<Quiz>(`/lessons/${lessonId}/quiz/`, { method: 'PUT', body: quiz }),
  deleteQuiz: (lessonId: number) => api(`/lessons/${lessonId}/quiz/`, { method: 'DELETE' }),
  submitQuiz: (lessonId: number, answers: Record<number, number>) =>
    api<QuizResult>(`/lessons/${lessonId}/quiz/submit/`, { method: 'POST', body: { answers } }),

  myEnrollments: () => api<Page<EnrollmentItem>>('/me/enrollments/'),
  certificate: (code: string) => api<CertificateRecord>(`/certificates/${encodeURIComponent(code)}/`),
}
