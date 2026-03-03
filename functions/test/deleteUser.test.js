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

const {resetMocks, seedDb, getDb, mockAuth, mockAuthUsers} =
    require("./firebaseMock");

let deleteUser;

beforeAll(() => {
  const funcs = require("../index");
  deleteUser = funcs.deleteUser;
});

beforeEach(() => resetMocks());

describe("deleteUser", () => {
  const adminUid = "admin_1";
  const userUid = "user_1";
  const orgId = "testorg";

  beforeEach(() => {
    seedDb(`organizations/${orgId}/users/${adminUid}`, {
      isAdmin: true, phoneNumber: "0501111111",
    });
    seedDb(`organizations/${orgId}/users/${userUid}`, {
      isAdmin: false, phoneNumber: "0502222222",
      currentComputerId: null,
    });
    mockAuthUsers["0502222222@sionyx.app"] = {
      uid: userUid, email: "0502222222@sionyx.app",
    };
  });

  test("deletes user successfully", async () => {
    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: userUid},
    };
    const result = await deleteUser(req);
    expect(result.success).toBe(true);
    expect(getDb(`organizations/${orgId}/users/${userUid}`))
        .toBeUndefined();
  });

  test("rejects unauthenticated request", async () => {
    const req = {auth: null, data: {orgId, userId: userUid}};
    await expect(deleteUser(req)).rejects.toThrow("Must be authenticated");
  });

  test("rejects non-admin caller", async () => {
    seedDb(`organizations/${orgId}/users/${adminUid}`, {
      isAdmin: false, phoneNumber: "0501111111",
    });
    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: userUid},
    };
    await expect(deleteUser(req)).rejects.toThrow("רק מנהלים יכולים למחוק משתמשים");
  });

  test("prevents self-deletion", async () => {
    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: adminUid},
    };
    await expect(deleteUser(req)).rejects.toThrow("לא ניתן למחוק את עצמך");
  });

  test("prevents deleting other admins", async () => {
    const otherAdmin = "admin_2";
    seedDb(`organizations/${orgId}/users/${otherAdmin}`, {
      isAdmin: true, phoneNumber: "0503333333",
    });
    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: otherAdmin},
    };
    await expect(deleteUser(req)).rejects.toThrow("לא ניתן למחוק משתמש מנהל");
  });

  test("rejects deleting non-existent user", async () => {
    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: "nonexistent"},
    };
    await expect(deleteUser(req)).rejects.toThrow("המשתמש לא נמצא");
  });

  test("rejects missing orgId or userId", async () => {
    const req = {auth: {uid: adminUid}, data: {orgId}};
    await expect(deleteUser(req)).rejects.toThrow("Missing orgId or userId");
  });

  test("clears computer association", async () => {
    seedDb(`organizations/${orgId}/users/${userUid}`, {
      isAdmin: false, phoneNumber: "0502222222",
      currentComputerId: "comp_1",
    });
    seedDb(`organizations/${orgId}/computers/comp_1`, {
      currentUserId: userUid, isActive: true,
    });

    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: userUid},
    };
    await deleteUser(req);

    const comp = getDb(`organizations/${orgId}/computers/comp_1`);
    expect(comp.currentUserId).toBeNull();
    expect(comp.isActive).toBe(false);
  });

  test("handles auth/user-not-found gracefully", async () => {
    delete mockAuthUsers["0502222222@sionyx.app"];
    mockAuth.deleteUser.mockRejectedValueOnce(
        Object.assign(new Error("not found"), {code: "auth/user-not-found"}),
    );

    const req = {
      auth: {uid: adminUid},
      data: {orgId, userId: userUid},
    };
    const result = await deleteUser(req);
    expect(result.success).toBe(true);
  });
});
