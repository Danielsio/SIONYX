using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32;
using WixToolset.Dtf.WindowsInstaller;

namespace SionyxInstaller
{
    /// <summary>
    /// WiX custom actions for SIONYX Kiosk installer.
    ///
    /// System registry changes (outside HKLM\SOFTWARE\SIONYX):
    ///   - Lsa\LimitBlankPasswordUse = 0  (required for blank-password user tiles)
    ///   - Per-user policies in SionyxUser's HKU hive only (never HKLM)
    ///
    /// No other system keys are modified. If a host machine has non-standard
    /// Windows configuration, that should be resolved separately.
    /// </summary>
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
        // ====================================================================

        /// <summary>
        /// Creates (or resets) the local SionyxUser account with a blank password.
        /// Sets LimitBlankPasswordUse=0 so credential providers show the account
        /// on the Windows sign-in screen.
        /// </summary>
        [CustomAction]
        public static ActionResult CreateKioskUser(Session session)
        {
            var sw = Stopwatch.StartNew();
            session.Log("=== CreateKioskUser: START ===");

            try
            {
                // Allow blank-password accounts to appear on login screen
                SetLimitBlankPasswordUse(session, enabled: false);

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

                RunCommand("net", $"localgroup Administrators \"{KioskUsername}\" /delete", session);
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
        /// Written to HKU\{SionyxUser}\... (NOT HKLM) so they only affect the
        /// kiosk account, never the machine owner.
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
        /// Creates a scheduled task that launches SionyxKiosk.exe --kiosk
        /// when SionyxUser logs on.
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

                RunCommand("schtasks", "/delete /tn \"SIONYX Kiosk\" /f", session);

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
                    session.Log($"[WARN] Scheduled task creation returned exit code {rc}");

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
        /// and sets up app directories + a startup shortcut.
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

                string startupPath = Path.Combine(profilePath,
                    @"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup");
                string sionyxDir = Path.Combine(profilePath, ".sionyx");
                string logsDir = Path.Combine(profilePath, @"AppData\Local\SIONYX\logs");

                Directory.CreateDirectory(startupPath);
                Directory.CreateDirectory(sionyxDir);
                Directory.CreateDirectory(logsDir);
                session.Log("[OK] Profile directories created");

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
        /// Post-install verification: checks user, profile, task, exe, and registry.
        /// Writes results to install.log. Only shows a MessageBox if errors are found;
        /// on success, the WiX finish page shows next steps.
        /// </summary>
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

                // 4. Scheduled task
                int taskCheck = RunCommand("schtasks", "/query /tn \"SIONYX Kiosk\"", session);
                if (taskCheck == 0)
                    Log("[PASS] Scheduled task SIONYX Kiosk exists");
                else
                {
                    Log("[FAIL] Scheduled task SIONYX Kiosk NOT FOUND");
                    errors.Add("Scheduled task was not created");
                }

                // 5. App executable
                string exePath = Path.Combine(installDir, "SionyxKiosk.exe");
                if (File.Exists(exePath))
                    Log($"[PASS] App executable: {exePath}");
                else
                {
                    Log($"[FAIL] App executable MISSING: {exePath}");
                    errors.Add("Application executable was not installed");
                }

                // 6. Startup shortcut
                string startupLnk = Path.Combine(profilePath,
                    @"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\SIONYX.lnk");
                if (File.Exists(startupLnk))
                    Log($"[PASS] Startup shortcut exists for {KioskUsername}");
                else
                    Log("[WARN] Startup shortcut not found at expected path");

                // 7. Registry configuration
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

                // 8. LimitBlankPasswordUse
                using (var lsaKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                               .OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Lsa"))
                {
                    int lbp = (int?)lsaKey?.GetValue("LimitBlankPasswordUse") ?? -1;
                    if (lbp == 0)
                        Log("[PASS] LimitBlankPasswordUse = 0 (blank-password tiles enabled)");
                    else
                    {
                        Log($"[FAIL] LimitBlankPasswordUse = {lbp} (expected 0)");
                        errors.Add($"LimitBlankPasswordUse is {lbp}, must be 0 for SionyxUser to appear on login screen");
                    }
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

                try { File.WriteAllText(logFile, log.ToString()); }
                catch { session.Log("[WARN] Could not write install.log"); }

                // Only show a MessageBox if verification found errors.
                // On success, the WiX finish page shows next steps — no popup needed.
                if (errors.Count > 0)
                {
                    string uiLevelStr = session.CustomActionData.ContainsKey("UILEVEL")
                        ? session.CustomActionData["UILEVEL"] : "5";
                    bool isSilent = int.TryParse(uiLevelStr, out int uiLevel) && uiLevel <= 3;

                    if (!isSilent)
                    {
                        try
                        {
                            string summary = $"{errors.Count} CHECK(S) FAILED\n\n" +
                                string.Join("\n", errors) +
                                $"\n\nFull log: {logFile}";

                            MessageBoxFromInstaller(
                                "SIONYX — Install Issues Detected",
                                summary,
                                0x00000030u); // WARNING icon
                        }
                        catch (Exception mbEx)
                        {
                            session.Log($"[WARN] Could not show MessageBox: {mbEx.Message}");
                        }
                    }
                }

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] VerifyInstallation failed: {ex}");
                return ActionResult.Success;
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
                session.Log(rc == 0 ? "[OK] SionyxKiosk terminated" : "[INFO] SionyxKiosk was not running");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] StopProcesses: {ex.Message}");
                return ActionResult.Success;
            }
        }

