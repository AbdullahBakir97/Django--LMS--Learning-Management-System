# Changelog

All notable changes. The project follows [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- **Portfolio**: projects, papers, talks and repositories on a profile.
- **Recommendations**: connections write them, or you ask a connection for one; nothing shows
  on your profile until you publish it, and a rewrite goes back for your approval.
- **Badges**: earned once for milestones (first course, five courses, first published course,
  first endorsement, ten connections, first recommendation) and announced as notifications.
- **Interviews**: the hiring team offers a slot (video, phone or on site) from the applicant list;
  the candidate confirms or declines; a new time asks again; either side adds it to a calendar
  (.ics); invitations, changes and cancellations reach the candidate by notification and email.
- **Digests and quiet hours**: email right away, or one daily or weekly digest of what you have
  not read at 08:00 in your time zone; quiet hours hold instant email until they end. A `beat`
  service in the production compose file runs the hourly schedule.
- **Installable app and offline reading**: a web app manifest and icons, and a small service
  worker. Courses and lessons you opened, and your account, stay readable offline, with a
  banner saying so. Sign-out deletes what was kept. Nothing else from the API is stored.
- **Search**: one search across people, courses, groups, events, jobs and companies, opened
  with Ctrl/⌘ K or `/`. PostgreSQL full-text search with prefix matching and title-first
  ranking; it reuses each area's visibility rules, so drafts and private groups never leak.

### Fixed

- Recommendation, badge and interview notifications had no icon in the app; a test now keeps
  the backend's notification kinds and the app's icons in step.

## 1.0.0

The rebuild: a modular monolith with nine bounded contexts, a Vue 3 app, and a production stack.

### Added

- **Foundation**: Django 5.1, DRF, PostgreSQL, Redis, Channels, Celery; RFC 9457 errors, cursor
  paging, a domain event bus published after commit, one WebSocket per user, JSON logs, CI.
- **Accounts and profiles**: email sign-in with verification, password reset, JWT with an
  HttpOnly refresh cookie; profiles with experience, education, skills and endorsements.
- **Frontend**: Vue 3, TypeScript, Pinia, Tailwind, a token-based design system with light and
  dark themes, typed API client, Playwright smoke test.
- **Learning**: courses, lessons, quizzes, enrolment with prerequisites, progress, PDF
  certificates with public verification, and the course screens.
- **Notifications**: in the app and live, email for important kinds, per-kind preferences.
- **Network and engagement**: follows, connections, suggestions by shared skills; comments,
  replies and reactions on any registered target, starting with lessons.
- **Community**: feed, public and private groups with roles and approvals, posts, events with
  capacity and RSVPs.
- **Careers**: companies, jobs with skill matching, saved jobs, applications with private
  résumés and a hiring pipeline.
- **Messaging**: direct and group conversations, live delivery, typing indicators, read receipts.
- **Release**: production images, nginx with a Content Security Policy, a production compose
  file, rate limits, a deploy-settings check, an OpenAPI check, image builds in CI, a release
  workflow, demo data, query-count and anonymous-access guards.

### Removed

- The legacy skeleton and its secrets. Owners must still rotate the old keys and purge the old
  database and keys from git history; see SECURITY.md.
