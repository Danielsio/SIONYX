#!/usr/bin/env node
/**
 * Reset all users' time to a clean slate.
 *
 * Usage:
 *   node scripts/reset-users-time.js                          # dry-run (preview)
 *   node scripts/reset-users-time.js --confirm                # reset time + prints
 *   node scripts/reset-users-time.js --confirm --keep-prints  # reset time, keep prints
 *
 * Requires: serviceAccountKey.json at repo root, ORG_ID in .env
 */

const path = require("path");
const fs = require("fs");

const saPath = path.resolve(__dirname, "..", "serviceAccountKey.json");
if (!fs.existsSync(saPath)) {
  console.error("ERROR: serviceAccountKey.json not found at", saPath);
  process.exit(1);
}

// Use firebase-admin from the functions/ directory
const admin = require(path.resolve(__dirname, "..", "functions", "node_modules", "firebase-admin"));

function loadEnv() {
  const envPath = path.resolve(__dirname, "..", ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf-8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    const val = trimmed.slice(eq + 1).trim();
    if (!process.env[key]) process.env[key] = val;
  }
}

async function main() {
  loadEnv();

  const orgId = process.env.ORG_ID;
  const dbUrl = process.env.FIREBASE_DATABASE_URL;

  if (!orgId) { console.error("ERROR: ORG_ID not set"); process.exit(1); }

  const args = process.argv.slice(2);
  const dryRun = !args.includes("--confirm");
  const keepPrints = args.includes("--keep-prints");

  admin.initializeApp({
    credential: admin.credential.cert(require(saPath)),
    databaseURL: dbUrl,
  });

  const db = admin.database();
  const usersRef = db.ref(`organizations/${orgId}/users`);

  console.log("╔══════════════════════════════════════════════╗");
  console.log("║       SIONYX — Reset All Users Time          ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log();
  console.log(`  Organization:  ${orgId}`);
  console.log(`  Mode:          ${dryRun ? "DRY RUN (preview only)" : "⚠  LIVE — changes will be applied"}`);
  console.log(`  Keep prints:   ${keepPrints ? "yes" : "no (reset to 0)"}`);
  console.log();

  console.log("Fetching users...");
  const snapshot = await usersRef.once("value");
  const users = snapshot.val();

  if (!users || typeof users !== "object") {
    console.log("No users found.");
    process.exit(0);
  }

  const userIds = Object.keys(users);
  console.log(`Found ${userIds.length} user(s)\n`);

  // Summary table
  const sep = "─";
  console.log(`┌${sep.repeat(37)}┬${sep.repeat(13)}┬${sep.repeat(12)}┬${sep.repeat(26)}┐`);
  console.log(`│ ${"User".padEnd(35)} │ ${"Time (min)".padStart(11)} │ ${"Prints (₪)".padStart(10)} │ ${"Expires".padEnd(24)} │`);
  console.log(`├${sep.repeat(37)}┼${sep.repeat(13)}┼${sep.repeat(12)}┼${sep.repeat(26)}┤`);

  for (const uid of userIds) {
    const u = users[uid];
    const name = [u.firstName, u.lastName].filter(Boolean).join(" ") || uid.slice(0, 16);
    const timeSec = u.remainingTime || 0;
    const timeMin = (timeSec / 60).toFixed(1);
    const prints = u.printBalance || 0;
    const expires = u.timeExpiresAt
      ? new Date(u.timeExpiresAt).toLocaleString("he-IL", { timeZone: "Asia/Jerusalem" })
      : "—";

    console.log(
      `│ ${name.slice(0, 35).padEnd(35)} │ ${timeMin.padStart(11)} │ ${String(prints).padStart(10)} │ ${expires.slice(0, 24).padEnd(24)} │`
    );
  }

  console.log(`└${sep.repeat(37)}┴${sep.repeat(13)}┴${sep.repeat(12)}┴${sep.repeat(26)}┘`);
  console.log();

  if (dryRun) {
    console.log("🔍 DRY RUN — no changes made.");
    console.log("   Run with --confirm to apply the reset.");
    admin.app().delete();
    return;
  }

  // Apply
  console.log("Resetting...\n");
  let ok = 0;
  let fail = 0;

  for (const uid of userIds) {
    const u = users[uid];
    const name = [u.firstName, u.lastName].filter(Boolean).join(" ") || uid.slice(0, 16);

    const update = {
      remainingTime: 0,
      timeExpiresAt: null,
      isSessionActive: false,
      sessionStartTime: null,
      currentComputerId: null,
      updatedAt: new Date().toISOString(),
    };
    if (!keepPrints) update.printBalance = 0;

    try {
      await db.ref(`organizations/${orgId}/users/${uid}`).update(update);
      console.log(`  ✓ ${name}`);
      ok++;
    } catch (err) {
      console.log(`  ✗ ${name}: ${err.message}`);
      fail++;
    }
  }

  console.log();
  console.log(`Done: ${ok} reset, ${fail} errors.`);
  admin.app().delete();
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