        [CustomAction]
        public static ActionResult RemoveScheduledTask(Session session)
        {
            session.Log("=== RemoveScheduledTask: START ===");
            try
            {
                int rc = RunCommand("schtasks", "/delete /tn \"SIONYX Kiosk\" /f", session);
                session.Log(rc == 0 ? "[OK] Scheduled task removed" : "[INFO] Scheduled task not found");
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
                // Remove any machine-wide policies (from older installs that used HKLM)
                RemoveRegistryPolicy(session, @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoRun");
                RemoveRegistryPolicy(session, @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools");
                RemoveRegistryPolicy(session, @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableCMD");
                RemoveRegistryPolicy(session, @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr");

                session.Log("[OK] Security restrictions reverted");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[WARN] RevertSecurity: {ex.Message}");
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

        // ====================================================================
        //  HELPERS
        // ====================================================================

        /// <summary>
        /// Sets LimitBlankPasswordUse. When disabled (value=0), Windows credential
        /// providers show blank-password accounts on the sign-in screen.
        /// This is the only system registry value the installer modifies.
        /// </summary>
        private static void SetLimitBlankPasswordUse(Session session, bool enabled)
        {
            try
            {
                using (var lsaKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
                                               .OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Lsa", true))
                {
                    if (lsaKey == null)
                    {
                        session.Log("[ERROR] Cannot open HKLM\\SYSTEM\\...\\Lsa");
                        return;
                    }

                    int value = enabled ? 1 : 0;
                    lsaKey.SetValue("LimitBlankPasswordUse", value, RegistryValueKind.DWord);
                    session.Log($"[OK] LimitBlankPasswordUse = {value}");
                }
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] LimitBlankPasswordUse: {ex.Message}");
            }
        }

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);

        private static void MessageBoxFromInstaller(string title, string text, uint type)
        {
            MessageBoxW(IntPtr.Zero, text, title, type | 0x00040000); // MB_TOPMOST
        }

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
                RunCommand("wmic",
                    $"useraccount where name=\"{username}\" set PasswordExpires=false",
                    session);
            }
            else
            {
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

        private static void SetUserRegistryPolicy(Session session, string hiveKey, string subKey, string name, int value)
        {
            using (var hku = RegistryKey.OpenBaseKey(RegistryHive.Users, RegistryView.Registry64))
            using (var key = hku.CreateSubKey($@"{hiveKey}\{subKey}"))
            {
                key.SetValue(name, value, RegistryValueKind.DWord);
                session.Log($"  Set {name} = {value} (per-user)");
            }
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

            if (UserExists(username, session))
            {
                RunCommand("net", $"user \"{username}\" /delete", session);
                session.Log($"[OK] User account '{username}' deleted");
            }

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
        }
    }
}
