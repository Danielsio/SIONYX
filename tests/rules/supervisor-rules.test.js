/**
 * Firebase Realtime Database security rules tests for the supervisor system.
 *
 * These tests validate that security rules enforce correct access control:
 * - Supervisors can read/write only what they should
 * - Admins retain their existing access
 * - Regular users cannot access supervisor paths
 * - Unauthenticated users are blocked
 *
 * Requires: Firebase Emulator running with RTDB
 *   firebase emulators:start --only database
 */

const {
  initializeTestEnvironment,
  assertSucceeds,
  assertFails,
} = require("@firebase/rules-unit-testing");
const fs = require("fs");
const path = require("path");

const PROJECT_ID = "sionyx-rules-test";
const RULES_PATH = path.resolve(__dirname, "..", "..", "database.rules.json");

const SUP_UID = "supervisor-1";
const ADMIN_UID = "admin-1";
const USER_UID = "user-1";
const OTHER_UID = "other-1";
const ORG_ID = "test-org";
const OTHER_ORG_ID = "other-org";

let testEnv;

beforeAll(async () => {
  const rules = fs.readFileSync(RULES_PATH, "utf-8");

  testEnv = await initializeTestEnvironment({
    projectId: PROJECT_ID,
    database: {
      rules,
      host: "127.0.0.1",
      port: 9000,
    },
  });
});

afterAll(async () => {
  if (testEnv) await testEnv.cleanup();
});

beforeEach(async () => {
  await testEnv.withSecurityRulesDisabled(async (context) => {
    const db = context.database();

    await db.ref().set({
      supervisors: {
        [SUP_UID]: {
          name: "Test Supervisor",
          phone: "0501234567",
          email: "0501234567@sionyx.app",
          createdAt: new Date().toISOString(),
          organizations: {
            [ORG_ID]: true,
          },
        },
      },
      organizations: {
        [ORG_ID]: {
          metadata: {
            name: "Test Org",
            status: "active",
            created_at: new Date().toISOString(),
          },
          users: {
            [ADMIN_UID]: {
              firstName: "Admin",
              lastName: "User",
              phoneNumber: "0501111111",
              isAdmin: true,
              role: "admin",
              remainingTime: 100,
              isSessionActive: false,
              createdAt: new Date().toISOString(),
            },
            [USER_UID]: {
              firstName: "Regular",
              lastName: "User",
              phoneNumber: "0502222222",
              isAdmin: false,
              role: "user",
              remainingTime: 60,
              isSessionActive: false,
              createdAt: new Date().toISOString(),
            },
          },
          packages: {
            "pkg-1": {
              name: "Basic",
              price: 50,
              minutes: 60,
              isActive: true,
            },
          },
          computers: {
            "comp-1": {
              computerName: "PC-1",
              isActive: true,
              lastSeen: Date.now(),
              userId: USER_UID,
            },
          },
          metadata: {
            name: "Test Org",
            status: "active",
            created_at: new Date().toISOString(),
          },
        },
        [OTHER_ORG_ID]: {
          metadata: {
            name: "Other Org",
            status: "active",
          },
          users: {
            "some-user": {
              firstName: "Other",
              lastName: "Person",
              phoneNumber: "0509999999",
              isAdmin: true,
              role: "admin",
              remainingTime: 0,
              isSessionActive: false,
              createdAt: new Date().toISOString(),
            },
          },
        },
      },
    });
  });
});

// ── Supervisor Self-Access ──────────────────────────────────────

describe("Supervisor own data", () => {
  test("supervisor can read their own supervisors/{uid} record", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(db.ref(`supervisors/${SUP_UID}`).get());
  });

  test("supervisor cannot read another supervisor's record", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(db.ref(`supervisors/${OTHER_UID}`).get());
  });

  test("supervisor cannot write to their own profile", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`supervisors/${SUP_UID}/name`).set("Hacked Name")
    );
  });

  test("unauthenticated user cannot read supervisor data", async () => {
    const db = testEnv.unauthenticatedContext().database();
    await assertFails(db.ref(`supervisors/${SUP_UID}`).get());
  });
});

// ── Supervisor blockedUsers Path ────────────────────────────────

describe("Supervisor blockedUsers", () => {
  test("supervisor can write to their own blockedUsers", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`supervisors/${SUP_UID}/blockedUsers/0502222222`).set({
        blockedAt: Date.now(),
        reason: "Spam",
        name: "Test User",
      })
    );
  });

  test("supervisor can remove from their own blockedUsers", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`supervisors/${SUP_UID}/blockedUsers/0502222222`).remove()
    );
  });

  test("supervisor cannot write to another supervisor's blockedUsers", async () => {
    const db = testEnv.authenticatedContext(OTHER_UID).database();
    await assertFails(
      db.ref(`supervisors/${SUP_UID}/blockedUsers/0502222222`).set({
        blockedAt: Date.now(),
      })
    );
  });

  test("supervisor can read their own blockedUsers", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`supervisors/${SUP_UID}/blockedUsers`).get()
    );
  });
});

// ── Supervisor Read Access on Supervised Org ─────────────────────

