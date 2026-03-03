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

const {resetMocks, seedDb, getDb, mockAuthUsers} = require("./firebaseMock");

let cleanupTestOrganization;

beforeAll(() => {
  const funcs = require("../index");
  cleanupTestOrganization = funcs.cleanupTestOrganization;
});

beforeEach(() => resetMocks());

describe("cleanupTestOrganization", () => {
  test("rejects missing orgId", async () => {
    const req = {auth: {uid: "admin"}, data: {}};
    await expect(cleanupTestOrganization(req))
        .rejects.toThrow("orgId is required");
  });

  test("rejects non-test/ci org IDs", async () => {
    const req = {auth: {uid: "admin"}, data: {orgId: "production_cafe"}};
    await expect(cleanupTestOrganization(req))
        .rejects.toThrow("Only test/CI orgs");
  });

  test("allows 'test' prefix orgs", async () => {
    seedDb("organizations/testcafe", {
      metadata: {name: "Test Cafe", admin_uid: "admin_1"},
      users: {admin_1: {isAdmin: true}},
    });
    mockAuthUsers["admin@test.com"] = {uid: "admin_1", email: "admin@test.com"};

    const req = {auth: {uid: "admin"}, data: {orgId: "testcafe"}};
    const result = await cleanupTestOrganization(req);
    expect(result.success).toBe(true);
    expect(getDb("organizations/testcafe")).toBeUndefined();
  });

  test("allows 'ci' prefix orgs", async () => {
    seedDb("organizations/citest123", {
      metadata: {name: "CI Test", admin_uid: "admin_2"},
    });
    mockAuthUsers["admin2@test.com"] = {
      uid: "admin_2", email: "admin2@test.com",
    };

    const req = {auth: {uid: "admin"}, data: {orgId: "citest123"}};
    const result = await cleanupTestOrganization(req);
    expect(result.success).toBe(true);
  });

  test("returns success when org does not exist", async () => {
    const req = {auth: {uid: "admin"}, data: {orgId: "testnonexistent"}};
    const result = await cleanupTestOrganization(req);
    expect(result.success).toBe(true);
    expect(result.message).toContain("Nothing to clean");
  });

  test("deletes all user auth accounts", async () => {
    seedDb("organizations/testcafe2", {
      metadata: {name: "Test Cafe 2", admin_uid: "admin_1"},
      users: {
        admin_1: {isAdmin: true},
        user_1: {isAdmin: false},
        user_2: {isAdmin: false},
      },
    });
    mockAuthUsers["a@t.com"] = {uid: "admin_1", email: "a@t.com"};
    mockAuthUsers["u1@t.com"] = {uid: "user_1", email: "u1@t.com"};
    mockAuthUsers["u2@t.com"] = {uid: "user_2", email: "u2@t.com"};

    const req = {auth: {uid: "admin"}, data: {orgId: "testcafe2"}};
    await cleanupTestOrganization(req);

    expect(mockAuthUsers).not.toHaveProperty("a@t.com");
    expect(mockAuthUsers).not.toHaveProperty("u1@t.com");
    expect(mockAuthUsers).not.toHaveProperty("u2@t.com");
  });
});
