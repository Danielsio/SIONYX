#!/usr/bin/env python3
"""
Upload SIONYX installer to Firebase Storage and update RTDB metadata.

Called by build.ps1 after a successful NSIS build.

Usage:
    python scripts/upload_release.py <installer_path> <version> <build_number>

Example:
    python scripts/upload_release.py sionyx-kiosk-wpf/sionyx-installer-v3.0.0.exe 3.0.0 1
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Firebase Admin SDK
# ---------------------------------------------------------------------------
try:
    import firebase_admin
    from firebase_admin import credentials, db, storage
except ImportError:
    print("[ERROR] firebase-admin is not installed. Run: pip install firebase-admin")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_KEY = PROJECT_ROOT / "serviceAccountKey.json"
STORAGE_BUCKET = "sionyx-19636.firebasestorage.app"
DATABASE_URL = "https://sionyx-19636-default-rtdb.europe-west1.firebasedatabase.app"


def init_firebase():
    """Initialize Firebase Admin SDK."""
    if not SERVICE_ACCOUNT_KEY.exists():
        env_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        key_path = Path(env_key) if env_key else SERVICE_ACCOUNT_KEY
        if not key_path.exists():
            print(f"[ERROR] Service account key not found at {SERVICE_ACCOUNT_KEY}")
            print("  Place serviceAccountKey.json in project root")
            print("  or set GOOGLE_APPLICATION_CREDENTIALS env var")
            sys.exit(1)
    else:
        key_path = SERVICE_ACCOUNT_KEY

    cred = credentials.Certificate(str(key_path))
    firebase_admin.initialize_app(cred, {
        "storageBucket": STORAGE_BUCKET,
        "databaseURL": DATABASE_URL,
    })
    print(f"[OK] Firebase initialized (bucket: {STORAGE_BUCKET})")


def cleanup_old_installers(current_filename: str):
    """Remove old installer files from Storage, keeping only the current one."""
    bucket = storage.bucket()
    blobs = list(bucket.list_blobs())
    removed = 0
    for blob in blobs:
        name = blob.name
        # Delete old installers and legacy files, keep latest.json and current
        is_old_installer = name.endswith(".exe") and name != current_filename
        is_old_releases = name.startswith("releases/")
        if is_old_installer or is_old_releases:
            blob.delete()
            print(f"  [DEL] {name}")
            removed += 1
    if removed:
        print(f"[OK] Cleaned {removed} old file(s) from Storage")
    else:
        print("[OK] Storage already clean")


def upload_installer(installer_path: Path, version: str) -> tuple[str, int]:
    """Upload installer to Firebase Storage. Returns (download_url, file_size)."""
    if not installer_path.exists():
        print(f"[ERROR] Installer not found: {installer_path}")
        sys.exit(1)

    file_size = installer_path.stat().st_size
    blob_name = installer_path.name  # e.g. sionyx-installer-v3.0.0.exe

    print(f"[INFO] Uploading {blob_name} ({file_size / 1024 / 1024:.1f} MB)...")

    bucket = storage.bucket()
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(installer_path), content_type="application/octet-stream")

    # Make publicly readable
    blob.make_public()
    download_url = blob.public_url

    print(f"[OK] Uploaded: {download_url}")

    # Clean old installers
    print("[INFO] Cleaning old installers from Storage...")
    cleanup_old_installers(blob_name)

    return download_url, file_size


def upload_metadata(version: str, download_url: str, file_size: int, build_number: int):
    """Upload latest.json to Storage and write RTDB metadata."""
    metadata = {
        "version": version,
        "downloadUrl": download_url,
        "filename": f"sionyx-installer-v{version}.exe",
        "releaseDate": datetime.now(timezone.utc).isoformat(),
        "fileSize": file_size,
        "buildNumber": build_number,
        "changelog": [],
    }

    # 1. Upload latest.json to Storage
    print("[INFO] Uploading latest.json to Storage...")
    bucket = storage.bucket()
    blob = bucket.blob("latest.json")
    blob.upload_from_string(
        json.dumps(metadata, indent=2),
        content_type="application/json",
    )
    blob.make_public()
    print(f"[OK] latest.json uploaded: {blob.public_url}")

    # 2. Write to RTDB at public/latestRelease
    print("[INFO] Writing metadata to RTDB...")
    ref = db.reference("public/latestRelease")
    ref.set(metadata)
    print("[OK] RTDB public/latestRelease updated")

    return metadata


def main():
    if len(sys.argv) < 4:
        print("Usage: python scripts/upload_release.py <installer_path> <version> <build_number>")
        print("Example: python scripts/upload_release.py sionyx-kiosk-wpf/sionyx-installer-v3.0.0.exe 3.0.0 1")
        sys.exit(1)

    installer_path = Path(sys.argv[1]).resolve()
    version = sys.argv[2]
    build_number = int(sys.argv[3])

    print()
    print("=" * 60)
    print(f"  SIONYX Release Upload — v{version} (Build #{build_number})")
    print("=" * 60)
    print()

    init_firebase()

    download_url, file_size = upload_installer(installer_path, version)
    metadata = upload_metadata(version, download_url, file_size, build_number)

    print()
    print("=" * 60)
    print("  Upload Complete!")
    print("=" * 60)
    print(f"  Version:      v{version}")
    print(f"  Build:        #{build_number}")
    print(f"  File size:    {file_size / 1024 / 1024:.1f} MB")
    print(f"  Download URL: {download_url}")
    print()


if __name__ == "__main__":
    main()
