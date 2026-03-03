/**
 * In-memory Firebase mock data layer.
 * Each test file must register jest.mock calls itself (for hoisting).
 * This module provides the mock implementations and data helpers.
 */

const mockDbData = {};
const mockAuthUsers = {};

const makeSnapshot = (path) => {
  const val = mockDbData[path];
  return {
    exists: () => val !== undefined && val !== null,
    val: () => val ?? null,
    child: (childPath) => makeSnapshot(`${path}/${childPath}`),
  };
};

const makeRef = (path) => ({
  once: jest.fn(async () => makeSnapshot(path)),
  set: jest.fn(async (data) => {
    mockDbData[path] = data;
  }),
  update: jest.fn(async (data) => {
    if (path === "" || path === "/") {
      // Multi-path update on root ref: keys are full paths
      for (const [fullPath, value] of Object.entries(data)) {
        const parts = fullPath.split("/");
        const leafKey = parts.pop();
        const parentPath = parts.join("/");
        if (!mockDbData[parentPath]) mockDbData[parentPath] = {};
        if (value === null) {
          delete mockDbData[parentPath][leafKey];
        } else {
          mockDbData[parentPath][leafKey] = value;
        }
      }
    } else {
      mockDbData[path] = {...(mockDbData[path] || {}), ...data};
    }
  }),
  remove: jest.fn(async () => {
    delete mockDbData[path];
  }),
});

const mockDatabase = {
  ref: jest.fn((path) => makeRef(path || "")),
  ServerValue: {TIMESTAMP: {".sv": "timestamp"}},
};

const mockAuth = {
  createUser: jest.fn(async ({email, password, displayName}) => {
    const uid = `uid_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    if (mockAuthUsers[email]) {
      const err = new Error("Email already exists");
      err.code = "auth/email-already-exists";
      throw err;
    }
    mockAuthUsers[email] = {uid, email, password, displayName};
    return {uid};
  }),
  updateUser: jest.fn(async (uid, props) => {
    const user = Object.values(mockAuthUsers).find((u) => u.uid === uid);
    if (!user) {
      const err = new Error("User not found");
      err.code = "auth/user-not-found";
      throw err;
    }
    Object.assign(user, props);
    return user;
  }),
  deleteUser: jest.fn(async (uid) => {
    const entry = Object.entries(mockAuthUsers)
        .find(([, u]) => u.uid === uid);
    if (!entry) {
      const err = new Error("User not found");
      err.code = "auth/user-not-found";
      throw err;
    }
    delete mockAuthUsers[entry[0]];
  }),
};

const resetMocks = () => {
  Object.keys(mockDbData).forEach((k) => delete mockDbData[k]);
  Object.keys(mockAuthUsers).forEach((k) => delete mockAuthUsers[k]);
  mockDatabase.ref.mockClear();
  mockAuth.createUser.mockClear();
  mockAuth.updateUser.mockClear();
  mockAuth.deleteUser.mockClear();
};

const seedDb = (path, data) => {
  mockDbData[path] = data;
};

const getDb = (path) => mockDbData[path];

module.exports = {
  mockDatabase,
  mockAuth,
  mockDbData,
  mockAuthUsers,
  resetMocks,
  seedDb,
  getDb,
};
