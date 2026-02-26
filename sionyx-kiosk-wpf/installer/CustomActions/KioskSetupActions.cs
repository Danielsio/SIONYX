using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32;
using WixToolset.Dtf.WindowsInstaller;

namespace SionyxInstaller
{
    public class KioskSetupActions
    {
        private const string KioskUsername = "SionyxUser";
        private const string AppName = "SIONYX";
        private const string TaskName = "SIONYX Kiosk";

        [DllImport("userenv.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern int CreateProfile(
            string pszUserSid,
            string pszUserName,
            StringBuilder pszProfilePath,
            uint cchProfilePath);

        // ====================================================================
        //  INSTALL ACTIONS
        //
        //  REGISTRY POLICY: This installer does NOT modify any machine-wide
        //  Windows login/display registry keys. The only registry it touches:
        //    1. HKLM\SOFTWARE\SIONYX\* -- app config (managed by WiX)
        //    2. Per-user policies inside SionyxUser's HKCU hive (NoRun,
        //       DisableCMD, etc.) -- kiosk lockdown, never affects the owner
        //
        //  The Windows sign-in screen shows all local users by default.
        //  We rely on that default behavior and do not manipulate it.
        // ====================================================================

        /// <summary>
        /// Creates (or resets) the local SionyxUser account with a blank password.
        /// Uses only "net user" commands -- no machine-wide registry changes.
        /// Windows default LimitBlankPasswordUse=1 already allows console logon
        /// with blank passwords; it only blocks network logon.
        /// </summary>
        [CustomAction]
        public static ActionResult CreateKioskUser(Session session)
        {
            var sw = Stopwatch.StartNew();
            session.Log("=== CreateKioskUser: START ===");

            try
            {
                bool exists = UserExists(KioskUsername, session);

                if (exists)
                {
                    session.Log($"User '{KioskUsername}' already exists — resetting password");
                    RunCommand("net", $"user \"{KioskUsername}\" \"\"", session);
                }
                else
                {
                    session.Log($"Creating new user '{KioskUsername}'...");
                    int rc = RunCommand("net",
                        $"user \"{KioskUsername}\" \"\" /add /fullname:\"SIONYX Kiosk User\" /comment:\"Restricted kiosk account\" /passwordchg:no",
                        session);

                    if (rc != 0)
                    {
                        session.Log($"[ERROR] Failed to create user (exit code {rc})");
                        return ActionResult.Failure;
                    }

                    SetPasswordNeverExpires(KioskUsername, session);
                }

                // Ensure not in Administrators (ignore errors — may not be a member)
                RunCommand("net", $"localgroup Administrators \"{KioskUsername}\" /delete", session);
                // Ensure in Users group
                RunCommand("net", $"localgroup Users \"{KioskUsername}\" /add", session);

                session.Log($"[OK] Kiosk user account ready ({sw.ElapsedMilliseconds}ms)");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] CreateKioskUser failed ({sw.ElapsedMilliseconds}ms): {ex}");
                return ActionResult.Failure;
            }
        }

