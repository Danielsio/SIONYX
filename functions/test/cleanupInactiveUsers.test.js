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

const {resetMocks, seedDb} = require("./firebaseMock");

let cleanupInactiveUsers;

beforeAll(() => {
  const funcs = require("../index");
  cleanupInactiveUsers = funcs.cleanupInactiveUsers;
});

beforeEach(() => resetMocks());

const daysAgo = (days) =>
  new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

describe("cleanupInactiveUsers (scheduled)", () => {
  test("runs without error on empty DB", async () => {
    await cleanupInactiveUsers();
  });

  test("runs without error with no users", async () => {
    seedDb("organizations", {
      testorg: {
        metadata: {name: "Test"},
      },
    });
    await cleanupInactiveUsers();
  });

  test("runs without error with only admin users", async () => {
    seedDb("organizations", {
      testorg: {
        users: {
          admin_user: {
            isAdmin: true,
            createdAt: daysAgo(30),
          },
        },
        purchases: {},
      },
    });
    await cleanupInactiveUsers();
  });

  test("runs without error with paying users", async () => {
    seedDb("organizations", {
      testorg: {
        users: {
          paying_user: {
            isAdmin: false,
            createdAt: daysAgo(20),
          },
        },
        purchases: {
          purchase_1: {userId: "paying_user", amount: 50},
        },
      },
    });
    await cleanupInactiveUsers();
  });

  test("runs without error with recent users", async () => {
    seedDb("organizations", {
      testorg: {
        users: {
          new_user: {
            isAdmin: false,
            createdAt: daysAgo(3),
          },
        },
        purchases: {},
      },
    });
    await cleanupInactiveUsers();
  });

  test("processes multiple organizations", async () => {
    seedDb("organizations", {
      org1: {
        users: {u1: {isAdmin: false, createdAt: daysAgo(10)}},
        purchases: {},
      },
      org2: {
        users: {u2: {isAdmin: false, createdAt: daysAgo(10)}},
        purchases: {},
      },
    });
    await cleanupInactiveUsers();
  });
});
