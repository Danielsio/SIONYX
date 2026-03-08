# Release Workflow

Automated semantic versioning for the SIONYX Kiosk installer using
[Conventional Commits](https://www.conventionalcommits.org/) and
[Semantic Versioning](https://semver.org/).

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer: BREAKING CHANGE: <explanation>]
```

### Types that affect version bumps

| Type | Bump | Example |
|------|------|---------|
| `fix:` | PATCH | `fix(auth): handle expired token on login` |
| `feat:` | MINOR | `feat(packages): add bulk pricing editor` |
| `feat!:` | MAJOR | `feat!: redesign payment flow` |
| `BREAKING CHANGE` in footer | MAJOR | Any commit type with this footer |

### Other types (no version bump)

`docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:`

These are still included in the changelog under "Other".

## How to Release

### Option A: Local release (recommended)

```powershell
# Auto-detect bump type from commits since last tag
make release

# Preview without making changes
make release-dry

# Force a specific bump type
make release-patch    # 3.4.0 → 3.4.1
make release-minor    # 3.4.0 → 3.5.0
make release-major    # 3.4.0 → 4.0.0
```

### Option B: CI release (GitHub Actions)

1. Go to **Actions** → **Release** → **Run workflow**
2. Optionally select a bump type override
3. The workflow builds, tags, and creates a GitHub Release with the MSI attached

## What happens during a release

1. **Commit analysis** — `get-next-version.ps1` parses all commits since the last `v*` tag
2. **Version calculation** — highest bump wins (fix=PATCH, feat=MINOR, breaking=MAJOR)
3. **Release branch** — `release/vX.Y.Z` created from main
4. **Build** — tests → publish → WiX MSI → Firebase upload
5. **Changelog** — `CHANGELOG.md` updated with grouped commit entries
6. **Version file** — `sionyx-kiosk-wpf/version.json` updated
7. **Merge + tag** — branch merged to main, `vX.Y.Z` tag created
8. **Push** — main and tag pushed to origin

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/release/release.ps1` | Main orchestrator |
| `scripts/release/get-next-version.ps1` | Analyzes commits, determines version |
| `scripts/release/generate-changelog.ps1` | Generates CHANGELOG.md entries |
| `sionyx-kiosk-wpf/build.ps1` | Builds app + MSI installer |
| `sionyx-kiosk-wpf/upload_release.py` | Uploads MSI to Firebase Storage |

## Version source of truth

`sionyx-kiosk-wpf/version.json` — updated automatically by the release scripts.
Never edit this file manually.

## Git tags

Format: `vMAJOR.MINOR.PATCH` (e.g. `v3.4.0`).
Tags are only for the kiosk installer. The web app has no version tags.
