#!/usr/bin/env node
/**
 * Seed global announcements for the kiosk home page.
 *
 * Usage:
 *   node scripts/seed-announcements.js                 # dry-run
 *   node scripts/seed-announcements.js --confirm       # write to DB
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

async function main() {
  loadEnv();

  const orgId = process.env.ORG_ID;
  const dbUrl = process.env.FIREBASE_DATABASE_URL;

  if (!orgId) { console.error("ERROR: ORG_ID not set in .env"); process.exit(1); }
  if (!dbUrl) { console.error("ERROR: FIREBASE_DATABASE_URL not set in .env"); process.exit(1); }

  const args = process.argv.slice(2);
  const dryRun = !args.includes("--confirm");

  admin.initializeApp({
    credential: admin.credential.cert(require(saPath)),
    databaseURL: dbUrl,
  });

  const db = admin.database();

  const announcements = [
    {
      title: "ברוכים הבאים למערכת הקיוסק!",
      body: "שמחים לראות אותך כאן. אנחנו כאן כדי לעזור לך להפיק את המירב מהשירות שלך. אם יש לך שאלות, אל תהסס לפנות אלינו.",
      type: "info",
      active: true,
      createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      title: "הנחה מיוחדת - 20% על החבילה החודשית",
      body: "רק השבוע! קבל 20% הנחה על חבילת ה-VIP החודשית. ההצעה בתוקף עד יום שישי.",
      type: "promotion",
      active: true,
      createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      title: "שעות פעילות מעודכנות",
      body: "החל מהשבוע הבא שעות הפעילות יהיו 08:00-22:00 בימים א׳-ה׳ ו-09:00-18:00 בימי שישי.",
      type: "warning",
      active: true,
      createdAt: new Date().toISOString(),
    },
  ];

  console.log("╔══════════════════════════════════════════════╗");
  console.log("║    SIONYX — Seed Global Announcements        ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log();
  console.log(`  Organization:  ${orgId}`);
  console.log(`  Mode:          ${dryRun ? "DRY RUN" : "⚠  LIVE"}`);
  console.log(`  Announcements: ${announcements.length}`);
  console.log();

  for (const a of announcements) {
    console.log(`  [${a.type}] ${a.title}`);
    console.log(`         ${a.body.slice(0, 60)}...`);
    console.log();
  }

  if (dryRun) {
    console.log("🔍 DRY RUN — no changes made.");
    console.log("   Run with --confirm to write announcements.");
    admin.app().delete();
    return;
  }

  const ref = db.ref(`organizations/${orgId}/announcements`);
  let ok = 0;
  for (const a of announcements) {
    try {
      await ref.push().set(a);
      ok++;
    } catch (err) {
      console.error(`  ✗ ${a.title}: ${err.message}`);
    }
  }

  console.log(`Done: ${ok} announcements written.`);
  admin.app().delete();
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
