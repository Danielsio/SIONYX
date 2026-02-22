# NSIS → WiX Migration Tracker

## Why Migrate?
NSIS is a 32-bit installer that requires `Sysnative` hacks to interact with the 64-bit
registry and system tools. WiX produces native 64-bit MSI packages using the Windows
Installer engine, eliminating registry-view mismatches and giving us:

- **Native 64-bit MSI** — no WOW64 redirection issues
- **C# custom actions** — replaces inline PowerShell strings embedded in NSIS FileWrite calls
- **Automatic uninstall** — MSI tracks every file, registry key, and shortcut it installs
- **Declarative** — files, registry, shortcuts defined in XML instead of imperative script
- **`dotnet build` integration** — WiX 6 is an MSBuild SDK; fits the existing .NET 8 pipeline
- **MajorUpgrade** — automatic upgrade handling (detect previous version, uninstall, install new)

## Architecture

```
installer/
├── SionyxInstaller.wixproj          # WiX MSBuild SDK project (produces .msi)
├── Package.wxs                       # Product: files, registry, shortcuts, CA scheduling, UI
├── OrgNameDlg.wxs                    # Custom dialog for organization name input
├── LICENSE.rtf                       # License in RTF (required by WiX UI)
└── CustomActions/
    ├── CustomActions.csproj          # .NET Framework 4.7.2 (required by WiX DTF)
    └── KioskSetupActions.cs          # All install/uninstall custom actions in C#
```

## Migration Checklist

### Phase 1: Project Setup
- [x] Create `installer/` directory structure
- [x] Create `CustomActions.csproj` (net472, DTF references)
- [x] Create `SionyxInstaller.wixproj` (WixToolset.Sdk 6.0.2)
- [x] Add projects to `SionyxKiosk.sln`

### Phase 2: Core MSI (Package.wxs)
- [x] Directory structure (`ProgramFiles6432Folder\SIONYX`)
- [x] File components (SionyxKiosk.exe, app-logo.ico, Assets/templates)
- [x] Registry keys (Install_Dir, Version, OrgId, Firebase config, etc.)
- [x] Desktop + Start Menu shortcuts
- [x] Add/Remove Programs entry (automatic via `MajorUpgrade`)
- [x] License agreement (RTF)
- [x] Detect existing NSIS install (launch condition)

### Phase 3: Custom UI
- [x] Organization name dialog (OrgNameDlg.wxs)
- [x] Text input bound to `ORGID` property
- [x] Validation (non-empty)
- [x] Dialog sequence: InstallDirDlg → OrgNameDlg → VerifyReadyDlg

### Phase 4: Install Custom Actions (C#)
- [x] `CreateKioskUser` — enable blank passwords, create/update SionyxUser, set group membership
- [x] `ApplySecurityRestrictions` — NoRun, DisableCMD, DisableRegistryTools, DisableTaskMgr
- [x] `SetupAutoStart` — create "SIONYX Kiosk" scheduled task
- [x] `InitializeProfile` — CreateProfile API, directories, startup shortcut
- [x] `VerifyInstallation` — post-install checks, write install.log

### Phase 5: Uninstall Custom Actions (C#)
- [x] `StopProcesses` — kill SionyxKiosk.exe
- [x] `RemoveScheduledTask` — delete scheduled task
- [x] `RevertSecurity` — remove restriction policies
- [x] `RemoveKioskUser` — delete user, profile, registry cleanup
- [x] `CleanupLegacyUser` — remove old "KioskUser" from pre-v3.0.16

### Phase 6: Build Pipeline
- [x] Update `build.ps1` — replace NSIS with `dotnet build` on WiX project
- [x] Update `Makefile` — no changes needed (calls build.ps1)
- [x] Deprecate `installer.nsi` (kept as reference)

### Phase 7: Verification
- [ ] Build installer successfully (`make build-local`)
- [ ] Install on clean machine
- [ ] Verify all registry keys present (64-bit view)
- [ ] Verify SionyxUser created with correct permissions
- [ ] Verify scheduled task created
- [ ] Verify shortcuts (Desktop, Start Menu, SionyxUser Startup)
- [ ] Verify uninstall cleans up everything
- [ ] Verify upgrade from previous NSIS version

## NSIS → WiX Feature Mapping

| NSIS Feature | WiX Equivalent |
|---|---|
| `File "SionyxKiosk.exe"` | `<File Source="..."/>` (declarative) |
| `WriteRegStr HKLM ...` | `<RegistryValue Root="HKLM" .../>` (declarative) |
| `CreateShortCut` | `<Shortcut>` element (declarative) |
| `WriteUninstaller` | Automatic (MSI tracks everything) |
| `nsExec::ExecToLog 'powershell ...'` | C# custom action with `Process.Start` or direct .NET APIs |
| `Page custom OrgPagePre` | `<Dialog>` element with `<Control Type="Edit">` |
| `.onInit` upgrade check | `<MajorUpgrade>` element (automatic) |
| `DumpLog` function | `session.Log()` + file logging in custom action |
| `SetRegView 64` | Not needed — native 64-bit MSI |
| `$WINDIR\Sysnative\powershell.exe` | Not needed — 64-bit process context |

## Key Differences

1. **Uninstall is automatic.** MSI removes every file, registry key, and shortcut it installed.
   Custom actions only needed for kiosk-specific cleanup (user account, scheduled task, policies).

2. **Upgrade is automatic.** `MajorUpgrade` detects previous MSI versions by `UpgradeCode` GUID
   and uninstalls before installing. No manual `.onInit` check needed.

3. **Custom actions are deferred.** They run under SYSTEM with elevated privileges. Data must be
   passed via `CustomActionData` (not direct property access).

4. **64-bit is native.** The MSI engine is 64-bit on 64-bit Windows. No registry view confusion,
   no Sysnative workarounds, no WOW6432Node surprises.
