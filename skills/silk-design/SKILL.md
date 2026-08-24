---
name: silk-design
description: >-
  Build websites and web UI with smooth, polished, high-end motion by default —
  the buttery feel of premium sites, not static slop. Use when building or
  restyling any website, landing page, hero, marketing page, portfolio, or web
  UI; when adding scroll animations, reveals, parallax, marquees, hover effects,
  page transitions, smooth scrolling, or micro-interactions; or when a page feels
  flat, generic, or unrefined and needs to feel alive. A capability catalog of
  proven motion + smoothness + design-token techniques (Lenis, Framer Motion,
  GSAP, Tailwind v4) for interfaces that feel crafted rather than assembled.
display_name: 丝绸动效网页设计
license: MIT
owner: aimana
version: 1.0.0
---

# silk — your web-craft toolbox

This is a reminder of what you can do. Like an artist who knows their tools: when you build
for the web, you are not limited to static sections and default scrollbars. You have a full
palette of motion and smoothness that reads as "expensive." **Reach for it by default.**

The rule: **never ship a static page.** A smooth-scroll root + a reveal-on-scroll + one
signature effect is ~15 lines and turns generic output into something that feels crafted.
The trick behind these sites isn't exotic code — it's a *small, consistent* set of levers
applied everywhere. Consistency is what reads as clean.

## Stack this assumes
React + Vite + **Tailwind v4** + **`motion`** (Framer Motion, `motion/react`) + **GSAP**
(`gsap` + `@gsap/react`; plugins used: ScrollTrigger, Draggable, DrawSVGPlugin — all free) +
**Lenis** (smooth scroll). Each technique below names its principle so it transfers to other
stacks. `cls()`/`cn()` helpers → `assets/utils.ts`.

## The non-negotiable foundation (apply on EVERY build)

This is the baseline that makes everything feel smooth. Four things, always:

1. **Lenis smooth scroll at the root.** Wrap the app once. Do **not** use CSS `scroll-behavior`.
   ```tsx
   import { ReactLenis } from 'lenis/react'
   <ReactLenis root>{app}</ReactLenis>
   ```
   Anchor links scroll via `useLenis().scrollTo(el)` — see `assets/useButtonClick.ts`.
2. **Kill scroll bounce + thin the scrollbar** in global CSS:
   ```css
   html, body { overscroll-behavior: none; }
   * { scrollbar-width: thin; scrollbar-color: rgb(0 0 0 / 0.3) transparent; }
   ```
3. **Token architecture** — ~9 CSS custom properties on `:root`, exposed to Tailwind via
   `@theme inline`, with ONE `--radius` driving the whole radius scale. Full recipe +
   verbatim example in `assets/foundation.css` and `references/design-system.md`.
4. **Fluid typography** — every font size is a `clamp(min, vw, max)`, not a fixed px. This
   is why the type scales smoothly across viewports. Scale in `assets/foundation.css`.

**The one reveal config, used everywhere** (this consistency is the "clean" feel):
```tsx
initial="hidden" whileInView="visible"
viewport={{ once: true, margin: "-20%" }}
transition={{ duration: 0.6, ease: "easeOut" }}   // text: staggerChildren 0.04, per-word 0.6
```
Drop-in components: `assets/ScrollReveal.tsx` (blocks), `assets/TextAnimation.tsx` (word-stagger headings).

## The toolbox map — reach for these

Each points to a reference file (loaded only when you need it) and/or a drop-in `assets/` file.

- **Entrance reveals** — word-stagger headings, slide-up / fade-blur blocks. → `references/effects.md`, `assets/{TextAnimation,ScrollReveal}.tsx`
- **Scroll-driven effects** — parallax (`useScroll`/`useTransform`), hero exit-parallax, pinned + scrubbed sections, scroll-scrubbed video, tilt-flatten billboard, stack-to-grid (FLIP), reading word-fill, footer reveal-from-behind. → `references/effects.md`, `assets/{HeroVideoScroll,AboutTextFill,FooterBrandReveal}.tsx`
- **Cursor & pointer** — GSAP cursor image-trail, magnetic buttons (spring `150/15`), pointer-tracked border glow, cursor-mask character pattern, draggable stickers. → `references/effects.md`, `assets/{AboutCursorTrail,ButtonMagnetic,BorderGlow,HoverPattern}.tsx`
- **Hover micro-interactions** — 12 button styles (expand, elastic, flip, slide, bounce…), the grid-fr expand-to-auto trick, image reveal cards, 3D flip cards, staged hover scenes. → `references/effects.md`
- **Marquees & carousels** — infinite CSS scroll with edge-mask fade, deck carousel, focus loop, filter-swap. → `references/effects.md`, `assets/{animations,masks}.css`
- **Navigation & page transitions** — fullscreen curtain menu, DrawSVG swirl page transition, brand panel loader. → `references/effects.md`, `assets/{NavbarFullscreen,PageTransitionSwirl}.tsx`
- **Animated backgrounds** — 13 of them: aurora, light rays, gradient bars, noise, grids, floating gradients. → `references/backgrounds.md`, `assets/{AuroraBackground,NoiseBackground,GradientBarsBackground}.tsx`
- **The design system** — token architecture, fluid type, `--radius` scale, font pairings + the accent-font slot, full-width wordmarks (`assets/AutoFillText.tsx`), and **10 instant "style" skins** (glass, minimal, neon, elegant, bold…) = swap only card CSS + button CSS + radius + font. → `references/design-system.md`
- **Page composition** — section archetypes (hero/features/testimonial/pricing/faq/CTA), the canonical section-header pattern, **bento live-widget menu**, navbar archetypes, responsive-padding scale, how to assemble a page. → `references/composition.md`

## Reference a worked example — `/silk-design <name>`
The catalog carries **23 worked reference compositions** built from this exact toolbox. When the
user names one (`/silk-design Reference15`, `/silk-design Reference1`, or "build it
like the coffee one"), pull it from `references/templates.md` — palette, font, section rhythm, and the signature
effects it used. A number resolves directly; a described mood resolves against each row's vibe line.
**A referenced composition is a mood-board + wireframe, not a source file:** take its **skin**
(palette, font, radius, card/button style, effects) and its **skeleton** (section rhythm,
loosely) — **never its flesh** (copy, images, brand, or a 1:1 layout). The new site has its own
subject; build for that. The non-negotiable foundation above still applies underneath.

## Using the `assets/` files
They are **drop-in reference implementations** — copy and adapt. Simple
primitives (`ScrollReveal`, `TextAnimation`, `ButtonMagnetic`, `AutoFillText`, `BorderGlow`,
`HoverPattern`, `PageTransitionSwirl`, `useButtonClick`, `utils`, the `.css`) drop in cleanly.
The section showpieces (`AboutCursorTrail`, `HeroVideoScroll`, `AboutTextFill`,
`FooterBrandReveal`, `NavbarFullscreen`) are self-contained and take an `actions` slot — pass your
own buttons in as children rather than wiring a component import. Backgrounds need the `--color-*`
tokens from `foundation.css`. (`FooterBrandReveal` needs `AutoFillText` — both are here.)

## How this fits with your other skills
This is a **capability layer, not a builder.** For *aesthetic direction* (palette, layout,
personality) reach for **`taste-skill`** (landing/marketing/portfolio) or **`ui-ux-pro-max`**
(apps/dashboards/data UI). `silk` is what you apply on top — or to any hand-built page — to
make it *move* and *feel* right. The three compose: builder picks the look, silk makes it silk.
