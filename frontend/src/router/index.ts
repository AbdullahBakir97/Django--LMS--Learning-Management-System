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
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue') },
  ],
})

router.beforeEach((to) => {
  const session = useSessionStore()
  if (to.meta.requiresAuth && !session.isAuthenticated) {
    return { name: 'login', query: to.fullPath !== '/' ? { next: to.fullPath } : {} }
  }
  if (to.meta.guestOnly && session.isAuthenticated && to.name !== 'verify-email') {
    return { name: 'home' }
  }
})
