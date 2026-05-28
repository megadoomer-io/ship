# Design System: Ship

Ship extends the [megadoomer.io design system](https://github.com/megadoomer-io/portal/blob/main/DESIGN.md) defined in Portal's `DESIGN.md`. All shared tokens (colors, typography, spacing, border radius, motion, nav, footer, breadcrumbs) are inherited via `shared.css`. This document covers Ship-specific component patterns and conventions.

## Product Context

- **What this is:** Dashboard for AI-curated Obsidian vault content (journal entries, weekly summaries, retros, active work)
- **Who it's for:** Small group with tiered access (cargo < crew < officers < captain)
- **Space:** Personal productivity dashboard / team status visibility tool
- **Project type:** Authenticated web app with role-based views
- **Shared with:** [portal](https://github.com/megadoomer-io/portal) via `shared.css`

## Relationship to Portal's Design System

Ship inherits and must not duplicate:

| Token Category | Source | Ship Usage |
|---------------|--------|------------|
| Color palette | `shared.css` `:root` / `[data-theme]` | All `var(--*)` color references |
| Typography | `shared.css` `--font-mono`, `--font-sans` | Headings, labels, body text |
| Spacing scale | `shared.css` `--space-*` | Layout spacing |
| Border radius | `shared.css` `--radius-*` | Cards, badges, buttons, inputs |
| Nav, footer, breadcrumbs | `shared.css` `.shared-*` | Site-wide chrome |

Ship's `style.css` only defines component-specific styles. If a token needs to change, change it in `shared.css` (Portal repo) so both apps update together.

## Content Rendering

Ship renders Obsidian vault markdown via mistune. The `.rendered-content` class scopes all vault-originated HTML. This is the most visually complex part of Ship.

### Rendered Content Hierarchy

| Element | Font | Size | Color | Notes |
|---------|------|------|-------|-------|
| h1 | `--font-mono` | 1.3rem | `--accent` | Green heading, signals top-level sections |
| h2 | `--font-mono` | 1.1rem | `--text` | Standard subheading |
| h3 | `--font-mono` | 0.95rem | `--text-muted` | Tertiary, visually recedes |
| p, li | inherited sans | 1rem | `--text` | Body text, readable line-height |
| code (inline) | `--font-mono` | 0.85em | `--text` on `--bg` | Subtle background highlight |
| pre (block) | `--font-mono` | inherited | `--text` | Bordered, padded, horizontal scroll |
| blockquote | inherited | inherited | `--text-muted` | 3px `--accent` left border |
| table | inherited | 0.9rem | `--text` | Full-width, collapsed borders |
| a | inherited | inherited | `--accent` | Underline on hover only |

### Tags

Obsidian `#tags` are converted to styled inline elements:

```css
.tag {
    font-family: var(--font-mono);
    font-size: 0.8em;
    color: var(--accent-secondary);    /* magenta */
    background: color-mix(in srgb, var(--accent-secondary), transparent 90%);
    border-radius: var(--radius-sm);
}
```

Tags use `--accent-secondary` (magenta) to visually distinguish them from links (`--accent` green).

### Task Lists

Obsidian task list items (`- [ ]` / `- [x]`) render as checkbox lists. The checkbox items have no list-style marker and are offset to align with the checkbox input.

## Component Patterns

### Cards

The primary content container. Used on every page.

```css
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);    /* 6px */
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
```

No hover effect on cards (they're content containers, not interactive targets). Compare with Portal's service cards which have hover border-color transitions because they're clickable.

### Badges

Small uppercase labels that classify content types. Two variants:

| Variant | Color Token | Usage |
|---------|-------------|-------|
| `.badge-retro` | `--accent` (green) | Retro summary entries |
| `.badge-weekly` | `--info` (blue) | Weekly summary entries |

Both use `color-mix()` to derive a 15% tinted background and 30% tinted border from their color token. This ensures badge colors automatically adapt to light/dark mode without hardcoded values.

```css
.badge {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.2em 0.6em;
    border-radius: var(--radius-sm);
}
```

### Timeline (Porthole)

Vertical stack of timeline cards. Each card has a header row (badge + date) and body (title + rendered content).

```
[ badge ] [ date right-aligned ]
Title
Rendered markdown content
```

- `.timeline-header`: flexbox row, `gap: 0.75rem`
- `.timeline-date`: `--font-mono`, 0.8rem, `--text-muted`
- `.timeline-title`: `--font-mono`, 1rem, weight 600

### Period Filter (Observation Deck)

Row of toggle buttons for time range selection: Past Week / Past Month / All Time.

```css
.period-btn {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
}

.period-btn.active {
    color: var(--accent);
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent), transparent 90%);
}
```

Active state uses the same `color-mix()` pattern as badges: accent color at 10% opacity for background.

### Hierarchical Feed (Observation Deck)

Collapsible week groups using native `<details>/<summary>`. Each week contains an optional weekly summary and daily entry groups.

- Week summary lines: `--font-mono`, 0.9rem, weight 600, hover changes color to `--accent`
- Day summary lines: `--font-mono`, 0.85rem, `--text-muted`, hover to `--text`
- Week content indented with `padding-left: 1rem`

### Retro Cards (Captain's Log)

Collapsible retro entries with metrics table. First entry defaults open.

- Retro summary row: flexbox with badge + title + date
- Metrics table: auto-width (not full-width), `--font-mono`, uppercase headers
- "View activity for this week" link at bottom

### View-As Controls (Floating Pill)

Fixed-position controls at bottom-left, matching Portal's `.floating-controls` pattern. Only visible when the user's actual role allows impersonation.

```css
.floating-controls {
    position: fixed;
    bottom: 1rem;
    left: 1rem;
    z-index: 200;
}
```

Each role option is a `.btn-toggle` button. The active role (when viewing-as) gets `--accent` border and tinted background. Controls adapt to smaller padding on mobile.

### Login Button (401 page)

```css
.btn-login {
    font-family: var(--font-mono);
    background: var(--accent);        /* green, not magenta */
    color: var(--bg);
    border-radius: var(--radius-md);
}
```

Ship uses `--accent` (green) for its login CTA, unlike Portal which uses `--accent-secondary` (magenta). The rationale: Ship's 401 page is utilitarian ("sign in to continue"), while Portal's login is a primary marketing CTA. Green feels like "proceed" rather than "buy."

### Error Pages

- **401**: "Welcome to Ship" + sign-in button. Minimal. Shows the shared nav with only Home link visible.
- **403**: Contextual messaging based on role state. When viewing-as, shows role switch suggestions. When at cargo level, uses nautical theming ("You're currently in the cargo hold").
- **404**: "Nothing at this heading. Check your course and try again." Shows username if authenticated.

## Page-Level Typography

| Element | Font | Size | Weight | Color | Notes |
|---------|------|------|--------|-------|-------|
| Page h1 | `--font-mono` | 0.75rem | 700 | `--accent` | Uppercase, letter-spacing 0.1em, border-bottom separator |
| Page blurb | inherited sans | 0.9rem | 400 | `--text-muted` | Below h1, describes the page's purpose |
| Section h2 | `--font-mono` | 1rem | 600 | `--text` | Card-level headings |

Page headings (`h1.page-heading`) use Portal's group label style: small uppercase monospace with tracked letter-spacing and a green accent color with border-bottom separator. This matches Portal's `ADMIN`, `MEDIA`, etc. group labels. Each page has a one-line blurb in muted sans-serif below the heading.

Behind each page heading, a `::before` pseudo-element renders the heading text in the Irken alien font with a triple-layer green glow, using the same shared pattern defined in Portal's DESIGN.md (Irken font, `--title-shadow-opacity`, green text-shadow layers).

Ship's application differs from Portal's in one key way: the Irken shadow is much larger than the foreground text (2rem shadow behind 0.75rem heading), whereas Portal's hero shadow is roughly the same size as the readable text. The 2rem value was chosen arbitrarily during implementation and confirmed by the user as visually appealing. If this ratio needs to be revisited, the key variable is the `font-size` on `h1.page-heading::before`.

The Irken text uses `content: attr(data-irken)` so each page renders its own alien script. In light mode, opacity drops via `--title-shadow-opacity` (0.08 vs 0.25 in dark mode).

Error page headings (401, 403, 404) do not use `.page-heading` and remain at standard size without the Irken shadow.

## Content Width

Ship content area is 960px max-width (vs Portal's 1200px and shared.css's 1200px). The narrower width improves readability for the long-form markdown content that dominates Ship's pages.

## Spacing Tokenization Policy

Ship and Portal both use the `--space-*` token scale from `shared.css` for layout and structural spacing. Not all spacing values are tokenized -- the boundary is:

**Tokenized (layout/structural):**
- Container padding (`.content`, `.card`)
- Section margins and gaps (`.period-filter`, `.floating-controls`)
- Content indentation (`.week-content`, `.day-content`)
- Structural separators (`.rendered-content hr`)
- Code block padding (`.rendered-content pre`)
- Blockquote indentation

**Not tokenized (content rhythm / component-internal):**
- Rendered markdown inter-element spacing (0.75rem) -- consistent content typography rhythm with no exact token match
- Component-internal micro-spacing (badge padding, button padding, summary padding) -- em-based or component-specific
- Typography margins (heading margin-bottom) -- tied to font size relationships, not layout grid
- The 0.75rem (12px) value appears frequently but represents content rhythm, not layout spacing. Adding a token for it would add naming complexity without improving consistency, since it's already used uniformly.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-27 | Created Ship DESIGN.md as extension of Portal's system | Single source of truth for shared tokens, Ship doc covers Ship-specific patterns only |
| 2026-05-27 | Replaced all hardcoded colors with CSS variable references | Design system compliance: `#3498db` to `var(--info)`, `rgba()` to `color-mix()` |
| 2026-05-27 | Replaced all hardcoded border-radius with `--radius-*` tokens | Consistency with shared spacing/radius scale |
| 2026-05-27 | Green login CTA (not magenta like Portal) | Ship's 401 is utilitarian "proceed," not a marketing CTA |
| 2026-05-27 | 960px content width (not 1200px) | Readability for long-form markdown content |
| 2026-05-27 | Floating pill for view-as controls | Matches Portal's `.floating-controls` pattern, frees header from power-user controls |
| 2026-05-27 | Uppercase group-label h1 headings | Matches Portal's group label treatment (ADMIN, MEDIA, etc.) |
| 2026-05-27 | Irken font shadow on page headings | Shared pattern from Portal's design system. Shadow size (2rem) was arbitrary, confirmed by user. Differs from Portal's same-size approach. |
| 2026-05-28 | Migrated layout spacing to `--space-*` tokens | Design system compliance: raw rem values replaced with token references for all layout/structural spacing. Content rhythm (0.75rem) intentionally left as raw values. |
