# Security Policy

## Supported versions

The latest release and the default branch are supported.

## Reporting a vulnerability

Please **do not open a public issue**. Contact the maintainer directly:

- Email: abdullah.bakir.1997@gmail.com
- GitHub: [@AbdullahBakir97](https://github.com/AbdullahBakir97)

You will get an acknowledgement, and a fix or mitigation will be coordinated before any public
disclosure.

## How the application protects data

- Every queryset is scoped to the signed-in user; rows a user may not see are a 404, not a 403.
- Résumés are stored under random names and served only through a permission-checked endpoint.
- Access tokens stay in memory; the refresh token is an HttpOnly, Secure cookie scoped to one path.
- WebSockets authenticate with a 30-second signed ticket and check the origin.
- Markdown from users is sanitised before it is shown; posts, comments and messages are plain text.
- Sign-in, sign-up and password reset are rate limited per client.
- CI checks the production settings with Django's deployment checklist on every push.

## Known history

Early revisions of this repository committed a database file and secret keys. They are removed
from the tree, but remain in git history until it is rewritten. Anyone running an old deployment
should rotate those keys.

_Last updated: 2026-10-18_
