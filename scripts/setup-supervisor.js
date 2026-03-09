#!/usr/bin/env node
/**
 * Create or replace the single supervisor user.
 *
 * Usage:
 *   node scripts/setup-supervisor.js                 # dry-run
 *   node scripts/setup-supervisor.js --confirm       # write to DB + Auth
 *
 * Requires:
 *   serviceAccountKey.json at repo root
 *   .env with FIREBASE_DATABASE_URL and:
 *     SUPERVISOR_PHONE      – phone number (e.g. "0501234567")
 *     SUPERVISOR_PASSWORD   – login password (min 6 chars)
 *     SUPERVISOR_NAME       – display name
 *     SUPERVISOR_ORG_IDS    – comma-separated org IDs (e.g. "org1,org2")
 */

const path = require("path");
const fs = require("fs");

const saPath = path.resolve(__dirname, "..", "serviceAccountKey.json");
if (!fs.existsSync(saPath)) {
  console.error("ERROR: serviceAccountKey.json not found at", saPath);
  process.exit(1);
}

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

function phoneToEmail(phone) {
  return `${phone.replace(/\D/g, "")}@sionyx.app`;
}

async function main() {
  loadEnv();

  const dbUrl = process.env.FIREBASE_DATABASE_URL;
  const phone = process.env.SUPERVISOR_PHONE;
  const password = process.env.SUPERVISOR_PASSWORD;
  const name = process.env.SUPERVISOR_NAME;
  const orgIdsCsv = process.env.SUPERVISOR_ORG_IDS;

  if (!dbUrl) { console.error("ERROR: FIREBASE_DATABASE_URL not set in .env"); process.exit(1); }
  if (!phone) { console.error("ERROR: SUPERVISOR_PHONE not set in .env"); process.exit(1); }
  if (!password) { console.error("ERROR: SUPERVISOR_PASSWORD not set in .env"); process.exit(1); }
  if (!name) { console.error("ERROR: SUPERVISOR_NAME not set in .env"); process.exit(1); }
  if (!orgIdsCsv) { console.error("ERROR: SUPERVISOR_ORG_IDS not set in .env"); process.exit(1); }

  const cleanPhone = phone.replace(/\D/g, "");
  const orgIds = orgIdsCsv.split(",").map(s => s.trim()).filter(Boolean);
  const email = phoneToEmail(cleanPhone);

  if (password.length < 6) {
    console.error("ERROR: SUPERVISOR_PASSWORD must be at least 6 characters");
    process.exit(1);
  }

  if (orgIds.length === 0) {
    console.error("ERROR: SUPERVISOR_ORG_IDS must contain at least one org ID");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const dryRun = !args.includes("--confirm");

  admin.initializeApp({
    credential: admin.credential.cert(require(saPath)),
    databaseURL: dbUrl,
  });

  const db = admin.database();

  console.log("╔══════════════════════════════════════════════╗");
  console.log("║    SIONYX — Setup Supervisor                 ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log();
  console.log(`  Phone:          ${cleanPhone}`);
  console.log(`  Email:          ${email}`);
  console.log(`  Name:           ${name}`);
  console.log(`  Organizations:  ${orgIds.join(", ")}`);
  console.log(`  Mode:           ${dryRun ? "DRY RUN" : "⚠  LIVE"}`);
  console.log();

  // Check if any existing supervisor exists
  const supervisorsRef = db.ref("supervisors");
  const existingSnap = await supervisorsRef.once("value");
  const existingSupervisors = existingSnap.exists() ? existingSnap.val() : {};
  const existingUids = Object.keys(existingSupervisors);

  if (existingUids.length > 0) {
    console.log(`  ⚠  Found ${existingUids.length} existing supervisor(s) — will be replaced:`);
    for (const uid of existingUids) {
      const sup = existingSupervisors[uid];
      console.log(`     - ${sup.name || "unnamed"} (${sup.phone || uid})`);
    }
    console.log();
  }

  // Verify all org IDs exist
  for (const orgId of orgIds) {
    const orgSnap = await db.ref(`organizations/${orgId}/metadata`).once("value");
    if (!orgSnap.exists()) {
      console.error(`ERROR: Organization "${orgId}" not found in database`);
      admin.app().delete();
      process.exit(1);
    }
    const orgName = orgSnap.val().name || orgId;
    console.log(`  ✓ Org verified: ${orgId} (${orgName})`);
  }
  console.log();

  if (dryRun) {
    console.log("🔍 DRY RUN — no changes made.");
    console.log("   Run with --confirm to create the supervisor.");
    admin.app().delete();
    return;
  }

  // Step 1: Create or get Firebase Auth user
  let uid;
  try {
    const userRecord = await admin.auth().getUserByEmail(email);
    uid = userRecord.uid;
    console.log(`  Auth user already exists: ${uid}`);
    await admin.auth().updateUser(uid, {
      password,
      displayName: name,
    });
    console.log(`  Auth password and display name updated.`);
  } catch (err) {
    if (err.code === "auth/user-not-found") {
      const userRecord = await admin.auth().createUser({
        email,
        password,
        displayName: name,
      });
      uid = userRecord.uid;
      console.log(`  Auth user created: ${uid}`);
    } else {
      throw err;
    }
  }

  // Step 2: Remove all existing supervisors (single supervisor model)
  if (existingUids.length > 0) {
    for (const oldUid of existingUids) {
      await db.ref(`supervisors/${oldUid}`).remove();
      console.log(`  Removed old supervisor: ${oldUid}`);
    }
  }

  // Step 3: Write new supervisor record
  const organizations = {};
  for (const orgId of orgIds) {
    organizations[orgId] = true;
  }

  const supervisorData = {
    name,
    phone: cleanPhone,
    email,
    createdAt: new Date().toISOString(),
    organizations,
  };

  await db.ref(`supervisors/${uid}`).set(supervisorData);
  console.log(`  Supervisor record written at supervisors/${uid}`);

  console.log();
  console.log("  ✅ Supervisor setup complete!");
  console.log(`     UID:   ${uid}`);
  console.log(`     Login: ${cleanPhone} / [password]`);
  console.log(`     Orgs:  ${orgIds.join(", ")}`);

  admin.app().delete();
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
