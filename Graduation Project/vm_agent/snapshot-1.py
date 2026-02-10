import json, os, hashlib, winreg, psutil, time

def get_registry():
    registry = {}
    keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services"),
    ]
    for hkey, path in keys:
        try:
            with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        full = f"{'HKCU' if hkey == winreg.HKEY_CURRENT_USER else 'HKLM'}\\{path}\\{name}"
                        registry[full] = str(value)
                        i += 1
                    except WindowsError:
                        break
        except: pass
    return registry

def get_files():
    files = {}
    paths = [os.path.expandvars(p) for p in ["%APPDATA%", "%LOCALAPPDATA%", "%TEMP%"]] + [
        r"C:\Windows\Temp", r"C:\Windows\Tasks", r"C:\Windows\Sub", 
        r"C:\ProgramData", r"C:\Windows\System32\Tasks"
    ]
    for path in paths:
        if not os.path.exists(path):
            try: os.makedirs(path, exist_ok=True)
            except: continue
        try:
            for root, dirs, filenames in os.walk(path):
                if root.count(os.sep) - path.count(os.sep) > 2: continue
                for item in filenames + dirs:
                    full = os.path.join(root, item)
                    try:
                        if os.path.isfile(full):
                            with open(full, 'rb') as f: h = hashlib.md5(f.read(4096)).hexdigest()
                            files[full] = {'size': os.path.getsize(full), 'hash': h, 'mtime': os.path.getmtime(full)}
                        else:
                            files[full] = {'type': 'folder'}
                    except: files[full] = {'type': 'error'}
        except: pass
    return files

def get_processes():
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'ppid']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'], 'name': info['name'], 
                    'exe': info['exe'] or "",
                    'command_line': " ".join(info['cmdline']).lower() if info['cmdline'] else "",
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