describe("Supervisor reading supervised org data", () => {
  test("can read users in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users`).get()
    );
  });

  test("can read packages in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/packages`).get()
    );
  });

  test("can read computers in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/computers`).get()
    );
  });

  test("can read metadata in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/metadata`).get()
    );
  });

  test("can read individual user in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}`).get()
    );
  });
});

// ── Supervisor CANNOT Read Non-Supervised Org ───────────────────

describe("Supervisor reading non-supervised org data", () => {
  test("cannot read users in non-supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${OTHER_ORG_ID}/users`).get()
    );
  });

  test("cannot read packages in non-supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${OTHER_ORG_ID}/packages`).get()
    );
  });

  test("cannot read metadata in non-supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${OTHER_ORG_ID}/metadata`).get()
    );
  });
});

// ── Supervisor Write: blocked Fields ────────────────────────────

describe("Supervisor writing blocked fields on users", () => {
  test("can write blocked=true on user in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/blocked`).set(true)
    );
  });

  test("can write blockedAt on user in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/blockedAt`).set(
        Date.now()
      )
    );
  });

  test("can write blockedReason on user in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/blockedReason`).set(
        "Violation of terms"
      )
    );
  });

  test("can clear blocked fields (set to false/null)", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/blocked`).set(false)
    );
  });

  test("cannot write blocked fields in non-supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${OTHER_ORG_ID}/users/some-user/blocked`).set(
        true
      )
    );
  });
});

// ── Supervisor CANNOT Write Other User Fields ───────────────────

describe("Supervisor cannot modify non-blocked user fields", () => {
  test("cannot change user role", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/role`).set("admin")
    );
  });

  test("cannot change isAdmin", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/isAdmin`).set(true)
    );
  });

  test("cannot change remainingTime", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/remainingTime`).set(
        999
      )
    );
  });

  test("cannot write packages", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/packages/new-pkg`).set({
        name: "Hacked Package",
        price: 0,
      })
    );
  });
});

// ── Supervisor Write: metadata/settings ─────────────────────────

describe("Supervisor writing metadata/settings", () => {
  test("can write to metadata/settings in supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/metadata/settings`).set({
        operatingHours: {
          enabled: true,
          startTime: "08:00",
          endTime: "22:00",
        },
      })
    );
  });

  test("cannot write to metadata/settings in non-supervised org", async () => {
    const db = testEnv.authenticatedContext(SUP_UID).database();
    await assertFails(
      db.ref(`organizations/${OTHER_ORG_ID}/metadata/settings`).set({
        operatingHours: { enabled: true },
      })
    );
  });
});

// ── Admin Access Preserved ──────────────────────────────────────

describe("Admin access still works", () => {
  test("admin can read users in their org", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users`).get()
    );
  });

  test("admin can write non-balance user data in their org", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/firstName`).set("Updated")
    );
  });

  // Balances are server-authoritative (changed only via the sionyx-server Worker,
  // which uses a service-account token that bypasses these rules). No client —
  // not even an admin — may change them directly.
  test("admin cannot change remainingTime directly (server-authoritative)", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/remainingTime`).set(120)
    );
  });

  test("admin cannot change printBalance directly (server-authoritative)", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/printBalance`).set(50)
    );
  });

  test("admin can write packages in their org", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/packages/new-pkg`).set({
        name: "New Package",
        price: 100,
      })
    );
  });

  test("admin can write metadata in their org", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/metadata/name`).set("Updated Name")
    );
  });

  test("admin cannot read supervisor data", async () => {
    const db = testEnv.authenticatedContext(ADMIN_UID).database();
    await assertFails(db.ref(`supervisors/${SUP_UID}`).get());
  });
});

// ── Regular User Access ─────────────────────────────────────────

describe("Regular user access", () => {
  test("regular user can read their own record", async () => {
    const db = testEnv.authenticatedContext(USER_UID).database();
    await assertSucceeds(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}`).get()
    );
  });

  test("regular user cannot read supervisor data", async () => {
    const db = testEnv.authenticatedContext(USER_UID).database();
    await assertFails(db.ref(`supervisors/${SUP_UID}`).get());
  });

  test("regular user cannot write blocked fields", async () => {
    const db = testEnv.authenticatedContext(USER_UID).database();
    await assertFails(
      db.ref(`organizations/${ORG_ID}/users/${USER_UID}/blocked`).set(false)
    );
  });
});

// ── Unauthenticated Access ──────────────────────────────────────

describe("Unauthenticated access", () => {
  test("cannot read organizations", async () => {
    const db = testEnv.unauthenticatedContext().database();
    await assertFails(db.ref(`organizations/${ORG_ID}/users`).get());
  });

  test("cannot read supervisor data", async () => {
    const db = testEnv.unauthenticatedContext().database();
    await assertFails(db.ref(`supervisors/${SUP_UID}`).get());
  });

  test("can read public latestRelease", async () => {
    const db = testEnv.unauthenticatedContext().database();
    await assertSucceeds(db.ref("public/latestRelease").get());
  });
});
