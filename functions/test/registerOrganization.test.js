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

let registerOrganization;

beforeAll(() => {
  const funcs = require("../index");
  registerOrganization = funcs.registerOrganization;
});

beforeEach(() => resetMocks());

describe("registerOrganization", () => {
  const validData = {
    organizationName: "Test Cafe",
    nedarimMosadId: "12345",
    nedarimApiValid: "api_key_abc",
    adminPhone: "0501234567",
    adminPassword: "securepass123",
    adminFirstName: "John",
    adminLastName: "Doe",
    adminEmail: "john@example.com",
  };

  test("registers organization and creates admin user", async () => {
    const req = {data: validData};
    const result = await registerOrganization(req);

    expect(result.success).toBe(true);
    expect(result.orgId).toBeDefined();
    expect(result.adminUid).toBeDefined();

    const metadata = getDb(`organizations/${result.orgId}/metadata`);
    expect(metadata).toBeDefined();
    expect(metadata.name).toBe("Test Cafe");
    expect(metadata.status).toBe("active");
  });

  test("rejects missing required fields", async () => {
    const req = {data: {organizationName: "Test"}};
    await expect(registerOrganization(req)).rejects.toThrow();
  });

  test("rejects duplicate organization name", async () => {
    await registerOrganization({data: validData});
    await expect(registerOrganization({data: validData}))
        .rejects.toThrow("מספר הטלפון כבר רשום במערכת");
  });

  test("rejects duplicate phone number", async () => {
    await registerOrganization({data: validData});
    const req = {
      data: {...validData, organizationName: "Another Cafe"},
    };
    await expect(registerOrganization(req)).rejects.toThrow();
  });

  test("normalizes org ID from name", async () => {
    const req = {data: {...validData, organizationName: "My Cafe 123"}};
    const result = await registerOrganization(req);
    expect(result.orgId).toBe("mycafe123");
  });

  test("rejects org name that normalizes to empty", async () => {
    const req = {data: {...validData, organizationName: "!@#$"}};
    await expect(registerOrganization(req)).rejects.toThrow();
  });

  test("stores encrypted Nedarim credentials", async () => {
    const req = {data: validData};
    const result = await registerOrganization(req);
    const metadata = getDb(`organizations/${result.orgId}/metadata`);

    expect(metadata.nedarim_mosad_id).not.toBe("12345");
    expect(metadata.nedarim_api_valid).not.toBe("api_key_abc");
  });

  test("creates admin user in org users collection", async () => {
    const req = {data: validData};
    const result = await registerOrganization(req);
    const adminUser = getDb(
        `organizations/${result.orgId}/users/${result.adminUid}`,
    );

    expect(adminUser).toBeDefined();
    expect(adminUser.isAdmin).toBe(true);
    expect(adminUser.firstName).toBe("John");
    expect(adminUser.lastName).toBe("Doe");
    expect(adminUser.phoneNumber).toBe("0501234567");
  });
});
