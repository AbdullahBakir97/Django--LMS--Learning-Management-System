# Design

The visual system of the LMS. Tokens live in `frontend/src/styles/tokens.css`; UI primitives in
`frontend/src/components/ui`; screens in `frontend/src/pages` and `frontend/src/features`. Product
context is in `PRODUCT.md`.

## World

A working tool for people who learn and teach for a living. Quiet surfaces, a single deep-teal
accent for the one action that matters on a screen, generous whitespace, and type that does the
talking. Nothing glows, nothing bounces.

## Themes

Every theme defines the same semantic roles, and components only ever use the roles:

| Role | Light | Dark | Use |
|---|---|---|---|
| `page` | cool off-white | deep slate | the canvas |
| `surface`, `surface-2` | white, light slate | raised slate | cards, inputs, hover fills |
| `ink`, `muted` | near-black, slate | off-white, light slate | text |
| `line`, `line-strong` | ink at 10% and 18% | same, inverted | hairlines, input rings |
| `accent`, `accent-ink`, `accent-soft` | teal 700 on white | teal 400 on dark | primary action, active nav, focus |
| `danger`, `success` + soft fills | | | feedback only, never decoration |

The theme is set as `data-theme` on `<html>`; the system preference is the default and the toggle
remembers the choice per browser.

## Type

- **Bricolage Grotesque** (display): page titles and section headings, weight 600, tight tracking.
- **Geist** (sans): body, labels, controls. 16px base, 1.5 line height.
- **Geist Mono**: handles (`@username`), dates, levels, counts, anything a machine produced.

Headings use `text-wrap: balance`. Running text stays under 65 characters per line.

## Layout

- App shell: a 240px rail on large screens, a slide-in drawer below `lg`. Content column maxes at
  64rem with 16px side gutters on phones.
- Auth screens: one 28rem column, brand top-left, theme toggle top-right.
- Cards use `surface`, a 1px `line` ring and the soft `shadow-card`. Only floating things (dialogs,
  menus) get `shadow-pop`.
- Radii: 6px controls, 10px cards, 14px large panels. Nothing fully round except avatars.

## Motion

| Token | Value | Use |
|---|---|---|
| `--duration-quick` | 160 ms | hover and focus colour changes |
| `--duration-base` | 240 ms | page arrival (`animate-page`), drawer, dialogs |

Easing `--ease-out` (expo-like) for arrivals. `prefers-reduced-motion` zeroes every duration.

## Components

Primitives in `components/ui`: `Button` (primary, secondary, ghost, danger; `sm`, `md`; loading
state), `TextField` (label, hint, error, textarea), `Alert` (danger, success, info), `Card`,
`Avatar` (image or initials), `Tag` (mono chip), `Dialog` (native `<dialog>`), `ThemeToggle`.
Icons: Phosphor, `light` weight, 16 to 24px. Every icon-only button has an `aria-label`.

## Rules

- Forms: label above field, error under the field, one general alert at the top only for errors
  the API did not attribute to a field. Submit buttons show a spinner and stay disabled while busy.
- Empty states say what will appear and, where possible, how to add the first item.
- No emoji, no illustrations, no gradients on surfaces.
