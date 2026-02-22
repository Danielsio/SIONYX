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
        // ====================================================================

        [CustomAction]
        public static ActionResult CreateKioskUser(Session session)
        {
            session.Log("=== CreateKioskUser: START ===");

            try
            {
                // Enable blank-password logon
                session.Log("Enabling blank-password logon...");
                RunCommand("reg", @"add ""HKLM\SYSTEM\CurrentControlSet\Control\Lsa"" /v LimitBlankPasswordUse /t REG_DWORD /d 0 /f", session);

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

                    RunCommand("wmic",
                        $"useraccount where name=\"{KioskUsername}\" set PasswordExpires=false",
                        session);
                }

                // Ensure not in Administrators (ignore errors — may not be a member)
                RunCommand("net", $"localgroup Administrators \"{KioskUsername}\" /delete", session);
                // Ensure in Users group
                RunCommand("net", $"localgroup Users \"{KioskUsername}\" /add", session);

                session.Log("[OK] Kiosk user account ready");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] CreateKioskUser failed: {ex}");
                return ActionResult.Failure;
            }
        }

        [CustomAction]
        public static ActionResult ApplySecurityRestrictions(Session session)
        {
            session.Log("=== ApplySecurityRestrictions: START ===");

            try
            {
                SetRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                    "NoRun", 1);

                SetRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    "DisableRegistryTools", 1);

                SetRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    "DisableCMD", 2);

                SetRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    "DisableTaskMgr", 1);

                session.Log("[OK] Security restrictions applied");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] ApplySecurityRestrictions failed: {ex}");
                return ActionResult.Failure;
            }
        }

        [CustomAction]
        public static ActionResult SetupAutoStart(Session session)
        {
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

                session.Log("[OK] Scheduled task created");
                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] SetupAutoStart failed: {ex}");
                return ActionResult.Failure;
            }
        }

        [CustomAction]
        public static ActionResult InitializeProfile(Session session)
        {
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
                session.Log("[OK] Startup shortcut created");

                return ActionResult.Success;
            }
            catch (Exception ex)
            {
                session.Log($"[ERROR] InitializeProfile failed: {ex}");
                return ActionResult.Failure;
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
                RemoveRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoRun");
                RemoveRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools");
                RemoveRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableCMD");
                RemoveRegistryPolicy(session,
                    @"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr");

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

        private static int RunCommand(string fileName, string arguments, Session session)
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var process = Process.Start(psi))
            {
                string stdout = process.StandardOutput.ReadToEnd();
                string stderr = process.StandardError.ReadToEnd();
                process.WaitForExit();

                if (!string.IsNullOrWhiteSpace(stdout))
                    session.Log(stdout.TrimEnd());
                if (!string.IsNullOrWhiteSpace(stderr) && process.ExitCode != 0)
                    session.Log($"STDERR: {stderr.TrimEnd()}");

                return process.ExitCode;
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
