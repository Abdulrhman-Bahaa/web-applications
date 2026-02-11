import subprocess
import json
import sys
import time
import threading
import os
import psutil

class ETWMonitor:
    def __init__(self):
        self.events = []
        self.seen_pids = set()
        self.start_time = time.time()
        
    def monitor_processes(self, duration, target_pid=None):
        """High-speed process monitoring - captures ALL processes"""
        print("[*] ETW monitoring processes...")
        
        # Track all PIDs from target tree
        target_pids = {target_pid} if target_pid else set()
        
        start = time.time()
        poll_interval = 0.05  # 50ms
        
        while time.time() - start < duration:
            loop_start = time.time()
            
            try:
                # Update target PIDs (find children)
                if target_pid:
                    try:
                        parent = psutil.Process(target_pid)
                        for child in parent.children(recursive=True):
                            target_pids.add(child.pid)
                    except:
                        pass
                
                # Get all processes quickly
                for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'create_time']):
                    try:
                        pid = proc.info['pid']
                        
                        if pid in self.seen_pids:
                            continue
                        self.seen_pids.add(pid)
                        
                        # Only new processes (created after monitoring started)
                        if proc.info['create_time'] < self.start_time:
                            continue
                        
                        ppid = proc.info['ppid']
                        name = proc.info['name'] or ''
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        
                        # Check if related to target
                        is_related = (target_pid and (pid == target_pid or ppid in target_pids or pid in target_pids))
                        
                        # Skip conhost unless related
                        if name.lower() == 'conhost.exe' and not is_related:
                            continue
                        
                        # Record event (detection happens in analyzer via YAML)
                        event = {
                            'type': 'process',
                            'name': name,
                            'pid': pid,
                            'ppid': ppid,
                            'command': cmdline,
                            'is_related': is_related,
                            'timestamp': time.time()
                        }
                        self.events.append(event)
                        
                        # Print for visibility
                        rel_marker = " [RELATED]" if is_related else ""
                        print(f"  [+] Process: {name}{rel_marker}")
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            except Exception as e:
                pass
            
            # Maintain polling interval
            elapsed = time.time() - loop_start
            if elapsed < poll_interval:
                time.sleep(poll_interval - elapsed)
    
    def monitor_files(self, duration, target_pid=None):
        """Monitor file system changes"""
        print("[*] ETW monitoring file system...")
        
        watch_dirs = [
            os.path.expandvars("%TEMP%"),
            os.path.expandvars("%APPDATA%"),
            os.path.expandvars("%LOCALAPPDATA%")
        ]
        
        # Initial state
        initial = set()
        for d in watch_dirs:
            if os.path.exists(d):
                try:
                    for root, _, files in os.walk(d):
                        for f in files:
                            initial.add(os.path.join(root, f).lower())
                except: pass
        
        start = time.time()
        while time.time() - start < duration:
            for d in watch_dirs:
                if not os.path.exists(d):
                    continue
                try:
                    for root, _, files in os.walk(d):
                        for f in files:
                            full = os.path.join(root, f)
                            lower = full.lower()
                            
                            if lower in initial:
                                continue
                            initial.add(lower)
                            
                            # Record event (detection in analyzer)
                            event = {
                                'type': 'file',
                                'path': full,
                                'filename': f,
                                'timestamp': time.time()
                            }
                            self.events.append(event)
                            print(f"  [+] File: {f}")
                            
                except: pass
            time.sleep(0.5)
    
    def run(self, duration, target_pid=None):
        """Run ETW monitoring"""
        print(f"[*] ETW Monitor starting ({duration}s)...")
        self.start_time = time.time()
        
        # Start threads
        t1 = threading.Thread(target=self.monitor_processes, args=(duration, target_pid))
        t2 = threading.Thread(target=self.monitor_files, args=(duration, target_pid))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Build report (raw events, no detection logic)
        report = {
            'success': True,
            'duration': duration,
            'total_events': len(self.events),
            'events': self.events,
            'processes': [e for e in self.events if e['type'] == 'process'],
            'files': [e for e in self.events if e['type'] == 'file']
        }
        
        with open('etw_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[+] ETW complete: {len(self.events)} events")
        return report

def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    target_pid = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    monitor = ETWMonitor()
    monitor.run(duration, target_pid)

if __name__ == "__main__":
    main()