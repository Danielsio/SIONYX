# UI Premium Improvements (Desktop)

This document captures UI upgrade tasks based on the current screenshots.
Goal: "premium of premium" visual polish and layout quality.

Status legend:
- [x] Complete
- [~] In progress
- [ ] Not started
- [!] Needs evaluation in UI after changes

Progress log:
- 2026-01-22: Added responsive grids, expanded headers, and refined card surfaces.
- 2026-01-22: Added featured package badge, support note, copy actions, and accent styling.
- 2026-01-22: Refined sidebar branding, card hover states, and reduced emoji usage.
- 2026-01-22: Centered Home action CTA and tightened packages card vertical rhythm.

## Cross‑App Foundations

- [~] Upgrade typography scale: stronger contrast between H1/H2/body; increase base size for readability on large displays.
- [~] Introduce a consistent spacing rhythm (8/12/16/24/32/48) and enforce it across pages.
- [~] Unify icon style (single set: outline vs filled) and remove mixed emoji/icon styles.
- [~] Define a global surface system: base background, elevated cards, and accent panels with consistent borders and shadows.
- [~] Normalize shadows: fewer, softer layers with consistent blur/spread across components.
- [~] Add subtle background texture/gradient to reduce flatness on large empty areas.
- [~] Ensure consistent corner radius hierarchy (small inputs, medium cards, large hero).

## Main Window / Sidebar

- [~] Increase sidebar visual hierarchy: larger active indicator, clearer hover/active contrast, optional section grouping.
- [x] Improve brand area: align logo, name, and menu icon with more breathing room and premium typography.
- [x] Standardize sidebar icon placement so labels align consistently.
- [x] Replace the small logout button with a wider, primary‑secondary treatment that feels deliberate.

## Home Page

- [x] Balance the stats cards: center alignment across the row and tighten internal padding.
- [x] Add visual emphasis to primary metrics (time + balance) using a tonal background or top border.
- [x] Improve the action card: make CTA larger, align text and CTA on a clean grid, reduce empty height.
- [ ] Add optional secondary info row (e.g., usage tip, last session, account status) to reduce empty space.

## Packages Page

- [x] Reduce tall empty card bodies; rework cards to bring price and CTA higher.
- [x] Create a structured grid with consistent card height alignment and tighter vertical rhythm.
- [x] Ensure proportional layout: number of packages sets columns so each card takes an equal share of the packages section (e.g., 2 cards = 50% each, 4 cards = 25% each).
- [x] Add a "featured" or "best value" badge to one package for hierarchy.
- [x] Upgrade price presentation: large price, smaller currency, clear discount treatment with consistent typography.
- [~] Add micro‑details: subtle separators, iconography for features, and a clearer "value" summary.

## History Page

- [x] Turn filters into a cohesive toolbar (single container, consistent heights, shared background).
- [x] Add column alignment or timeline styling so rows feel structured, not floating.
- [x] Add a lightweight empty‑state illustration or branded icon to reduce plain look.
- [x] Improve purchase cards with stronger typography and spacing; reduce card height slightly.

## Help Page

- [~] Align contact cards to a clean grid with equal widths and consistent icon sizes.
- [x] Simplify FAQ cards: reduce height, tighten spacing, add subtle dividers for clarity.
- [x] Add a short "Support hours" or "Response time" note to increase trust.
- [x] Make contact actions clearer (tap to copy / click to email) with hover affordances.

## Visual Polish / Details

- [~] Replace mixed emoji with a cohesive icon set for modern consistency.
- [~] Adjust gradients to be more subtle and refined (avoid overly saturated hero bars).
- [~] Add micro‑interactions (hover lift, focus glow, pressed states) on cards and buttons.
- [~] Enforce consistent padding on all cards and sections to remove visual "wobble."

## Responsiveness / Large Screens

- [~] Use adaptive max‑widths on sections to avoid over‑stretching text on ultra‑wide displays.
- [~] Keep the hero/header full‑width, but constrain content inside to a premium readable width.
- [~] Use responsive grid column counts for cards to eliminate awkward empty columns.

## Needs Evaluation (after next run)

- [!] Verify package cards fill the section proportionally (2=50%, 3=33%, 4=25).
- [!] Check alignment of stat cards and action card spacing on Home.
- [!] Review empty states on History and Help for balance and hierarchy.
- [!] Confirm icon style consistency after emoji removal.
- [!] Validate Home action card height and CTA prominence.
- [!] Check Packages card height and vertical density (too tall vs content).
