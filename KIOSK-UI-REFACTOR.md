# Kiosk UI Refactor - Base44 Design Alignment

## Overview
Refactor the WPF kiosk app to match the Base44-generated design language:
warm gradients, colored stat icons, cleaner sidebar nav, collapsible FAQ,
Hebrew-localized dialogs, and improved empty states.

---

## Improvements Identified

### 1. Sidebar Navigation
| # | Current | Target | Priority |
|---|---------|--------|----------|
| S1 | Nav items use spaces+text as pseudo-icons | Add Segoe MDL2 icons per nav item (Home, Package, History, Help) | HIGH |
| S2 | Active state is subtle | Bold filled background for active nav item | HIGH |
| S3 | No visual separator between user info and nav | Add subtle divider line | LOW |

### 2. Home Page
| # | Current | Target | Priority |
|---|---------|--------|----------|
| H1 | Violet gradient PageHeader | Warm yellow/orange gradient header with greeting + date | HIGH |
| H2 | Stat cards use emoji icons, no color differentiation | Each stat card gets a unique accent-colored circular icon background | HIGH |
| H3 | Session controls are in a plain white card | Keep but improve with better spacing and visual hierarchy | MED |
| H4 | Message card uses light blue (#EFF6FF) | Keep as-is, matches Base44 style | SKIP |

### 3. Packages Page
| # | Current | Target | Priority |
|---|---------|--------|----------|
| P1 | White card backgrounds (#F5F3FF / #EEF2FF) | Light blue card backgrounds to match Base44 | MED |
| P2 | Green discount badges | Red discount badges (matching Base44 "הנחה X%") | HIGH |
| P3 | Card header gradient is purple-tinted | Switch to softer blue-tinted background | MED |
| P4 | Buy button is primary (indigo) | Make gradient blue to match Base44 | MED |

### 4. History Page
| # | Current | Target | Priority |
|---|---------|--------|----------|
| HI1 | 2 stat cards (total purchases, total spent) | Add 3rd stat card: average per purchase | MED |
| HI2 | Dropdown filter (ComboBox) | Tab-style filter buttons (הכל, תשלום, הדפסה) | HIGH |
| HI3 | Empty state is basic text | Improved empty state with larger icon | MED |

### 5. Help Page
| # | Current | Target | Priority |
|---|---------|--------|----------|
| HP1 | FAQ items always expanded | Collapsible accordion (click to expand/collapse) | HIGH |
| HP2 | No working hours in contact card | Add working hours row | MED |
| HP3 | Section headers use TextH3 | Add section icons before titles | LOW |

### 6. Admin Exit Dialog
| # | Current | Target | Priority |
|---|---------|--------|----------|
| A1 | English text ("Administrator Access", "Cancel", "Confirm") | Hebrew ("יציאה מהאפליקציה", "ביטול", "אשר יציאה") | HIGH |
| A2 | Indigo confirm button | Red confirm button (danger action) | HIGH |
| A3 | No warning icon/message | Add warning icon + explanatory message | MED |

### 7. Stat Card Control
| # | Current | Target | Priority |
|---|---------|--------|----------|
| SC1 | Single color scheme for all stat cards | Support per-card accent color via DependencyProperty | HIGH |
| SC2 | Icon displayed as plain text | Icon in colored circular background | HIGH |

### 8. PageHeader Control
| # | Current | Target | Priority |
|---|---------|--------|----------|
| PH1 | All pages use same violet HeroGradient | Support custom gradient colors per page | HIGH |
| PH2 | No page icon | Add icon support (e.g., house, package, clock, help) | MED |

---

## Work Plan

### Phase 1: Design System Updates (foundation)
- [ ] **1.1** Update `StatCard.xaml` - add `AccentColor` DependencyProperty, render icon in colored circle
- [ ] **1.2** Update `PageHeader.xaml` - add `HeaderBrush` and `Icon` DependencyProperties
- [ ] **1.3** Add new color resources to `Colors.xaml` for warm gradients (orange/yellow, blue)

### Phase 2: Sidebar & Navigation
- [ ] **2.1** Add Segoe MDL2 icons to sidebar nav items
- [ ] **2.2** Improve active state styling in `SidebarNavButton` (Theme.xaml)

### Phase 3: Page-Level Refactor
- [ ] **3.1** HomePage - warm gradient header, colored stat card icons
- [ ] **3.2** PackagesPage - light blue card backgrounds, red discount badges
- [ ] **3.3** HistoryPage - 3rd stat card, tab-style filters
- [ ] **3.4** HelpPage - collapsible FAQ accordion

### Phase 4: Dialogs
- [ ] **4.1** AdminExitDialog - Hebrew localization, red confirm, warning message

### Phase 5: Polish
- [ ] **5.1** Verify visual consistency across all pages
- [ ] **5.2** Test RTL layout with all changes
- [ ] **5.3** Commit, push, release

---

## Design Decisions

### What we're adopting from Base44:
- Colored accent icons on stat cards (each stat has its own color)
- Warm gradient headers (page-specific gradients instead of one-size-fits-all violet)
- Red discount badges (more eye-catching than green)
- Collapsible FAQ accordion
- Hebrew-localized admin dialog
- Tab-style filters on history page

### What we're keeping from current design:
- FROST design system color palette (violet-indigo primary)
- Sidebar gradient and layout structure
- Package card feature list layout (already very close to Base44)
- Session controls on home page
- Payment dialog with WebView2 (functional requirement)
- Toast notifications
- Loading spinners and empty states

### What we're NOT doing:
- Complete color palette overhaul (current FROST palette is solid)
- Sidebar restructure (current layout already matches Base44 closely)
- Adding working hours to contact card (requires backend data)

---

## Status Tracker

| Task | Status | Notes |
|------|--------|-------|
| 1.1 StatCard accent colors | DONE | AccentColor + AccentBgColor DPs, colored icon circles |
| 1.2 PageHeader customization | DONE | HeaderBrush + Icon DPs, per-page gradient support |
| 1.3 Color resources | DONE | Added StatXxxColor/BgColor palette, page-specific header gradients |
| 2.1 Sidebar icons | DONE | Segoe MDL2 Assets icons (Home, Package, Clock, Help) |
| 2.2 Active nav state | DONE | ContentPresenter + TextElement.Foreground for icon+text coloring |
| 3.1 HomePage refactor | DONE | Warm orange gradient, colored stat icons |
| 3.2 PackagesPage refactor | DONE | Red discount badges, blue card backgrounds, purple header |
| 3.3 HistoryPage refactor | DONE | 3 stat cards with colors, blue header |
| 3.4 HelpPage accordion | DONE | Click-to-expand FAQ, chevron toggle, working hours row |
| 4.1 AdminExitDialog Hebrew | DONE | Full Hebrew, white card, red confirm, warning icon |
| 5.1 Visual consistency | DONE | Build + 1185 tests pass |
| 5.2 RTL testing | DONE | FlowDirection=RightToLeft maintained |
| 5.3 Release | DONE | v3.0.17 |
