import json, os, hashlib, winreg, ctypes, psutil, time

ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x0004 | 0x8000)

def get_registry():
    registry = {}

    keys = [
        # ===== Startup / Run Keys =====
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),

        # ===== Startup Approved =====
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),

        # ===== Winlogon Persistence =====
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),

        # ===== Services =====
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services"),

        # ===== Image File Execution Options (Debugger Hijack) =====
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"),

        # ===== Scheduled Tasks =====
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tasks"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree"),

        # ===== Firewall Rules =====
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"),

        # ===== Windows Defender Policies =====
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender"),

        # ===== Known DLL Hijacking =====
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs"),

        # ===== LSA (Credential Theft) =====
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Lsa"),
    ]

    for hkey, path in keys:
        try:
            with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        hive = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                        full = f"{hive}\\{path}\\{name}"
                        registry[full] = str(value)
                        i += 1
                    except OSError:
                        break
        except:
            continue

    return registry


def get_files():
    files = {}

    paths = [
        # ===== User Folders =====
        "%APPDATA%",
        "%LOCALAPPDATA%",
        "%TEMP%",
        "%USERPROFILE%\\Desktop",
        "%USERPROFILE%\\Downloads",

        # ===== Startup Folders =====
        "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
        "%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",

        # ===== ProgramData =====
        "%PROGRAMDATA%",

        # ===== Public Folder =====
        "C:\\Users\\Public",

        # ===== Scheduled Tasks (File-Level) =====
        "C:\\Windows\\System32\\Tasks",

        # ===== Drivers =====
        "C:\\Windows\\System32\\drivers",

        # ===== Prefetch =====
        "C:\\Windows\\Prefetch",

        # ===== Group Policy Scripts =====
        "C:\\Windows\\System32\\GroupPolicy\\Machine\\Scripts",
        "C:\\Windows\\System32\\GroupPolicy\\User\\Scripts",
    ]

    # Expand environment variables
    expanded_paths = [os.path.expandvars(p) for p in paths]

    for path in expanded_paths:
        if not os.path.exists(path):
            continue

        try:
            # Use shallow scan for heavy system directories
            if "System32" in path or "ProgramData" in path:
                items = os.listdir(path)
                for item in items:
                    full = os.path.join(path, item)
                    try:
                        if os.path.isfile(full):
                            with open(full, 'rb') as f:
                                h = hashlib.md5(f.read(4096)).hexdigest()
                            files[full] = {
                                'size': os.path.getsize(full),
                                'hash': h,
                                'mtime': os.path.getmtime(full)
                            }
                        else:
                            files[full] = {'size': 0, 'hash': 'folder'}
                    except:
                        files[full] = {'size': 0, 'hash': 'error'}
            else:
                # Recursive scan for user-level directories
                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        full = os.path.join(root, f)
                        try:
                            with open(full, 'rb') as file_obj:
                                h = hashlib.md5(file_obj.read(4096)).hexdigest()
                            files[full] = {
                                'size': os.path.getsize(full),
                                'hash': h,
                                'mtime': os.path.getmtime(full)
                            }
                        except:
                            files[full] = {'size': 0, 'hash': 'error'}
        except:
            continue

    return files


def get_processes():
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'ppid']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'], 'name': info['name'], 'exe': info['exe'] or "",
                    'command_line': " ".join(info['cmdline']) if info['cmdline'] else "",
                    'ppid': info['ppid']
                })
            except: pass
    except: pass
    return processes

def main():
    print("[*] Taking snapshot...")
    snapshot = {
        'timestamp': time.time(),
        'registry': get_registry(),
        'files': get_files(),
        'processes': get_processes()
    }
    with open('snapshot.json', 'w') as f:
        json.dump(snapshot, f, indent=2)
    print(f"[+] Done: {len(snapshot['registry'])} reg, {len(snapshot['files'])} files, {len(snapshot['processes'])} procs")

if __name__ == "__main__":
    main()