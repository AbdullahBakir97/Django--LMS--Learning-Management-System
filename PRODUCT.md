# Product

## Platform

Web app: a Vue 3 single-page app served next to a Django REST and WebSocket API. Desktop and phone
browsers; installable later as a PWA.

## Users

- **Learners**: enrol in courses, work through lessons and quizzes, earn certificates, build a
  profile and a network, find jobs.
- **Instructors**: author courses, lessons and quizzes, see who is enrolled and how far they are,
  issue certificates.
- **Admins**: moderate, manage companies and roles, see the whole platform.

## Purpose

A learning management system joined to a professional network. People learn, show what they learned
on a profile, connect with the people who taught them and the people they studied with, and move
from there to jobs. Success: a learner can go from sign-up to a verified certificate on a public
profile without leaving the product.

## Positioning

Calm and credible. The product is used at work and for work: it should feel like a well-made tool
people trust with their credentials, not a consumer feed. Open source under MIT; the architecture is
a reference for building Django products properly.

## Constraints

- Every action is scoped to the signed-in user; the API never trusts ids from the client.
- Accessibility: keyboard reachable, visible focus, 4.5:1 text contrast, reduced motion respected.
- Works at 390px width; tables and long content scroll inside their card, never the page.
- English first; strings are kept simple so Arabic and German can follow with right-to-left support.

## Brand commitments

- One accent colour (deep teal), one neutral family (cool slate), two type families (Bricolage
  Grotesque for display, Geist for everything else) and a mono face for data.
- Light and dark themes with identical structure; the user picks, the system is the default.
- No decorative illustration or stock imagery. Content and typography carry the page.

## Open decisions

- Social login providers for v2 (Google, LinkedIn through allauth).
- Payments for paid courses (v2, behind a flag).
