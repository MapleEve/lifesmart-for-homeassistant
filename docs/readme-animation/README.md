# LifeSmart README Animation Workflow

This folder contains the reusable Remotion template used to generate the README animated image sets.

## Structure

- `src/data.ts`: localized, replaceable text for every README locale and section.
- `src/scene.tsx`: shared visual system and animation logic.
- `public/source/{locale}/{slug}.png`: preserved copies of the previous README PNGs, used as visual/source references inside the animated scenes.
- `scripts/render-all.mjs`: renders MP4 intermediates with Remotion and converts them to optimized GitHub-compatible GIFs.
- `scripts/render-locale-stills.mjs`: renders one keyframe still per locale for visual QA.
- `scripts/validate-assets.mjs`: checks GIF dimensions, file sizes, README references, source copies, and text-length bounds.

## Commands

```bash
npm install
npm run render:all
npm run still:locales
npm run validate
```

Generated intermediates are ignored by the root `.gitignore`; source data and source PNG copies are trackable.

## gptimage-2 placeholder

No usable local/API `gptimage-2` route was available during this implementation. The current backdrops are deterministic Remotion shapes. If a route becomes available later, generate only abstract brand plates, never fake Home Assistant UI screenshots.

Suggested prompt:

```text
Create an abstract LifeSmart x Home Assistant README backdrop plate. Visual style: premium smart-home command center, emerald and cyan energy mesh, subtle glass panels, no readable UI text, no fake screenshots, no logos except replaceable geometric brand mark space, high contrast, GitHub README-safe, 16:9.
```
