#!/usr/bin/env node
/**
 * Seed purchase records based on existing packages and users.
 *
 * Usage:
 *   node scripts/seed-purchases.js                 # dry-run (preview)
 *   node scripts/seed-purchases.js --confirm       # write purchases to DB
 *   node scripts/seed-purchases.js --confirm --count 20  # write 20 purchases
 *
 * Requires: serviceAccountKey.json at repo root, ORG_ID + FIREBASE_DATABASE_URL in .env
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

function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomDate(daysBack) {
  const now = Date.now();
  const past = now - daysBack * 24 * 60 * 60 * 1000;
  return new Date(past + Math.random() * (now - past));
}

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

async function main() {
  loadEnv();

  const orgId = process.env.ORG_ID;
  const dbUrl = process.env.FIREBASE_DATABASE_URL;

  if (!orgId) { console.error("ERROR: ORG_ID not set in .env"); process.exit(1); }
  if (!dbUrl) { console.error("ERROR: FIREBASE_DATABASE_URL not set in .env"); process.exit(1); }

  const args = process.argv.slice(2);
  const dryRun = !args.includes("--confirm");
  const countIdx = args.indexOf("--count");
  const purchaseCount = countIdx >= 0 ? parseInt(args[countIdx + 1], 10) || 15 : 15;

  admin.initializeApp({
    credential: admin.credential.cert(require(saPath)),
    databaseURL: dbUrl,
  });

  const db = admin.database();

  console.log("╔══════════════════════════════════════════════╗");
  console.log("║       SIONYX — Seed Purchase Records         ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log();
  console.log(`  Organization:  ${orgId}`);
  console.log(`  Mode:          ${dryRun ? "DRY RUN (preview only)" : "⚠  LIVE — will write to DB"}`);
  console.log(`  Count:         ${purchaseCount} purchases`);
  console.log();

  // Fetch existing packages
  console.log("Fetching packages...");
  const pkgSnapshot = await db.ref(`organizations/${orgId}/packages`).once("value");
  const pkgData = pkgSnapshot.val();

  if (!pkgData || typeof pkgData !== "object") {
    console.error("ERROR: No packages found. Create packages first.");
    admin.app().delete();
    process.exit(1);
  }

  const packages = Object.entries(pkgData).map(([id, data]) => ({ id, ...data }));
  console.log(`  Found ${packages.length} package(s):`);
  for (const pkg of packages) {
    const price = pkg.price || 0;
    const discount = pkg.discountPercent || 0;
    const finalPrice = Math.round(price * (1 - discount / 100) * 100) / 100;
    console.log(`    - ${pkg.name}: ₪${finalPrice} (${pkg.minutes || 0} min, ${pkg.validityDays || 0} days validity)`);
  }
  console.log();

  // Fetch existing users
  console.log("Fetching users...");
  const usersSnapshot = await db.ref(`organizations/${orgId}/users`).once("value");
  const usersData = usersSnapshot.val();

  if (!usersData || typeof usersData !== "object") {
    console.error("ERROR: No users found. Create users first.");
    admin.app().delete();
    process.exit(1);
  }

  const users = Object.entries(usersData).map(([uid, data]) => ({ uid, ...data }));
  console.log(`  Found ${users.length} user(s)`);
  console.log();

  // Generate purchases
  const statusWeights = [
    { status: "completed", weight: 0.75 },
    { status: "pending", weight: 0.08 },
    { status: "failed", weight: 0.10 },
    { status: "cancelled", weight: 0.07 },
  ];

  function weightedStatus() {
    const r = Math.random();
    let cumulative = 0;
    for (const { status, weight } of statusWeights) {
      cumulative += weight;
      if (r <= cumulative) return status;
    }
    return "completed";
  }

  const purchases = [];
  for (let i = 0; i < purchaseCount; i++) {
    const pkg = pickRandom(packages);
    const user = pickRandom(users);
    const status = weightedStatus();
    const createdAt = randomDate(60);
    const discount = pkg.discountPercent || 0;
    const amount = Math.round((pkg.price || 0) * (1 - discount / 100) * 100) / 100;

    const purchase = {
      userId: user.uid,
      packageId: pkg.id,
      packageName: pkg.name || "חבילה",
      minutes: pkg.minutes || 0,
      printBudget: pkg.prints || 0,
      validityDays: pkg.validityDays || 0,
      amount,
      status,
      createdAt: createdAt.toISOString(),
      updatedAt: createdAt.toISOString(),
    };

    if (status === "completed") {
      purchase.transactionId = `TXN-${Date.now()}-${randomBetween(1000, 9999)}`;
      const processedAt = new Date(createdAt.getTime() + randomBetween(5, 120) * 1000);
      purchase.callbackReceivedAt = processedAt.toISOString();
      purchase.processedAt = processedAt.toISOString();
    }

    purchases.push(purchase);
  }

  // Display summary
  const sep = "─";
  console.log("Generated purchases:");
  console.log(`┌${sep.repeat(24)}┬${sep.repeat(22)}┬${sep.repeat(10)}┬${sep.repeat(12)}┬${sep.repeat(22)}┐`);
  console.log(`│ ${"User".padEnd(22)} │ ${"Package".padEnd(20)} │ ${"Amount".padStart(8)} │ ${"Status".padEnd(10)} │ ${"Date".padEnd(20)} │`);
  console.log(`├${sep.repeat(24)}┼${sep.repeat(22)}┼${sep.repeat(10)}┼${sep.repeat(12)}┼${sep.repeat(22)}┤`);

  for (const p of purchases) {
    const user = users.find(u => u.uid === p.userId);
    const name = [user?.firstName, user?.lastName].filter(Boolean).join(" ") || p.userId.slice(0, 16);
    const date = new Date(p.createdAt).toLocaleDateString("he-IL");
    console.log(
      `│ ${name.slice(0, 22).padEnd(22)} │ ${(p.packageName || "").slice(0, 20).padEnd(20)} │ ${("₪" + p.amount).padStart(8)} │ ${p.status.padEnd(10)} │ ${date.padEnd(20)} │`
    );
  }
  console.log(`└${sep.repeat(24)}┴${sep.repeat(22)}┴${sep.repeat(10)}┴${sep.repeat(12)}┴${sep.repeat(22)}┘`);

  const completedCount = purchases.filter(p => p.status === "completed").length;
  const totalRevenue = purchases.filter(p => p.status === "completed").reduce((sum, p) => sum + p.amount, 0);
  console.log();
  console.log(`  Total:     ${purchases.length} purchases`);
  console.log(`  Completed: ${completedCount}`);
  console.log(`  Revenue:   ₪${totalRevenue.toFixed(2)}`);
  console.log();

  if (dryRun) {
    console.log("🔍 DRY RUN — no changes made.");
    console.log("   Run with --confirm to write these purchases to the database.");
    admin.app().delete();
    return;
  }

  // Write to database
  console.log("Writing purchases to database...\n");
  const purchasesRef = db.ref(`organizations/${orgId}/purchases`);
  let ok = 0;
  let fail = 0;

  for (const purchase of purchases) {
    try {
      const newRef = purchasesRef.push();
      await newRef.set(purchase);
      ok++;
    } catch (err) {
      console.error(`  ✗ Error writing purchase: ${err.message}`);
      fail++;
    }
  }

  console.log(`Done: ${ok} written, ${fail} errors.`);
  admin.app().delete();
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
