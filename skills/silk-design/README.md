# silk-design

A Claude Code skill for building web interfaces that move well.

Most generated pages come out static. Default scrollbars, sections that just appear,
hover states that do nothing. This is a catalog of motion and design-token techniques,
and it tells the agent to reach for them by default rather than only when asked.

## Results

Six sites built with this skill, they are all in German tho:

- [The Hair House](https://the-hair-house.bendrape1.workers.dev/), hair studio for women
- [Kronberger](https://kronberger-website.bendrape1.workers.dev/), bakery
- [The Coffee Club 29](https://coffee-club29.bendrape1.workers.dev/), café
- [Mina](https://mina-cafe.com/), café
- [Café OPITZ im Goethehaus](https://cafe-opitz.bendrape1.workers.dev/), café
- [Oeffner Media](https://www.oeffnermedia.com/), Social Media Agency
- [Orthotrain](https://orthotrain-frankfurt.bendrape1.workers.dev/), Physio-Therapy
- [F-Studios](https://f-studios-six.vercel.app/), Nail Studio

## Install

```
git clone https://github.com/bendrape1-byte/silk-design ~/.claude/skills/silk-design
```

Then ask your coding agent to build a website using the /silk-design skill and give it additional information such as:
- Who you are (who this website is for)
- What the use case of the website is
- Add any additional information, photos or videos for it to use

## What's in it

A foundation to apply on every build: Lenis smooth scroll at the root, scroll bounce
killed, a nine-token color system exposed to Tailwind, and fluid `clamp()` type. Four
things, about fifteen lines, and they do most of the work.

Then an effects catalog with the actual numbers in it. Spring constants, easing curves,
stagger intervals, scroll offsets. Word-stagger headings, parallax, pinned and scrubbed
sections, scroll-scrubbed video, cursor image-trails, magnetic buttons, curtain menus,
marquees. The five larger components in `assets/` are written out in full; the rest are
recipes precise enough to type from, which keeps the files small enough to load only
when they are needed.

Thirteen animated backgrounds. Three ship as components.

A design system built on one `--radius` knob that drives the whole scale, with font
pairings and ten style skins you switch by swapping three CSS blocks.

Twenty-three reference compositions, each with a palette, a type choice, a section rhythm
and an effect set. They are starting points, not templates to fill in.

## Stack

React + Vite, Tailwind v4, `motion` (Framer Motion), GSAP with ScrollTrigger, Draggable
and DrawSVG (all free plugins), and Lenis. Each technique names the principle behind it, so the
snippets are portable even when the stack is not.

## Notes

Written from scratch. The components in `assets/` are original implementations of publicly
documented techniques (GSAP ScrollTrigger, CSS clip-path, SVG filters) and contain no
third-party code, assets, or branding. The palettes and type values under `templates/` are
plain CSS custom properties.

MIT licensed. See [LICENSE](LICENSE).