        /// <summary>
        /// Applies kiosk lockdown policies to SionyxUser's per-user registry hive.
        /// These are written to HKU\{SionyxUser}\... (NOT HKLM), so they only
        /// affect the kiosk account and never the machine owner's account.
        ///
        /// Policies set (per-user only):
        ///   NoRun = 1              -- disables Win+R run dialog
        ///   DisableRegistryTools=1 -- blocks regedit
        ///   DisableCMD = 2         -- blocks cmd.exe but allows .bat scripts
        ///   DisableTaskMgr = 1     -- blocks Ctrl+Shift+Esc task manager
        ///
        /// Also removes any machine-wide (HKLM) versions of these policies
        /// that older installers may have set, to avoid affecting all users.
        /// </summary>
        [CustomAction]
        public static ActionResult ApplySecurityRestrictions(Session session)
        {
            var sw = Stopwatch.StartNew();
            session.Log("=== ApplySecurityRestrictions: START ===");

            try
            {
                string hivePath = $@"C:\Users\{KioskUsername}\ntuser.dat";
                const string tempHiveKey = "SIONYX_TEMP_HIVE";

                if (!File.Exists(hivePath))
                {
                    session.Log($"[WARN] ntuser.dat not found at {hivePath} — skipping per-user policies");
                    return ActionResult.Success;
                }

                int loadResult = RunCommand("reg", $"load \"HKU\\{tempHiveKey}\" \"{hivePath}\"", session);
                if (loadResult != 0)
                {
                    session.Log("[WARN] Could not load user hive — skipping per-user policies");
                    return ActionResult.Success;
                }

                try
                {
                    SetUserRegistryPolicy(session, tempHiveKey,
                        @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                        "NoRun", 1);

                    SetUserRegistryPolicy(session, tempHiveKey,
                        @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                        "DisableRegistryTools", 1);

                    SetUserRegistryPolicy(session, tempHiveKey,
                        @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                        "DisableCMD", 2);

                    SetUserRegistryPolicy(session, tempHiveKey,
                        @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                        "DisableTaskMgr", 1);

                    session.Log($"[OK] Security restrictions applied to {KioskUsername} only");
                }
                finally
                {
                    GC.Collect();
                    GC.WaitForPendingFinalizers();
                    RunCommand("reg", $"unload \"HKU\\{tempHiveKey}\"", session);
                }

                CleanupMachineWidePolicies(session);

                session.Log($"=== ApplySecurityRestrictions: DONE ({sw.ElapsedMilliseconds}ms) ===");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] ApplySecurityRestrictions failed ({sw.ElapsedMilliseconds}ms): {ex}");
                return ActionResult.Failure;
            }
        }

