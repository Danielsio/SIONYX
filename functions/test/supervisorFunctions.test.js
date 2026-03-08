jest.mock("firebase-admin", () => {
  const mock = require("./firebaseMock");
  return {
    initializeApp: jest.fn(),
    database: () => mock.mockDatabase,
    auth: () => mock.mockAuth,
  };
});
jest.mock("firebase-functions", () => {
  class MockHttpsError extends Error {
    constructor(code, message) { super(message); this.code = code; }
  }
  return { setGlobalOptions: jest.fn(), https: { HttpsError: MockHttpsError } };
});
jest.mock("firebase-functions/https", () => ({
  onRequest: (fn) => fn, onCall: (fn) => fn,
}));
jest.mock("firebase-functions/logger", () => ({
  info: jest.fn(), warn: jest.fn(), error: jest.fn(),
}));
jest.mock("firebase-functions/v2/https", () => ({
  onRequest: (fn) => fn,
  onCall: (optsOrFn, maybeFn) => typeof optsOrFn === "function" ? optsOrFn : maybeFn,
}));
jest.mock("firebase-functions/v2/scheduler", () => ({
  onSchedule: (_opts, fn) => fn,
}));

const {resetMocks, seedDb, getDb} = require("./firebaseMock");

let blockUser, unblockUser, getSupervisorOrgs, setSupervisorOrgSettings;

beforeAll(() => {
  const funcs = require("../index");
  blockUser = funcs.blockUser;
  unblockUser = funcs.unblockUser;
  getSupervisorOrgs = funcs.getSupervisorOrgs;
  setSupervisorOrgSettings = funcs.setSupervisorOrgSettings;
});

beforeEach(() => resetMocks());

const supervisorUid = "supervisor-1";

const seedSupervisor = (orgs = ["org-a", "org-b"], blockedUsers = {}) => {
  const orgMap = {};
  orgs.forEach((id) => { orgMap[id] = true; });
  seedDb(`supervisors/${supervisorUid}`, {
    name: "Test Supervisor",
    email: "super@test.com",
    phone: "0501111111",
    createdAt: new Date().toISOString(),
    organizations: orgMap,
    blockedUsers,
  });
  seedDb(`supervisors/${supervisorUid}/organizations`, orgMap);
  seedDb(`supervisors/${supervisorUid}/blockedUsers`, blockedUsers);
};

const seedOrg = (orgId, users = {}, purchases = {}) => {
  seedDb(`organizations/${orgId}`, {
    metadata: {
      name: orgId,
      status: "active",
      created_at: new Date().toISOString(),
    },
    users,
    purchases,
  });
  seedDb(`organizations/${orgId}/metadata`, {
    name: orgId,
    status: "active",
    created_at: new Date().toISOString(),
  });
  seedDb(`organizations/${orgId}/users`, users);
  seedDb(`organizations/${orgId}/purchases`, purchases);
};

const mkAuth = (uid) => ({auth: {uid}});

// ─── blockUser ───

describe("blockUser", () => {
  it("rejects unauthenticated callers", async () => {
    await expect(blockUser({data: {phone: "0509999999"}, auth: null}))
        .rejects.toThrow("Must be authenticated");
  });

  it("rejects non-supervisor callers", async () => {
    await expect(blockUser({...mkAuth("random-user"), data: {phone: "0509999999"}}))
        .rejects.toThrow("Not a supervisor");
  });

  it("rejects missing phone", async () => {
    seedSupervisor();
    await expect(blockUser({...mkAuth(supervisorUid), data: {}}))
        .rejects.toThrow("Phone number is required");
  });

  it("blocks user across all supervised orgs", async () => {
    seedSupervisor(["org-a", "org-b"]);
    seedOrg("org-a", {
      "user-1": {phoneNumber: "050-999-9999", firstName: "John"},
    });
    seedOrg("org-b", {
      "user-2": {phoneNumber: "0509999999", firstName: "John"},
      "user-3": {phoneNumber: "0501111111", firstName: "Other"},
    });

    const result = await blockUser({
      ...mkAuth(supervisorUid),
      data: {phone: "050-999-9999", reason: "Bad behavior", userName: "John"},
    });

    expect(result.success).toBe(true);
    expect(result.blockedCount).toBe(2);

    // Verify blocked list entry
    const blockedEntry = getDb(`supervisors/${supervisorUid}/blockedUsers/0509999999`);
    expect(blockedEntry.name).toBe("John");
    expect(blockedEntry.reason).toBe("Bad behavior");

    // Verify user records are blocked
    const user1 = getDb(`organizations/org-a/users/user-1`);
    expect(user1.blocked).toBe(true);
    expect(user1.blockedReason).toBe("Bad behavior");

    const user2 = getDb(`organizations/org-b/users/user-2`);
    expect(user2.blocked).toBe(true);

    // Non-matching user should not have been updated (no individual path entry)
    const user3 = getDb(`organizations/org-b/users/user-3`);
    expect(user3 === undefined || user3.blocked === undefined).toBe(true);
  });

  it("handles user not found in any org gracefully", async () => {
    seedSupervisor(["org-a"]);
    seedOrg("org-a", {
      "user-1": {phoneNumber: "0501111111", firstName: "Other"},
    });

    const result = await blockUser({
      ...mkAuth(supervisorUid),
      data: {phone: "0509999999"},
    });

    expect(result.success).toBe(true);
    expect(result.blockedCount).toBe(0);
  });
});

// ─── unblockUser ───

