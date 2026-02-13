import subprocess
import time
import os
import glob
import json
import sys


def cleanup():
    for f in ["snapshot_before.json", "snapshot_after.json", "etw_report.json", "Sha256_dynamic.json", "sha256_net.json"]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except:
            pass


def take_snapshot(name):
    try:
        subprocess.run([sys.executable, "snapshot.py"],
                       check=True, capture_output=True)
        if os.path.exists("snapshot.json"):
            os.rename("snapshot.json", name)
            print(f"[+] Snapshot: {name}")
            return True
    except Exception as e:
        print(f"[-] Snapshot failed: {e}")
        return False


def run_analysis(malware_path, duration=12):
    print("=" * 70)
    print("MALWARE ANALYSIS SYSTEM (Snapshot + ETW)")
    print("=" * 70)

    if not os.path.exists(malware_path):
        print(f"[-] ERROR: File not found: {malware_path}")
        return False

    cleanup()

    # Step 1: Before snapshot
    print("\n[*] STEP 1: BEFORE snapshot...")
    if not take_snapshot("snapshot_before.json"):
        return False

    with open("snapshot_before.json") as f:
        before = json.load(f)
    print(f"    Processes: {len(before.get('processes', []))}")

    # Step 2: Run malware with ETW and Network Monitoring
    print(
        f"\n[*] STEP 2: Running malware with ETW and Network Monitoring ({duration}s)...")

    try:
        malware_proc = subprocess.Popen(
            [malware_path],
            cwd=os.path.dirname(malware_path) or ".",
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        print(f"    Malware PID: {malware_proc.pid}")

        # Start ETW monitor
        etw_proc = subprocess.Popen(
            [sys.executable, "etw_monitor.py", str(
                duration), str(malware_proc.pid)]
        )

        # Start Network monitor
        net_proc = subprocess.Popen(
            [sys.executable, "network_monitor.py",
                str(duration), str(malware_proc.pid)]
        )

        # Wait for malware
        try:
            malware_proc.wait(timeout=duration + 5)
        except subprocess.TimeoutExpired:
            malware_proc.terminate()

        # Wait for ETW and Network monitoring to finish
        etw_proc.wait()
        net_proc.wait()

    except Exception as e:
        print(f"[-] Error: {e}")
        return False

    # Step 3: After snapshot
    print("\n[*] STEP 3: AFTER snapshot...")
    time.sleep(1)
    if not take_snapshot("snapshot_after.json"):
        return False

    with open("snapshot_after.json") as f:
        after = json.load(f)
    print(f"    Processes: {len(after.get('processes', []))}")

    # Step 4: Analyze (with ETW, Network, and Snapshot data)
    print("\n[*] STEP 4: Analyzing (ETW, Network, and Snapshots)...")
    cmd = [sys.executable, "analyzer.py",
           "--before", "snapshot_before.json",
           "--after", "snapshot_after.json",
           "--rules", "1.yaml"]

    if os.path.exists("etw_report.json"):
        cmd.extend(["--etw", "etw_report.json"])

    if os.path.exists("sha256_net.json"):
        cmd.extend(["--network", "sha256_net.json"])

    try:
        subprocess.run(cmd, check=True)
        print("\n[+] Analysis complete!")
        print("[+] Generated reports:")
        print("    - Snapshot Analysis: snapshot_before.json, snapshot_after.json")
        print("    - ETW Behavioral: Sha256_dynamic.json, analysis_report_dynamic.txt")
        print("    - Network Analysis: sha256_net.json, analysis_report_network.txt")
        print("    - Static Analysis: Sha256_static.json, analysis_report_static.txt")
        return True
    except Exception as e:
        print(f"[-] Analysis failed: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        malware_path = sys.argv[1]
    else:
        for pattern in [r"C:\covid_rat\uploads\*.exe", r".\uploads\*.exe", r".\*.exe"]:
            files = glob.glob(pattern)
            if files:
                malware_path = files[0]
                break
        else:
            print("[-] No .exe found. Usage: python main.py <path>")
            return

    malware_path = os.path.abspath(malware_path)
    print(f"[+] Target: {malware_path}")

    try:
        run_analysis(malware_path)
    except KeyboardInterrupt:
        print("\n[*] Interrupted")
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()

    # Auto-exit after 2 seconds instead of waiting for Enter
    print("\n[*] Auto-exiting in 2 seconds...")
    time.sleep(2)


if __name__ == "__main__":
    main()
