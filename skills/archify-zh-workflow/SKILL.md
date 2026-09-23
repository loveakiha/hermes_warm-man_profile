---
name: archify-zh-workflow
description: CJK workflow diagrams with Archify. Broken-package fix.
metadata:
  author: hermes
---

# Archify Chinese Workflow Authoring

Companion to the `archify` skill for workflow-type diagrams with Chinese content. All base invariants (schema v2, quality_profile showcase, no invented subtitles/legends, validate-before-deliver, separate the three evidence claims) come from `archify`; this skill carries what the base skill omits for CJK and for broken packages.

## Package integrity first

- Before any `validate`/`deliver`, confirm the package directory contains `bin/`, `schemas/`, and `renderers/`; run `node bin/archify.mjs doctor` — it lists missing files. When the installed skill package is incomplete (missing renderers/schemas), `validate` fails with unclassified-renderer errors and `doctor` confirms it: clone the official repo (`git clone --depth 1 https://github.com/tt-a1i/archify`) into the scratch dir and run bin/ from there. The local skill package is read-only context, not an execution base.

## CJK composition rules

- Keep node `width` at the default 132: wider nodes inflate the viewBox, and at the 1440px proof viewport the projected font size falls below the 6px minimum and every CJK sublabel fails composition. Diagnose by running `validate` with `--layout-json` and reading the returned `viewBox`.
- Keep CJK `sublabel`s to ~12 characters or fewer, single line. CJK glyphs are wide, so long sublabels wrap inside the 132px node and the renderer shrinks them below 6px. Put longer detail in `tag`, in card `items`, or in edge labels instead — those surfaces are not subject to the projection check.
- Layout contract: columns `0..5`, main path column monotonic non-decreasing; multiple nodes may stack in one column across lanes. Side branches (e.g. a database lane) attach with dashed edges from the nearest main-path node.

## Evidence and delivery

- `visual-check` exits `skipped` in headless environments without Chromium; install with `npx agent-browser install --with-deps` when real browser evidence is needed. Fallback: verify the delivered HTML textually — title, every node label, every edge label, exactly one SVG block, and the viewer runtime string all present — and report visual-check as skipped, never as passed.
- A delivery is only success when the receipt reports all 9 artifact checks with 0 errors and 0 warnings; the spec and artifact SHA-256 receipts are the handoff evidence.
- Never write the delivered HTML into the user's project directory without explicit confirmation; if the confirm prompt times out, render into the workspace and send the file to the user instead.
