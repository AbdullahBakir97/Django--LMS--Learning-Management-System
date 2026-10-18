import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '@/stores/session'

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/AppShell.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'home', component: () => import('@/pages/HomePage.vue') },
        { path: 'me', name: 'my-profile', component: () => import('@/pages/MyProfilePage.vue') },
        {
          path: 'u/:username',
          name: 'profile',
          component: () => import('@/pages/ProfilePage.vue'),
          props: true,
        },
        { path: 'messages', name: 'messages', component: () => import('@/pages/MessagesPage.vue') },
        {
          path: 'messages/:id',
          name: 'conversation',
          component: () => import('@/pages/MessagesPage.vue'),
          props: true,
        },
        { path: 'jobs', name: 'jobs', component: () => import('@/pages/careers/JobsPage.vue') },
        {
          path: 'jobs/:id',
          name: 'job',
          component: () => import('@/pages/careers/JobPage.vue'),
          props: true,
        },
        {
          path: 'jobs/:id/applications',
          name: 'job-applications',
          component: () => import('@/pages/careers/JobApplicationsPage.vue'),
          props: true,
        },
        {
          path: 'applications',
          name: 'applications',
          component: () => import('@/pages/careers/MyApplicationsPage.vue'),
        },
        {
          path: 'companies',
          name: 'companies',
          component: () => import('@/pages/careers/CompaniesPage.vue'),
        },
        {
          path: 'companies/:slug',
          name: 'company',
          component: () => import('@/pages/careers/CompanyPage.vue'),
          props: true,
        },
        {
          path: 'groups',
          name: 'groups',
          component: () => import('@/pages/GroupsPage.vue'),
        },
        {
          path: 'groups/:slug',
          name: 'group',
          component: () => import('@/pages/GroupPage.vue'),
          props: true,
        },
        {
          path: 'events',
          name: 'events',
          component: () => import('@/pages/EventsPage.vue'),
        },
        {
          path: 'events/:id',
          name: 'event',
          component: () => import('@/pages/EventPage.vue'),
          props: true,
        },
        {
          path: 'posts/:id',
          name: 'post',
          component: () => import('@/pages/PostPage.vue'),
          props: true,
        },
        {
          path: 'network',
          name: 'network',
          component: () => import('@/pages/NetworkPage.vue'),
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/pages/NotificationsPage.vue'),
        },
        { path: 'courses', name: 'courses', component: () => import('@/pages/learning/CatalogPage.vue') },
        {
          path: 'courses/:slug',
          name: 'course',
          component: () => import('@/pages/learning/CoursePage.vue'),
          props: true,
        },
        {
          path: 'courses/:slug/lessons/:id',
          name: 'lesson',
          component: () => import('@/pages/learning/LessonPage.vue'),
          props: true,
        },
        {
          path: 'learning',
          name: 'my-learning',
          component: () => import('@/pages/learning/MyLearningPage.vue'),
        },
        {
          path: 'teach',
          name: 'teach',
          component: () => import('@/pages/learning/TeachPage.vue'),
          meta: { instructorOnly: true },
        },
        {
          path: 'teach/new',
          name: 'course-new',
          component: () => import('@/pages/learning/CourseEditorPage.vue'),
          meta: { instructorOnly: true },
        },
        {
          path: 'teach/:slug',
          name: 'course-editor',
          component: () => import('@/pages/learning/CourseEditorPage.vue'),
          props: true,
          meta: { instructorOnly: true },
        },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/AuthLayout.vue'),
      meta: { guestOnly: true },
      children: [
        { path: 'login', name: 'login', component: () => import('@/pages/auth/LoginPage.vue') },
        { path: 'register', name: 'register', component: () => import('@/pages/auth/RegisterPage.vue') },
        {
          path: 'check-email',
          name: 'check-email',
          component: () => import('@/pages/auth/CheckEmailPage.vue'),
        },
        {
          path: 'verify-email/:code',
          name: 'verify-email',
          component: () => import('@/pages/auth/VerifyEmailPage.vue'),
          props: true,
        },
        {
          path: 'forgot-password',
          name: 'forgot-password',
          component: () => import('@/pages/auth/ForgotPasswordPage.vue'),
        },
        {
          path: 'reset-password/:uid/:token',
          name: 'reset-password',
          component: () => import('@/pages/auth/ResetPasswordPage.vue'),
          props: true,
        },
      ],
    },
    {
      path: '/certificates/:code',
      name: 'certificate',
      component: () => import('@/pages/learning/CertificatePage.vue'),
      props: true,
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue') },
  ],
})

router.beforeEach((to) => {
  const session = useSessionStore()
  if (to.meta.requiresAuth && !session.isAuthenticated) {
    return { name: 'login', query: to.fullPath !== '/' ? { next: to.fullPath } : {} }
  }
  if (to.meta.instructorOnly && !['instructor', 'admin'].includes(session.user?.role ?? '')) {
    return { name: 'home' }
  }
  if (to.meta.guestOnly && session.isAuthenticated && to.name !== 'verify-email') {
    return { name: 'home' }
  }
})