describe("unblockUser", () => {
  it("rejects unauthenticated callers", async () => {
    await expect(unblockUser({data: {phone: "0509999999"}, auth: null}))
        .rejects.toThrow("Must be authenticated");
  });

  it("rejects non-supervisor callers", async () => {
    await expect(unblockUser({...mkAuth("random"), data: {phone: "0509999999"}}))
        .rejects.toThrow("Not a supervisor");
  });

  it("unblocks user across all supervised orgs", async () => {
    const blockedUsers = {"0509999999": {name: "John", reason: "test", blockedAt: Date.now()}};
    seedSupervisor(["org-a"], blockedUsers);
    seedOrg("org-a", {
      "user-1": {phoneNumber: "0509999999", blocked: true, blockedReason: "test"},
    });
    // Seed all supervisors for multi-supervisor check
    seedDb("supervisors", {
      [supervisorUid]: getDb(`supervisors/${supervisorUid}`),
    });

    const result = await unblockUser({
      ...mkAuth(supervisorUid),
      data: {phone: "0509999999"},
    });

    expect(result.success).toBe(true);
    expect(result.unblockedCount).toBe(1);

    const user1 = getDb(`organizations/org-a/users/user-1`);
    expect(user1.blocked).toBe(false);
  });

  it("does not unblock if another supervisor still blocks the user", async () => {
    const blockedUsers = {"0509999999": {name: "John", reason: "test", blockedAt: Date.now()}};
    seedSupervisor(["org-a"], blockedUsers);
    seedOrg("org-a", {
      "user-1": {phoneNumber: "0509999999", blocked: true},
    });
    // Another supervisor also blocks this phone for org-a
    seedDb("supervisors", {
      [supervisorUid]: getDb(`supervisors/${supervisorUid}`),
      "supervisor-2": {
        organizations: {"org-a": true},
        blockedUsers: {"0509999999": {name: "John", reason: "other"}},
      },
    });

    const result = await unblockUser({
      ...mkAuth(supervisorUid),
      data: {phone: "0509999999"},
    });

    expect(result.success).toBe(true);
    expect(result.unblockedCount).toBe(0);
  });
});

// ─── getSupervisorOrgs ───

describe("getSupervisorOrgs", () => {
  it("rejects unauthenticated callers", async () => {
    await expect(getSupervisorOrgs({data: {}, auth: null}))
        .rejects.toThrow("Must be authenticated");
  });

  it("returns org metadata and stats", async () => {
    seedSupervisor(["org-a"]);
    seedOrg("org-a", {
      "user-1": {isSessionActive: true},
      "user-2": {isSessionActive: false},
    }, {
      "p-1": {status: "completed", amount: 50},
      "p-2": {status: "completed", amount: 30},
      "p-3": {status: "failed", amount: 10},
    });

    const result = await getSupervisorOrgs({
      ...mkAuth(supervisorUid),
      data: {},
    });

    expect(result.success).toBe(true);
    expect(result.organizations).toHaveLength(1);

    const org = result.organizations[0];
    expect(org.orgId).toBe("org-a");
    expect(org.userCount).toBe(2);
    expect(org.activeUsers).toBe(1);
    expect(org.totalRevenue).toBe(80);
    expect(org.status).toBe("active");
  });

  it("returns blocked users count", async () => {
    seedSupervisor(["org-a"]);
    seedDb(`supervisors/${supervisorUid}/blockedUsers`, {
      "0501111111": {name: "A"},
      "0502222222": {name: "B"},
    });
    seedOrg("org-a", {});

    const result = await getSupervisorOrgs({
      ...mkAuth(supervisorUid),
      data: {},
    });

    expect(result.blockedUsersCount).toBe(2);
  });

  it("returns empty for supervisor with no orgs", async () => {
    seedSupervisor([]);

    const result = await getSupervisorOrgs({
      ...mkAuth(supervisorUid),
      data: {},
    });

    expect(result.organizations).toHaveLength(0);
  });
});

// ─── setSupervisorOrgSettings ───

describe("setSupervisorOrgSettings", () => {
  it("rejects unauthenticated callers", async () => {
    await expect(setSupervisorOrgSettings({
      data: {orgId: "org-a", settings: {}}, auth: null,
    })).rejects.toThrow("Must be authenticated");
  });

  it("rejects non-supervisor callers", async () => {
    await expect(setSupervisorOrgSettings({
      ...mkAuth("random"), data: {orgId: "org-a", settings: {}},
    })).rejects.toThrow("Not a supervisor");
  });

  it("rejects org not under supervision", async () => {
    seedSupervisor(["org-a"]);

    await expect(setSupervisorOrgSettings({
      ...mkAuth(supervisorUid),
      data: {orgId: "org-other", settings: {operatingHours: {enabled: true}}},
    })).rejects.toThrow("not under your supervision");
  });

  it("updates operating hours for supervised org", async () => {
    seedSupervisor(["org-a"]);
    seedOrg("org-a", {});
    seedDb("organizations/org-a/metadata/settings", {});

    const operatingHours = {
      enabled: true,
      startTime: "08:00",
      endTime: "22:00",
    };

    const result = await setSupervisorOrgSettings({
      ...mkAuth(supervisorUid),
      data: {orgId: "org-a", settings: {operatingHours}},
    });

    expect(result.success).toBe(true);

    const settings = getDb("organizations/org-a/metadata/settings");
    expect(settings.operatingHours).toEqual(operatingHours);
  });

  it("filters out non-allowed settings keys", async () => {
    seedSupervisor(["org-a"]);
    seedOrg("org-a", {});
    seedDb("organizations/org-a/metadata/settings", {});

    await expect(setSupervisorOrgSettings({
      ...mkAuth(supervisorUid),
      data: {orgId: "org-a", settings: {malicious: "data"}},
    })).rejects.toThrow("No valid settings provided");
  });
});
