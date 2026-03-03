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

const {resetMocks, seedDb, mockAuth, mockAuthUsers} = require("./firebaseMock");

let resetUserPassword;

beforeAll(() => {
  const funcs = require("../index");
  resetUserPassword = funcs.resetUserPassword;
});

beforeEach(() => resetMocks());

describe("resetUserPassword", () => {
  const callerUid = "admin_uid_1";
  const targetUid = "user_uid_1";
  const orgId = "testorg";

  const makeRequest = (data, auth) => ({data, auth});

  beforeEach(() => {
    seedDb(`organizations/${orgId}/users/${callerUid}`, {
      isAdmin: true, phoneNumber: "0501111111",
    });
    seedDb(`organizations/${orgId}/users/${targetUid}`, {
      isAdmin: false, phoneNumber: "0502222222",
    });
    mockAuthUsers["0502222222@sionyx.app"] = {
      uid: targetUid, email: "0502222222@sionyx.app",
    };
  });

  test("resets password successfully", async () => {
    const req = makeRequest(
        {orgId, userId: targetUid, newPassword: "newpass123"},
        {uid: callerUid},
    );
    const result = await resetUserPassword(req);
    expect(result.success).toBe(true);
    expect(mockAuth.updateUser).toHaveBeenCalledWith(
        targetUid, {password: "newpass123"},
    );
  });

  test("rejects unauthenticated request", async () => {
    const req = makeRequest(
        {orgId, userId: targetUid, newPassword: "newpass123"},
        null,
    );
    await expect(resetUserPassword(req)).rejects.toThrow("Must be authenticated");
  });

  test("rejects missing fields", async () => {
    const req = makeRequest({orgId}, {uid: callerUid});
    await expect(resetUserPassword(req)).rejects.toThrow("Missing required");
  });

  test("rejects short password", async () => {
    const req = makeRequest(
        {orgId, userId: targetUid, newPassword: "123"},
        {uid: callerUid},
    );
    await expect(resetUserPassword(req)).rejects.toThrow();
  });

  test("rejects non-admin caller", async () => {
    seedDb(`organizations/${orgId}/users/${callerUid}`, {
      isAdmin: false, phoneNumber: "0501111111",
    });
    const req = makeRequest(
        {orgId, userId: targetUid, newPassword: "newpass123"},
        {uid: callerUid},
    );
    await expect(resetUserPassword(req)).rejects.toThrow("רק מנהלים יכולים לאפס סיסמאות");
  });

  test("rejects caller not in org", async () => {
    const req = makeRequest(
        {orgId: "other_org", userId: targetUid, newPassword: "newpass123"},
        {uid: callerUid},
    );
    await expect(resetUserPassword(req)).rejects.toThrow();
  });

  test("rejects non-existent target user", async () => {
    const req = makeRequest(
        {orgId, userId: "nonexistent", newPassword: "newpass123"},
        {uid: callerUid},
    );
    await expect(resetUserPassword(req)).rejects.toThrow();
  });
});
