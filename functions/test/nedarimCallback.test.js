jest.mock("firebase-admin", () => {
  const mock = require("./firebaseMock");
  const db = () => mock.mockDatabase;
  db.ServerValue = mock.mockDatabase.ServerValue;
  return {
    initializeApp: jest.fn(),
    database: db,
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

const makeReq = (body = {}, overrides = {}) => ({
  method: "POST",
  body,
  query: {},
  headers: {"content-type": "application/json"},
  ip: "127.0.0.1",
  ...overrides,
});

const makeRes = () => {
  const res = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

let nedarimCallback;

beforeAll(() => {
  delete process.env.CALLBACK_SECRET;
  delete process.env.NODE_ENV;
  const funcs = require("../index");
  nedarimCallback = funcs.nedarimCallback;
});

beforeEach(() => resetMocks());

afterEach(() => {
  delete process.env.CALLBACK_SECRET;
});

describe("nedarimCallback", () => {
  const validBody = {
    Amount: "100",
    TransactionId: "txn_123",
    Status: "OK",
    Param1: "purchase_1",
    Param2: "org_1",
    CreditCardNumber: "4111111111111111",
    Message: "Success",
  };

  // ── HTTP Method ────────────────────────────────────

  test("rejects non-POST requests with 405", async () => {
    const req = makeReq(validBody, {method: "GET"});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(405);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({error: "Method Not Allowed"}),
    );
  });

  // ── Validation ─────────────────────────────────────

  test("rejects invalid Amount", async () => {
    const req = makeReq({...validBody, Amount: "abc"});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({error: "Invalid Amount"}),
    );
  });

  test("rejects negative Amount", async () => {
    const req = makeReq({...validBody, Amount: "-50"});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
  });

  test("rejects missing Param1 (purchaseId)", async () => {
    const req = makeReq({...validBody, Param1: ""});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({error: "Invalid Param1 (purchaseId)"}),
    );
  });

  test("rejects missing Param2 (orgId)", async () => {
    const req = makeReq({...validBody, Param2: ""});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
  });

  test("rejects missing TransactionId", async () => {
    const {TransactionId, ...noTxn} = validBody;
    const req = makeReq(noTxn);
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({error: "Missing required fields"}),
    );
  });

  test("rejects missing Status", async () => {
    const {Status, ...noStatus} = validBody;
    const req = makeReq(noStatus);
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
  });

  // ── Secret Validation ──────────────────────────────

  test("rejects request with wrong secret", async () => {
    process.env.CALLBACK_SECRET = "my-secret";
    try {
      jest.resetModules();
      const {resetMocks: rm} = require("./firebaseMock");
      rm();
      const funcs = require("../index");

      const req = makeReq(validBody, {query: {secret: "wrong"}});
      const res = makeRes();
      await funcs.nedarimCallback(req, res);
      expect(res.status).toHaveBeenCalledWith(403);
    } finally {
      delete process.env.CALLBACK_SECRET;
    }
  });

  test("accepts request with correct secret via query", async () => {
    process.env.CALLBACK_SECRET = "my-secret";
    try {
      jest.resetModules();
      const mock = require("./firebaseMock");
      mock.resetMocks();
      mock.seedDb("organizations/org_1/purchases/purchase_1", {
        userId: "user_1", minutes: 60, printBudget: 0, validityDays: 0,
      });
      mock.seedDb("organizations/org_1/users/user_1", {
        remainingTime: 0, printBalance: 0,
      });
      const funcs = require("../index");

      const req = makeReq(validBody, {query: {secret: "my-secret"}});
      const res = makeRes();
      await funcs.nedarimCallback(req, res);
      expect(res.status).toHaveBeenCalledWith(200);
    } finally {
      delete process.env.CALLBACK_SECRET;
    }
  });

  // ── Successful Payment ─────────────────────────────

  test("credits user time on successful payment", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1",
      minutes: 60,
      printBudget: 10,
      validityDays: 0,
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 300,
      printBalance: 5,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({success: true}),
    );

    const user = getDb("organizations/org_1/users/user_1");
    expect(user.remainingTime).toBe(300 + 60 * 60);
    expect(user.printBalance).toBe(15);
  });

  test("sets timeExpiresAt when validityDays > 0", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1",
      minutes: 120,
      printBudget: 0,
      validityDays: 30,
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 0, printBalance: 0,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    const user = getDb("organizations/org_1/users/user_1");
    expect(user.timeExpiresAt).toBeDefined();
    const expiry = new Date(user.timeExpiresAt);
    expect(expiry.getTime()).toBeGreaterThan(Date.now());
  });

  // ── Failed Payment ─────────────────────────────────

  test("marks purchase failed and does not credit on Error status", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1", minutes: 60, printBudget: 0, validityDays: 0,
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 100, printBalance: 0,
    });

    const req = makeReq({...validBody, Status: "Error"});
    const res = makeRes();
    await nedarimCallback(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    const purchase = getDb("organizations/org_1/purchases/purchase_1");
    expect(purchase.status).toBe("failed");

    const user = getDb("organizations/org_1/users/user_1");
    expect(user.remainingTime).toBe(100);
  });

  // ── Idempotency ────────────────────────────────────

  test("does not double-credit on duplicate callback", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1",
      minutes: 60,
      printBudget: 0,
      validityDays: 0,
      status: "completed",
      creditedAt: "2026-01-01T00:00:00.000Z",
      transactionId: "txn_123",
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 3600, printBalance: 0,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Callback already processed (idempotent)",
        }),
    );

    const user = getDb("organizations/org_1/users/user_1");
    expect(user.remainingTime).toBe(3600);
  });

  // ── Edge cases ─────────────────────────────────────

  test("handles missing user gracefully", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_nonexistent",
      minutes: 60, printBudget: 0, validityDays: 0,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(200);
  });

  test("handles purchase with no userId", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      minutes: 60, printBudget: 0, validityDays: 0,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(200);
  });

  test("accepts Amount of zero", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1", minutes: 0, printBudget: 0, validityDays: 0,
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 0, printBalance: 0,
    });

    const req = makeReq({...validBody, Amount: "0"});
    const res = makeRes();
    await nedarimCallback(req, res);
    expect(res.status).toHaveBeenCalledWith(200);
  });

  test("marks creditedAt on purchase after crediting", async () => {
    seedDb("organizations/org_1/purchases/purchase_1", {
      userId: "user_1", minutes: 30, printBudget: 5, validityDays: 0,
    });
    seedDb("organizations/org_1/users/user_1", {
      remainingTime: 0, printBalance: 0,
    });

    const req = makeReq(validBody);
    const res = makeRes();
    await nedarimCallback(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    const purchase = getDb("organizations/org_1/purchases/purchase_1");
    expect(purchase.creditedAt).toBeDefined();
    expect(purchase.creditedUserId).toBe("user_1");
  });
});
