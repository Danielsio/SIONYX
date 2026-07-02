# Firebase RTDB Cleanup Plan

**Date:** 2026-02-17
**Status:** Executing

---

## 1. RTDB vs Firestore Decision

**Recommendation: Stay with RTDB.** Here's why:

| Factor | RTDB | Firestore |
|--------|------|-----------|
| Real-time subscriptions | SSE (lightweight, kiosk uses REST) | Heavier SDK required |
| Data shape | Flat JSON tree — fits our model | Subcollections (overkill) |
| Query complexity | Simple reads by path — sufficient | Complex queries not needed |
| Scale | ~10 PCs, ~100 users — trivially handled | Designed for millions+ |
| Pricing | $1/GB stored, bandwidth-based | Per-read/write pricing |
| Auth rules | Path-based, already working | More powerful but unnecessary |
| Kiosk REST API | Native `.json` endpoint | Requires Firestore REST (verbose) |
| Offline sync | Not needed (kiosk is always online) | Main advantage — irrelevant |

**Bottom line:** Firestore would be over-engineering. Our data is <10KB, flat, and the
real-time features (session status, force logout, messages) work perfectly with RTDB's
SSE-based listeners. No migration needed.

---

## 2. `public/latestRelease` — Keep It

The web admin Settings page uses `public/latestRelease` to show the current installer
version and provide a download link (`downloadService.js`). The upload script writes
here on every release. It's publicly readable (no auth needed), which is intentional.

**Verdict:** Keep. Tiny data (<200 bytes), actively used by the web dashboard.

---

## 3. Cleanup Targets

### 3a. Messages — DELETE ALL (26 test messages)

All messages are test data from Jan 4:
- "בדיקה של הודעה", "הודעה 2", "s", "s", "s", "s", "s", "ש'ג", etc.
- All read, all between admin and themselves
- No production value

**Action:** Delete `organizations/sionov/messages` entirely.

### 3b. Stale Computer — DELETE

`ac361bec567a` — old computer registration from Feb 10, no user, no `isActive` field.
Likely from the Python kiosk era with different device ID generation.

**Action:** Delete `organizations/sionov/computers/ac361bec567a`.

### 3c. Users — Remove Redundant Fields

| Field | Present on | Action | Reason |
|-------|-----------|--------|--------|
| `correlation_id` | Admin | DELETE | Registration artifact, never queried |
| `createdBy` | Admin, Supervisor | DELETE | Registration artifact, never queried |
| `roleMigratedAt` | All users | DELETE | One-time migration done, never queried |
| `forceLogoutTimestamp` | l9PAI... | DELETE | Stale, force logout already handled |
| `lastComputerLogout` | Admin | DELETE | Never read by kiosk or web |

Fields to KEEP:
- `isAdmin` — used in RTDB security rules
- `role` — used in web dashboard UI
- `isLoggedIn`, `isSessionActive` — core session state
- `remainingTime`, `printBalance` — core business data
- `currentComputerId`, `sessionStartTime` — live session data
- `passwordResetAt/By` — audit trail, keep

### 3d. Message Schema — Remove Redundant Fields

When messages are recreated going forward, these fields are redundant:
- `id` — duplicates the Firebase push key (the parent key)
- `orgId` — duplicates the path (`organizations/{orgId}/messages/...`)

**Action:** Update web `chatService.js` to stop writing `id` and `orgId`.
Update kiosk ChatService if it reads these fields.

### 3e. Computer Schema — Remove Redundant Fields

- `deviceId` — duplicates the Firebase key (`computers/{deviceId}`)

**Action:** Stop writing `deviceId` in `ComputerService.RegisterComputerAsync`.

### 3f. Packages — Replace with Realistic Ones

Current packages are test data ("1", "דקות", etc.). Replace with realistic
internet cafe packages:

| Name | Minutes | Prints (₪) | Price | Validity |
|------|---------|-------------|-------|----------|
| שעה בודדת | 60 | 10 | ₪15 | 1 day |
| חבילת 5 שעות | 300 | 30 | ₪50 | 7 days |
| חבילת 20 שעות | 1200 | 50 | ₪150 | 14 days |
| חופשי חודשי | 6000 | 100 | ₪300 | 30 days |
| חבילת הדפסות | 0 | 50 | ₪40 | 30 days |

---

## 4. Execution Order

1. Run cleanup script (Python + firebase-admin)
2. Remove redundant field writes from kiosk code
3. Remove redundant field writes from web code
4. Commit code changes
5. Deploy web (if changed)