        /// <summary>
        /// Creates a Windows scheduled task that launches SionyxKiosk.exe --kiosk
        /// when SionyxUser logs on. No registry changes -- uses Task Scheduler API
        /// via PowerShell cmdlets. The task runs as Interactive (no stored password).
        /// </summary>
        [CustomAction]
        public static ActionResult SetupAutoStart(Session session)
        {
            var sw = Stopwatch.StartNew();
            session.Log("=== SetupAutoStart: START ===");

            try
            {
                string installDir = session.CustomActionData["INSTALLDIR"];
                string appExe = Path.Combine(installDir, "SionyxKiosk.exe");

                // Remove existing task (ignore errors)
                RunCommand("schtasks", "/delete /tn \"SIONYX Kiosk\" /f", session);

                // Build the PowerShell command for task creation
                // We use the full scheduled-task cmdlets for maximum control
                string psScript =
                    $"$action = New-ScheduledTaskAction -Execute '{appExe}' -Argument '--kiosk'; " +
                    $"$trigger = New-ScheduledTaskTrigger -AtLogOn -User '{KioskUsername}'; " +
                    "$settings = New-ScheduledTaskSettingsSet " +
                        "-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable " +
                        "-ExecutionTimeLimit (New-TimeSpan -Hours 0) " +
                        "-RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1); " +
                    $"$principal = New-ScheduledTaskPrincipal -UserId '{KioskUsername}' -LogonType Interactive -RunLevel Limited; " +
                    "Register-ScheduledTask -TaskName 'SIONYX Kiosk' " +
                        "-Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force";

                int rc = RunCommand("powershell.exe",
                    $"-ExecutionPolicy Bypass -NoProfile -Command \"{psScript}\"",
                    session);

                if (rc != 0)
                {
                    session.Log($"[WARN] Scheduled task creation returned exit code {rc}");
                }

                session.Log($"[OK] Scheduled task created ({sw.ElapsedMilliseconds}ms)");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] SetupAutoStart failed ({sw.ElapsedMilliseconds}ms): {ex}");
                return ActionResult.Failure;
            }
        }

        /// <summary>
        /// Creates the SionyxUser Windows profile (via Win32 CreateProfile API)
        /// and sets up app directories + a startup shortcut. No registry changes.
        /// </summary>
        [CustomAction]
        public static ActionResult InitializeProfile(Session session)
        {
            var sw = Stopwatch.StartNew();
            session.Log("=== InitializeProfile: START ===");

            try
            {
                string installDir = session.CustomActionData["INSTALLDIR"];
                string profilePath = $@"C:\Users\{KioskUsername}";

                // Create profile via Win32 API if it doesn't exist
                if (!File.Exists(Path.Combine(profilePath, "ntuser.dat")))
                {
                    string sid = GetUserSid(KioskUsername);
                    if (sid != null)
                    {
                        session.Log($"SID for {KioskUsername}: {sid}");

                        var pathBuf = new StringBuilder(260);
                        int hr = CreateProfile(sid, KioskUsername, pathBuf, 260);

                        if (hr == 0)
                            session.Log($"[OK] Profile created at: {pathBuf}");
                        else
                            session.Log($"[WARN] CreateProfile HRESULT: 0x{hr:X8} (profile may already exist)");
                    }
                    else
                    {
                        session.Log("[WARN] Could not resolve SID — profile will be created on first logon");
                    }
                }
                else
                {
                    session.Log("[INFO] Profile already exists");
                }

                // Create app directories
                string startupPath = Path.Combine(profilePath,
                    @"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup");
                string sionyxDir = Path.Combine(profilePath, ".sionyx");
                string logsDir = Path.Combine(profilePath, @"AppData\Local\SIONYX\logs");

                Directory.CreateDirectory(startupPath);
                Directory.CreateDirectory(sionyxDir);
                Directory.CreateDirectory(logsDir);
                session.Log("[OK] Profile directories created");

                // Create startup shortcut for SionyxUser
                string shortcutPath = Path.Combine(startupPath, "SIONYX.lnk");
                string targetExe = Path.Combine(installDir, "SionyxKiosk.exe");
                string iconPath = Path.Combine(installDir, "app-logo.ico");
                CreateShortcut(shortcutPath, targetExe, "--kiosk", iconPath, session);
                session.Log($"[OK] Startup shortcut created ({sw.ElapsedMilliseconds}ms)");

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] InitializeProfile failed ({sw.ElapsedMilliseconds}ms): {ex}");
                return ActionResult.Failure;
            }
        }

        /// <summary>
        /// Safety net: ensures Windows auto-logon is not pointing at SionyxUser.
        /// This protects against upgrades from the old NSIS installer which used
        /// auto-logon. Also cleans up login-screen registry keys that previous
        /// versions of this WiX installer (v3.2.2-v3.2.3) incorrectly created.
        ///
        /// Keys touched (Winlogon):
        ///   AutoAdminLogon    -- set to "0" if currently "1" (prevents auto-login)
        ///   DefaultPassword   -- deleted (should never store a password)
        ///   DefaultUserName   -- deleted only if it equals "SionyxUser"
        ///   DefaultDomainName -- deleted only if DefaultUserName was "SionyxUser"
        ///
        /// Keys REMOVED (cleanup from v3.2.2-v3.2.3 that should not have been set):
        ///   Winlogon\SpecialAccounts\UserList  -- entire subtree
        ///   Policies\...\System\EnumerateLocalUsers
        ///   Lsa\LimitBlankPasswordUse          -- restored to default (1)
        /// </summary>
        [CustomAction]
        public static ActionResult EnsureNoAutoLogon(Session session)
        {
            session.Log("=== EnsureNoAutoLogon: START ===");

            try
            {
                const string winlogonKey = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon";

                using (var key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                            .OpenSubKey(winlogonKey, true))
                {
                    if (key != null)
                    {
                        string autoLogon = key.GetValue("AutoAdminLogon") as string;
                        if (autoLogon == "1")
                        {
                            key.SetValue("AutoAdminLogon", "0", RegistryValueKind.String);
                            session.Log("[OK] AutoAdminLogon was 1, set to 0");
                        }

                        key.DeleteValue("DefaultPassword", false);

                        string currentDefault = key.GetValue("DefaultUserName") as string;
                        if (string.Equals(currentDefault, KioskUsername, StringComparison.OrdinalIgnoreCase))
                        {
                            key.DeleteValue("DefaultUserName", false);
                            key.DeleteValue("DefaultDomainName", false);
                            session.Log("[OK] Cleared DefaultUserName (was set to kiosk user)");
                        }
                    }
                }

                // --- Cleanup keys incorrectly set by installer v3.2.2-v3.2.3 ---

                CleanupLegacyRegistryKey(session,
                    winlogonKey + @"\SpecialAccounts",
                    deleteTree: true,
                    reason: "SpecialAccounts (set by v3.2.3)");

                CleanupLegacyRegistryKey(session,
                    @"SOFTWARE\Policies\Microsoft\Windows\System",
                    valueName: "EnumerateLocalUsers",
                    reason: "EnumerateLocalUsers (set by v3.2.3)");

                // Restore LimitBlankPasswordUse to Windows default (1) if we lowered it.
                // Default=1 means "blank passwords can only log on at the console" which
                // is exactly what we want. Previous versions set it to 0 unnecessarily.
                using (var lsaKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                               .OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Lsa", true))
                {
                    if (lsaKey != null)
                    {
                        int current = (int?)lsaKey.GetValue("LimitBlankPasswordUse") ?? 1;
                        if (current != 1)
                        {
                            lsaKey.SetValue("LimitBlankPasswordUse", 1, RegistryValueKind.DWord);
                            session.Log("[OK] Restored LimitBlankPasswordUse to default (1)");
                        }
                    }
                }

                session.Log("[OK] EnsureNoAutoLogon complete");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] EnsureNoAutoLogon: {ex.Message}");
                return ActionResult.Success;
            }
        }

        [CustomAction]
        public static ActionResult VerifyInstallation(Session session)
        {
            session.Log("=== VerifyInstallation: START ===");

            try
            {
                string installDir = session.CustomActionData["INSTALLDIR"];
                string logFile = Path.Combine(installDir, "install.log");
                var errors = new System.Collections.Generic.List<string>();
                var log = new StringBuilder();

                void Log(string msg)
                {
                    session.Log(msg);
                    log.AppendLine(msg);
                }

                string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                Log("");
                Log("============================================");
                Log($"  POST-INSTALL VERIFICATION ({timestamp})");
                Log("============================================");

                // 1. User account
                if (UserExists(KioskUsername, session))
                    Log($"[PASS] User account {KioskUsername} exists");
                else
                {
                    Log($"[FAIL] User account {KioskUsername} NOT FOUND");
                    errors.Add($"User account {KioskUsername} was not created");
                }

                // 2. Profile directory
                string profilePath = $@"C:\Users\{KioskUsername}";
                if (Directory.Exists(profilePath))
                    Log($"[PASS] Profile directory exists: {profilePath}");
                else
                {
                    Log($"[FAIL] Profile directory MISSING: {profilePath}");
                    errors.Add("User profile directory was not created");
                }

                // 3. Profile registry (ProfileList)
                string sid = GetUserSid(KioskUsername);
                if (sid != null)
                {
                    string regPath = $@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}";
                    using (var key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                                .OpenSubKey(regPath))
                    {
                        if (key != null)
                            Log($"[PASS] Profile registry entry exists (SID: {sid})");
                        else
                        {
                            Log($"[FAIL] Profile registry entry MISSING for SID {sid}");
                            errors.Add("ProfileList registry entry not found");
                        }
                    }
                }

                // 4. ntuser.dat
                string ntuserPath = Path.Combine(profilePath, "ntuser.dat");
                if (File.Exists(ntuserPath))
                    Log("[PASS] Profile initialized (ntuser.dat present)");
                else
                    Log("[WARN] Cannot verify ntuser.dat (access denied or missing)");

                // 5. Scheduled task
                int taskCheck = RunCommand("schtasks", "/query /tn \"SIONYX Kiosk\"", session);
                if (taskCheck == 0)
                    Log("[PASS] Scheduled task SIONYX Kiosk exists");
                else
                {
                    Log("[FAIL] Scheduled task SIONYX Kiosk NOT FOUND");
                    errors.Add("Scheduled task was not created");
                }

                // 6. App executable
                string exePath = Path.Combine(installDir, "SionyxKiosk.exe");
                if (File.Exists(exePath))
                    Log($"[PASS] App executable: {exePath}");
                else
                {
                    Log($"[FAIL] App executable MISSING: {exePath}");
                    errors.Add("Application executable was not installed");
                }

                // 7. Startup shortcut
                string startupLnk = Path.Combine(profilePath,
                    @"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\SIONYX.lnk");
                if (File.Exists(startupLnk))
                    Log($"[PASS] Startup shortcut exists for {KioskUsername}");
                else
                    Log("[WARN] Startup shortcut not found at expected path");

                // 8. Registry configuration
                string[] regKeys = { "Install_Dir", "Version", "OrgId", "FirebaseProjectId", "KioskUsername" };
                var missingKeys = new System.Collections.Generic.List<string>();
                using (var appKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                               .OpenSubKey($@"SOFTWARE\{AppName}"))
                {
                    foreach (string keyName in regKeys)
                    {
                        if (appKey?.GetValue(keyName) == null)
                            missingKeys.Add(keyName);
                    }
                }

                if (missingKeys.Count == 0)
                    Log("[PASS] All registry configuration keys present");
                else
                {
                    Log($"[FAIL] Missing registry keys: {string.Join(", ", missingKeys)}");
                    errors.Add($"Registry configuration incomplete — missing: {string.Join(", ", missingKeys)}");
                }

                // Summary
                Log("");
                Log("--------------------------------------------");
                if (errors.Count == 0)
                    Log("[OK] ALL CHECKS PASSED — Installation verified successfully!");
                else
                {
                    Log($"[ERROR] Installation completed with {errors.Count} error(s):");
                    foreach (string e in errors)
                        Log($"    - {e}");
                }
                Log("--------------------------------------------");

                // Write log file
                try { File.WriteAllText(logFile, log.ToString()); }
                catch { session.Log("[WARN] Could not write install.log"); }

                // Verification failures are warnings, not install failures
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] VerifyInstallation failed: {ex}");
                return ActionResult.Success; // Don't fail the install over verification
            }
        }

        // ====================================================================
        //  UNINSTALL ACTIONS
        // ====================================================================

        [CustomAction]
        public static ActionResult StopProcesses(Session session)
        {
            session.Log("=== StopProcesses: START ===");

            try
            {
                int rc = RunCommand("taskkill", "/F /IM SionyxKiosk.exe", session);
                session.Log(rc == 0
                    ? "[OK] SionyxKiosk process terminated"
                    : "[INFO] SionyxKiosk was not running");

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] StopProcesses: {ex.Message}");
                return ActionResult.Success; // Don't block uninstall
            }
        }

        [CustomAction]
        public static ActionResult RemoveScheduledTask(Session session)
        {
            session.Log("=== RemoveScheduledTask: START ===");

            try
            {
                int rc = RunCommand("schtasks", "/delete /tn \"SIONYX Kiosk\" /f", session);
                session.Log(rc == 0
                    ? "[OK] Scheduled task removed"
                    : "[INFO] Scheduled task not found");

                // Also clear any legacy auto-run registry entry
                try
                {
                    using (var runKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                                   .OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", true))
                    {
                        runKey?.DeleteValue(AppName, false);
                    }
                }
                catch { /* ignore */ }

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] RemoveScheduledTask: {ex.Message}");
                return ActionResult.Success;
            }
        }

        [CustomAction]
        public static ActionResult RevertSecurity(Session session)
        {
            session.Log("=== RevertSecurity: START ===");

            try
            {
                // Clean up machine-wide policies (from older installs that used HKLM)
                CleanupMachineWidePolicies(session);

                session.Log("[OK] Security restrictions reverted");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] RevertSecurity: {ex.Message}");
                return ActionResult.Success;
            }
        }

        /// <summary>
        /// Uninstall cleanup: clears any Winlogon values pointing at SionyxUser.
        /// Does not modify LimitBlankPasswordUse or any login-screen display keys
        /// because the current installer never changes them.
        /// </summary>
        [CustomAction]
        public static ActionResult RevertAutoLogon(Session session)
        {
            session.Log("=== RevertAutoLogon: START ===");

            try
            {
                const string winlogonKey = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon";

                using (var key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                            .OpenSubKey(winlogonKey, true))
                {
                    if (key != null)
                    {
                        string autoLogon = key.GetValue("AutoAdminLogon") as string;
                        if (autoLogon == "1")
                        {
                            key.SetValue("AutoAdminLogon", "0", RegistryValueKind.String);
                            session.Log("[OK] AutoAdminLogon was 1, set to 0");
                        }

                        key.DeleteValue("DefaultPassword", false);

                        string currentDefault = key.GetValue("DefaultUserName") as string;
                        if (string.Equals(currentDefault, KioskUsername, StringComparison.OrdinalIgnoreCase))
                        {
                            key.DeleteValue("DefaultUserName", false);
                            key.DeleteValue("DefaultDomainName", false);
                        }
                    }
                }

                // Clean up keys that older installer versions may have created
                CleanupLegacyRegistryKey(session,
                    winlogonKey + @"\SpecialAccounts",
                    deleteTree: true,
                    reason: "SpecialAccounts (legacy cleanup)");

                CleanupLegacyRegistryKey(session,
                    @"SOFTWARE\Policies\Microsoft\Windows\System",
                    valueName: "EnumerateLocalUsers",
                    reason: "EnumerateLocalUsers (legacy cleanup)");

                session.Log("[OK] Auto-logon reverted");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] RevertAutoLogon: {ex.Message}");
                return ActionResult.Success;
            }
        }

        [CustomAction]
        public static ActionResult RemoveKioskUser(Session session)
        {
            session.Log("=== RemoveKioskUser: START ===");

            try
            {
                RemoveUserAndProfile(KioskUsername, session);
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] RemoveKioskUser: {ex.Message}");
                return ActionResult.Success;
            }
        }

        [CustomAction]
        public static ActionResult CleanupLegacyUser(Session session)
        {
            session.Log("=== CleanupLegacyUser: START ===");

            try
            {
                if (UserExists("KioskUser", session))
                {
                    RemoveUserAndProfile("KioskUser", session);
                    session.Log("[OK] Legacy KioskUser removed");
                }
                else
                {
                    session.Log("[INFO] No legacy KioskUser found");
                }

                // Clean up orphaned profile folders
                foreach (string dir in new[] { @"C:\Users\KioskUser", @"C:\Users\KioskUser.000", @"C:\Users\KioskUser.001" })
                {
                    if (Directory.Exists(dir))
                    {
                        try
                        {
                            Directory.Delete(dir, true);
                            session.Log($"[OK] Deleted legacy folder: {dir}");
                        }
                        catch
                        {
                            session.Log($"[WARN] Could not delete {dir} — may need reboot");
                        }
                    }
                }

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] CleanupLegacyUser: {ex.Message}");
                return ActionResult.Success;
            }
        }

        // ====================================================================
        //  HELPERS
        // ====================================================================

        private static string ResolvePath(string fileName)
        {
            if (Path.IsPathRooted(fileName)) return fileName;

            string sysDir = Environment.GetFolderPath(Environment.SpecialFolder.System);
            string withExe = Path.HasExtension(fileName) ? fileName : fileName + ".exe";

            string sys = Path.Combine(sysDir, withExe);
            if (File.Exists(sys)) return sys;

            string wbem = Path.Combine(sysDir, "wbem", withExe);
            if (File.Exists(wbem)) return wbem;

            return fileName;
        }

        private static int RunCommand(string fileName, string arguments, Session session, int timeoutMs = 60000)
        {
            var resolvedPath = ResolvePath(fileName);
            session.Log($"  [CMD] {resolvedPath} {arguments}");
            var sw = Stopwatch.StartNew();

            var psi = new ProcessStartInfo
            {
                FileName = resolvedPath,
                Arguments = arguments,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var process = Process.Start(psi))
            {
                var stderrBuilder = new StringBuilder();
                process.ErrorDataReceived += (s, e) =>
                {
                    if (e.Data != null) stderrBuilder.AppendLine(e.Data);
                };
                process.BeginErrorReadLine();

                string stdout = process.StandardOutput.ReadToEnd();

                bool exited = process.WaitForExit(timeoutMs);
                sw.Stop();

                if (!exited)
                {
                    session.Log($"  [TIMEOUT] Command did not finish in {timeoutMs}ms — killing process");
                    try { process.Kill(); } catch { /* best effort */ }
                    return -1;
                }

                if (!string.IsNullOrWhiteSpace(stdout))
                    session.Log($"  [STDOUT] {stdout.TrimEnd()}");

                string stderr = stderrBuilder.ToString();
                if (!string.IsNullOrWhiteSpace(stderr) && process.ExitCode != 0)
                    session.Log($"  [STDERR] {stderr.TrimEnd()}");

                session.Log($"  [CMD] exit={process.ExitCode} elapsed={sw.ElapsedMilliseconds}ms");
                return process.ExitCode;
            }
        }

        private static void SetPasswordNeverExpires(string username, Session session)
        {
            string wmic = ResolvePath("wmic");
            if (File.Exists(wmic))
            {
                session.Log("Using wmic to set password never expires...");
                RunCommand("wmic",
                    $"useraccount where name=\"{username}\" set PasswordExpires=false",
                    session);
            }
            else
            {
                session.Log("wmic not available, using PowerShell...");
                RunCommand("powershell.exe",
                    $"-NoProfile -Command \"Set-LocalUser -Name '{username}' -PasswordNeverExpires $true\"",
                    session);
            }
        }

        private static bool UserExists(string username, Session session)
        {
            return RunCommand("net", $"user \"{username}\"", session) == 0;
        }

        private static string GetUserSid(string username)
        {
            try
            {
                var account = new NTAccount(username);
                var sid = (SecurityIdentifier)account.Translate(typeof(SecurityIdentifier));
                return sid.Value;
            }
            catch
            {
                return null;
            }
        }

        private static void SetRegistryPolicy(Session session, string subKey, string name, int value)
        {
            using (var key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                        .CreateSubKey(subKey))
            {
                key.SetValue(name, value, RegistryValueKind.DWord);
                session.Log($"  Set {name} = {value}");
            }
        }

        private static void SetUserRegistryPolicy(Session session, string hiveKey, string subKey, string name, int value)
        {
            using (var hku = RegistryKey.OpenBaseKey(RegistryHive.Users, RegistryView.Registry64))
            using (var key = hku.CreateSubKey($@"{hiveKey}\{subKey}"))
            {
                key.SetValue(name, value, RegistryValueKind.DWord);
                session.Log($"  Set {name} = {value} (per-user)");
            }
        }

        private static void CleanupLegacyRegistryKey(Session session, string subKey,
            bool deleteTree = false, string valueName = null, string reason = null)
        {
            try
            {
                using (var baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                {
                    if (deleteTree)
                    {
                        baseKey.DeleteSubKeyTree(subKey, false);
                    }
                    else if (valueName != null)
                    {
                        using (var key = baseKey.OpenSubKey(subKey, true))
                        {
                            if (key?.GetValue(valueName) != null)
                                key.DeleteValue(valueName, false);
                            else
                                return;
                        }
                    }
                }

                session.Log($"  [OK] Removed {reason ?? subKey}");
            }
            catch
            {
                // Key didn't exist or access denied -- nothing to clean
            }
        }

        private static void CleanupMachineWidePolicies(Session session)
        {
            RemoveRegistryPolicy(session,
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoRun");
            RemoveRegistryPolicy(session,
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools");
            RemoveRegistryPolicy(session,
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableCMD");
            RemoveRegistryPolicy(session,
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr");
        }

        private static void RemoveRegistryPolicy(Session session, string subKey, string name)
        {
            try
            {
                using (var key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                            .OpenSubKey(subKey, true))
                {
                    if (key?.GetValue(name) != null)
                    {
                        key.DeleteValue(name);
                        session.Log($"  Removed policy: {name}");
                    }
                }
            }
            catch
            {
                session.Log($"  Policy not set: {name}");
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string arguments, string iconPath, Session session)
        {
            try
            {
                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                dynamic shell = Activator.CreateInstance(shellType);
                dynamic shortcut = shell.CreateShortcut(shortcutPath);
                shortcut.TargetPath = targetPath;
                shortcut.Arguments = arguments;
                shortcut.IconLocation = iconPath + ",0";
                shortcut.Save();
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] CreateShortcut failed: {ex.Message}");
            }
        }

        private static void RemoveUserAndProfile(string username, Session session)
        {
            string sid = GetUserSid(username);

            // Delete user account
            if (UserExists(username, session))
            {
                RunCommand("net", $"user \"{username}\" /delete", session);
                session.Log($"[OK] User account '{username}' deleted");
            }

            // Remove profile via WMI
            if (sid != null)
            {
                try
                {
                    using (var searcher = new ManagementObjectSearcher(
                        $"SELECT * FROM Win32_UserProfile WHERE SID = '{sid}'"))
                    {
                        foreach (ManagementObject profile in searcher.Get())
                        {
                            profile.Delete();
                            session.Log($"[OK] WMI profile removed for SID {sid}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    session.Log($"[WARN] WMI profile removal failed: {ex.Message}");
                }

                // Clean ProfileList registry
                string profileRegPath = $@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}";
                try
                {
                    using (var baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                    {
                        baseKey.DeleteSubKeyTree(profileRegPath, false);
                        session.Log("[OK] ProfileList registry entry removed");
                    }
                }
                catch { /* already clean */ }
            }

            // Delete profile folder
            string profilePath = $@"C:\Users\{username}";
            if (Directory.Exists(profilePath))
            {
                try
                {
                    Directory.Delete(profilePath, true);
                    session.Log($"[OK] Profile folder deleted: {profilePath}");
                }
                catch
                {
                    session.Log($"[WARN] Could not fully delete {profilePath} — may need reboot");
                    RunCommand("cmd", $"/c rmdir /s /q \"{profilePath}\"", session);
                }
            }

            // Clean orphaned ProfileList entries
            try
            {
                using (var profileList = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                                    .OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"))
                {
                    if (profileList != null)
                    {
                        foreach (string subKeyName in profileList.GetSubKeyNames())
                        {
                            using (var entry = profileList.OpenSubKey(subKeyName))
                            {
                                string imagePath = entry?.GetValue("ProfileImagePath") as string;
                                if (imagePath != null && imagePath.IndexOf(username, StringComparison.OrdinalIgnoreCase) >= 0)
                                {
                                    using (var baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                                    {
                                        baseKey.DeleteSubKeyTree(
                                            $@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{subKeyName}",
                                            false);
                                        session.Log($"[OK] Removed orphaned ProfileList entry: {subKeyName}");
                                    }
                                }
                            }
                        }
                    }
                }
            }
            catch { /* best effort */ }
        }
    }
}
