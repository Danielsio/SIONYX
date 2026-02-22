# Easy Features to Add

## Web Admin (`sionyx-web/`)

### ~~FEAT-W1: Dark Mode Toggle~~ DONE
**Fix applied:** Added dark mode toggle (BulbOutlined/BulbFilled) in the header. Uses Ant Design 5 `theme.darkAlgorithm`. Preference persisted in Zustand store (localStorage). Sidebar, header, and content backgrounds adapt automatically.

---

### ~~FEAT-W2: Dashboard Charts (Revenue & Usage)~~ DONE
**Fix applied:** Added two recharts-based charts to OverviewPage:
- Revenue trend area chart (last 7 days, brand gradient colors)
- Package distribution donut chart (5 categories, brand palette)
Both wrapped in motion animations matching the page style.

---

### ~~FEAT-W3: Export Data to CSV/Excel~~ DONE
**Fix applied:** Created `src/utils/csvExport.js` utility. Added "ייצא CSV" button to UsersPage that exports filtered user data with proper Hebrew column headers and UTF-8 BOM for Excel compatibility.

---

### FEAT-W4: User Activity Timeline
**Effort:** ~2 hours  
**Status:** Pending — good candidate for next sprint.

---

### FEAT-W5: Real-time Notifications Bell
**Effort:** ~2 hours  
**Status:** Pending — requires Firebase RTDB listener integration.

---

### FEAT-W6: Search Across All Entities
**Effort:** ~2 hours  
**Status:** Pending — data is in Zustand stores, implementation is straightforward.

---

### ~~FEAT-W7: Page Transition Animations~~ DONE
**Fix applied:** Wrapped `<Outlet>` in `MainLayout.jsx` with `AnimatePresence mode="wait"` and `motion.div`. Smooth fade + slide on every page change using `location.pathname` as key.

---

### ~~FEAT-W8: Favicon and Meta Tags~~ DONE
**Fix applied:** Added Open Graph meta tags to `index.html`. Lang set to "he", dir set to "rtl".

---

## Kiosk App (`sionyx-kiosk-wpf/`)

### FEAT-K1: Session Usage Statistics
**Effort:** ~3 hours  
**Status:** Pending.

---

### FEAT-K2: Multi-language Support (English/Hebrew)
**Effort:** ~4 hours  
**Status:** Pending.

---

### FEAT-K3: Auto-Update Notification
**Effort:** ~2 hours  
**Status:** Pending — `public/latestRelease` path already exists.

---

## Cloud Functions (`functions/`)

### FEAT-F1: Payment Receipt Email
**Effort:** ~2 hours  
**Status:** Pending — consider Firebase Trigger Email extension.

---

### FEAT-F2: Admin Alert on Failed Payments
**Effort:** ~1 hour  
**Status:** Pending.

---

## DevOps

### FEAT-D1: Automated Release Notes
**Effort:** ~1 hour  
**Status:** Pending.
