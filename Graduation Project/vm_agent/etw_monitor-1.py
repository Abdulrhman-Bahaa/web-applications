import json, sys, time, threading, os, psutil, hashlib
from collections import deque, defaultdict

class ETWMonitor:
    def __init__(self):
        self.events = deque(maxlen=10000)
        self.seen_pids = set()
        self.seen_files = set()
        self.start = time.time()
        self.baseline_procs = set()
        self.baseline_files = set()
        self._capture_baseline()
        
    def _capture_baseline(self):
        """Capture system baseline - anything deviating is suspicious"""
        print("[*] Capturing baseline...")
        for proc in psutil.process_iter(['pid', 'name']):
            try: self.baseline_procs.add(proc.info['name'].lower())
            except: pass
        for root in [os.path.expandvars(p) for p in ["%SystemRoot%", "%ProgramFiles%"]]:
            try:
                for r, _, files in os.walk(root):
                    for f in files: self.baseline_files.add(f.lower())
            except: pass
        print(f"    Baseline: {len(self.baseline_procs)} procs, {len(self.baseline_files)} files")
    
    def _score_anomaly(self, name, cmd, path):
        """Generic anomaly scoring - no malware-specific rules"""
        score = 0
        name_l = (name or '').lower()
        cmd_l = (cmd or '').lower()
        path_l = (path or '').lower()
        
        # 1. New process not in baseline
        if name_l and name_l not in self.baseline_procs:
            score += 2
        
        # 2. Command line entropy (randomness = obfuscation)
        if cmd and len(cmd) > 20:
            entropy = len(set(cmd)) / len(cmd)
            if entropy > 0.8: score += 3  # High randomness
            if entropy < 0.3: score += 1  # Low variety (possible padding)
        
        # 3. Path anomaly
        if path_l:
            # Deep paths (hiding)
            if path_l.count('\\') > 6: score += 2
            # Temp/AppData execution
            if any(x in path_l for x in ['\\temp\\', '\\appdata\\', '\\local\\']): score += 2
            # System directory write
            if path_l.startswith('c:\\windows') and not path_l.startswith('c:\\windows\\temp'): score += 3
        
        # 4. Command patterns (generic)
        if cmd:
            # Redirection/piping
            if '|' in cmd or '>' in cmd: score += 1
            # Network indicators
            if any(x in cmd_l for x in ['http', 'tcp', 'download', 'upload', 'connect']): score += 2
            # Encoding patterns (generic)
            if any(x in cmd for x in [' -e', ' /e', ' -enc', ' /enc']): score += 2
        
        # 5. Parent-child anomaly (checked later)
        
        return score
    
    def _monitor_proc(self, duration, target_pid):
        print("[*] Monitoring processes...")
        try:
            import win32com.client
            wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            svc = wmi.ConnectServer(".", r"root\cimv2")
            events = svc.ExecNotificationQuery(
                "SELECT * FROM __InstanceCreationEvent WITHIN 0.01 WHERE TargetInstance ISA 'Win32_Process'"
            )
            
            while time.time() - self.start < duration:
                try:
                    e = events.NextEvent(100)
                    p = e.TargetInstance
                    pid, name, ppid = p.ProcessId, p.Name, p.ParentProcessId
                    
                    if pid in self.seen_pids: continue
                    self.seen_pids.add(pid)
                    
                    cmd = p.CommandLine or ''
                    exe_path = p.ExecutablePath or ''
                    
                    # Calculate anomaly score
                    score = self._score_anomaly(name, cmd, exe_path)
                    
                    # Check parent relationship
                    parent_name = ""
                    try:
                        parent = psutil.Process(ppid)
                        parent_name = parent.name()
                        # Child of unusual parent
                        if parent_name.lower() not in ['explorer.exe', 'services.exe', 'svchost.exe']:
                            score += 1
                    except: pass
                    
                    is_target = target_pid and (pid == target_pid or ppid == target_pid)
                    
                    if score >= 3 or is_target:
                        self.events.append({
                            'type': 'process', 'time': time.time(), 'pid': pid, 'ppid': ppid,
                            'name': name, 'cmd': cmd[:200], 'path': exe_path, 'score': score,
                            'target': is_target, 'parent': parent_name
                        })
                        marker = " [!]" if score >= 6 else ""
                        print(f"  [{score}]{marker} {name} (parent: {parent_name})")
                        
                except: pass
        except Exception as e:
            print(f"[!] WMI: {e}")
            self._poll_proc(duration, target_pid)
    
    def _poll_proc(self, duration, target_pid):
        while time.time() - self.start < duration:
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'exe', 'create_time']):
                try:
                    info = proc.info
                    pid = info['pid']
                    if pid in self.seen_pids or info['create_time'] < self.start: continue
                    self.seen_pids.add(pid)
                    
                    name, cmd = info['name'] or '', ' '.join(info['cmdline'] or [])
                    exe_path = info['exe'] or ''
                    score = self._score_anomaly(name, cmd, exe_path)
                    
                    if score >= 3 or (target_pid and (pid == target_pid or info['ppid'] == target_pid)):
                        self.events.append({
                            'type': 'process', 'time': time.time(), 'pid': pid, 'ppid': info['ppid'],
                            'name': name, 'cmd': cmd[:200], 'path': exe_path, 'score': score, 'target': True
                        })
                        print(f"  [POLL][{score}] {name}")
                except: pass
            time.sleep(0.05)
    
    def _monitor_file(self, duration):
        print("[*] Monitoring files...")
        watch = [os.path.expandvars(p) for p in ["%TEMP%", "%APPDATA%", "%LOCALAPPDATA%"]] + \
                [r"C:\Windows\Temp", r"C:\ProgramData"]
        watch = [p for p in watch if os.path.exists(p)]
        
        # Baseline snapshot
        snaps = {}
        for p in watch:
            try: snaps[p] = {os.path.join(r, f) for r, _, files in os.walk(p) for f in files}
            except: snaps[p] = set()
        
        while time.time() - self.start < duration:
            for p in watch:
                try:
                    curr = {os.path.join(r, f) for r, _, files in os.walk(p) for f in files}
                    new = curr - snaps[p]
                    
                    for fpath in new:
                        if fpath in self.seen_files: continue
                        self.seen_files.add(fpath)
                        
                        fname = os.path.basename(fpath).lower()
                        fpath_l = fpath.lower()
                        
                        # Generic file anomaly scoring
                        score = 0
                        # New file in temp locations
                        if fname not in self.baseline_files: score += 2
                        # Executable dropped
                        if fname.endswith(('.exe', '.dll', '.sys')): score += 3
                        # Script dropped
                        if fname.endswith(('.ps1', '.vbs', '.js', '.bat', '.cmd')): score += 2
                        # Hidden in deep path
                        if fpath_l.count('\\') > 5: score += 2
                        # System directory abuse
                        if 'windows' in fpath_l and 'temp' not in fpath_l: score += 4
                        
                        if score >= 3:
                            self.events.append({
                                'type': 'file', 'time': time.time(), 'path': fpath,
                                'file': fname, 'score': score
                            })
                            print(f"  [FILE][{score}] {fname}")
                    
                    snaps[p] = curr
                except: pass
            time.sleep(0.2)
    
    def run(self, duration, target_pid=None):
        print(f"[*] ETW Monitor ({duration}s)")
        
        t1 = threading.Thread(target=self._monitor_proc, args=(duration, target_pid))
        t2 = threading.Thread(target=self._monitor_file, args=(duration,))
        t1.start(); t2.start(); t1.join(); t2.join()
        
        # Calculate final score
        proc_events = [e for e in self.events if e['type'] == 'process']
        file_events = [e for e in self.events if e['type'] == 'file']
        
        total_score = sum(e['score'] for e in self.events)
        max_score = min(100, total_score * 2)
        
        # Behavioral clusters (generic)
        behaviors = []
        high_scores = [e for e in self.events if e['score'] >= 6]
        if len(high_scores) >= 2: behaviors.append("suspicious_chain")
        if any('windows' in e.get('path', '').lower() for e in file_events): behaviors.append("system_abuse")
        
        report = {
            'ok': True, 'duration': duration, 'score': max_score,
            'total_events': len(self.events), 'behaviors': behaviors,
            'processes': len(proc_events), 'files': len(file_events),
            'high_anomalies': len(high_scores),
            'events': list(self.events)
        }
        
        with open('etw_report.json', 'w') as f: json.dump(report, f, indent=2, default=str)
        
        print(f"\n[+] Score: {max_score}/100")
        print(f"    Events: {len(self.events)} | High anomalies: {len(high_scores)}")
        print(f"    Behaviors: {', '.join(behaviors) if behaviors else 'None detected'}")
        return report

if __name__ == "__main__":
    ETWMonitor().run(
        int(sys.argv[1]) if len(sys.argv) > 1 else 12,
        int(sys.argv[2]) if len(sys.argv) > 2 else None
    )