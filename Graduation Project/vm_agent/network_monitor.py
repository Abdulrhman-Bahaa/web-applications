"""
Network Monitor for Malware Analysis
Captures network activity including DNS queries, TCP/UDP connections, and HTTP traffic
Outputs: sha256_net.json
"""

import psutil
import json
import sys
import time
import threading
import os
from datetime import datetime
from collections import defaultdict


class NetworkMonitor:
    """Monitor and capture network activity from running malware"""

    def __init__(self):
        self.events = []
        self.connections_seen = set()
        self.dns_queries = []
        self.http_traffic = []
        self.start_time = time.time()
        self.target_pid = None
        self.target_children = set()

    def get_process_tree(self, pid):
        """Get all child processes of a target PID"""
        try:
            parent = psutil.Process(pid)
            children = set([pid])
            for child in parent.children(recursive=True):
                children.add(child.pid)
            return children
        except:
            return {pid}

    def monitor_connections(self, duration, target_pid=None):
        """Monitor network connections (TCP/UDP)"""
        print("[*] Network Monitor: Tracking connections...")
        self.target_pid = target_pid
        self.target_children = self.get_process_tree(
            target_pid) if target_pid else set()

        start = time.time()
        poll_interval = 0.5  # Poll every 500ms

        while time.time() - start < duration:
            loop_start = time.time()

            try:
                # Get all connections
                for conn in psutil.net_connections(kind='inet'):
                    try:
                        # Filter by target process if specified
                        if target_pid and conn.pid not in self.target_children:
                            continue

                        # Create connection signature
                        conn_sig = (conn.laddr.ip, conn.laddr.port,
                                    conn.raddr.ip if conn.raddr else None,
                                    conn.raddr.port if conn.raddr else None,
                                    conn.type, conn.pid)

                        # Skip duplicates
                        if conn_sig in self.connections_seen:
                            continue
                        self.connections_seen.add(conn_sig)

                        # Record event
                        event = {
                            'type': 'connection',
                            'protocol': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                            'local_ip': conn.laddr.ip,
                            'local_port': conn.laddr.port,
                            'remote_ip': conn.raddr.ip if conn.raddr else None,
                            'remote_port': conn.raddr.port if conn.raddr else None,
                            'state': conn.status,
                            'pid': conn.pid,
                            'timestamp': time.time()
                        }
                        self.events.append(event)

                        # Print for visibility
                        remote = f"{event['remote_ip']}:{event['remote_port']}" if event['remote_ip'] else "N/A"
                        print(
                            f"  [+] {event['protocol']} {event['local_ip']}:{event['local_port']} -> {remote}")

                    except (AttributeError, TypeError):
                        continue
                    except Exception as e:
                        continue

            except Exception as e:
                pass

            # Maintain polling interval
            elapsed = time.time() - loop_start
            if elapsed < poll_interval:
                time.sleep(poll_interval - elapsed)

    def monitor_dns(self, duration, target_pid=None):
        """Monitor DNS queries (via connection monitoring and logs)"""
        print("[*] Network Monitor: Tracking DNS queries...")

        start = time.time()
        poll_interval = 1.0  # Poll every 1 second

        # Check Windows DNS cache or system logs for DNS activity
        while time.time() - start < duration:
            try:
                # Monitor for DNS queries through port 53 connections
                for conn in psutil.net_connections(kind='inet'):
                    try:
                        if target_pid and conn.pid not in self.target_children:
                            continue

                        # Check for DNS traffic (port 53)
                        if conn.raddr and (conn.raddr.port == 53 or conn.laddr.port == 53):
                            dns_event = {
                                'type': 'dns',
                                'query_ip': conn.raddr.ip if conn.raddr else None,
                                'pid': conn.pid,
                                'timestamp': time.time()
                            }
                            self.events.append(dns_event)
                            print(
                                f"  [+] DNS Query to: {dns_event['query_ip']}")
                    except:
                        continue

            except Exception as e:
                pass

            time.sleep(poll_interval)

    def monitor_listening_ports(self, duration):
        """Monitor listening ports that processes open"""
        print("[*] Network Monitor: Tracking listening ports...")

        start = time.time()
        listening_seen = set()

        while time.time() - start < duration:
            try:
                for conn in psutil.net_connections(kind='inet'):
                    try:
                        if conn.status == 'LISTEN':
                            listen_sig = (
                                conn.laddr.ip, conn.laddr.port, conn.pid)

                            if listen_sig not in listening_seen:
                                listening_seen.add(listen_sig)

                                # Only record if target process or children
                                if self.target_pid and conn.pid not in self.target_children:
                                    continue

                                event = {
                                    'type': 'listen',
                                    'ip': conn.laddr.ip,
                                    'port': conn.laddr.port,
                                    'protocol': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                                    'pid': conn.pid,
                                    'timestamp': time.time()
                                }
                                self.events.append(event)
                                print(
                                    f"  [+] Listening on {event['ip']}:{event['port']}")
                    except:
                        continue
            except:
                pass

            time.sleep(0.5)

    def run(self, duration, target_pid=None):
        """Run network monitoring"""
        print(f"[*] Network Monitor starting ({duration}s)...")
        self.start_time = time.time()

        # Start monitoring threads
        t1 = threading.Thread(target=self.monitor_connections, args=(
            duration, target_pid), daemon=True)
        t2 = threading.Thread(target=self.monitor_dns, args=(
            duration, target_pid), daemon=True)
        t3 = threading.Thread(
            target=self.monitor_listening_ports, args=(duration,), daemon=True)

        t1.start()
        t2.start()
        t3.start()

        # Wait for all threads
        t1.join(timeout=duration + 2)
        t2.join(timeout=duration + 2)
        t3.join(timeout=duration + 2)

        print(
            f"[+] Network monitoring complete. Captured {len(self.events)} events")
        return self.events

    def to_dict(self):
        """Convert network events to dictionary for JSON serialization"""
        return {
            'events': self.events,
            'total_connections': len([e for e in self.events if e.get('type') == 'connection']),
            'total_dns_queries': len([e for e in self.events if e.get('type') == 'dns']),
            'listening_ports': len([e for e in self.events if e.get('type') == 'listen']),
            'unique_remote_ips': len(set(
                e.get('remote_ip') for e in self.events
                if e.get('type') == 'connection' and e.get('remote_ip')
            )),
            'unique_remote_ports': len(set(
                e.get('remote_port') for e in self.events
                if e.get('type') == 'connection' and e.get('remote_port')
            )),
            'timestamp': datetime.now().isoformat()
        }


def save_network_report(monitor, output_file="sha256_net.json"):
    """Save network monitoring report to JSON file"""
    try:
        output_dir = r"C:\covid_rat" if os.name == 'nt' else os.path.expandvars(
            "$HOME/covid_rat")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, output_file)

        # Serialize and save
        report = monitor.to_dict()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print(f"[+] Network report saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"[-] Failed to save report: {e}")
        return None


def generate_text_report(monitor, output_file="analysis_report_network.txt"):
    """Generate human-readable network analysis report"""
    try:
        output_dir = r"C:\covid_rat" if os.name == 'nt' else os.path.expandvars(
            "$HOME/covid_rat")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, output_file)

        lines = []
        lines.append("=" * 80)
        lines.append(" " * 20 + "NETWORK BEHAVIORAL ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Analysis Type: Dynamic (Network Monitoring)")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("-" * 80)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append("")

        data = monitor.to_dict()
        lines.append(f"  Total Network Events:      {len(data['events'])}")
        lines.append(
            f"  Total Connections:         {data['total_connections']}")
        lines.append(
            f"  Total DNS Queries:         {data['total_dns_queries']}")
        lines.append(f"  Listening Ports:           {data['listening_ports']}")
        lines.append(
            f"  Unique Remote IPs:         {data['unique_remote_ips']}")
        lines.append(
            f"  Unique Remote Ports:       {data['unique_remote_ports']}")
        lines.append("")

        # Connections
        connections = [e for e in monitor.events if e.get(
            'type') == 'connection']
        if connections:
            lines.append("-" * 80)
            lines.append("OUTBOUND CONNECTIONS")
            lines.append("-" * 80)
            lines.append("")

            for conn in connections[:50]:  # Limit to 50 for readability
                lines.append(
                    f"  {conn['protocol']}: {conn['local_ip']}:{conn['local_port']} -> {conn['remote_ip']}:{conn['remote_port']}")
                lines.append(
                    f"        State: {conn['state']}, PID: {conn['pid']}")

            if len(connections) > 50:
                lines.append(
                    f"  ... and {len(connections) - 50} more connections")
            lines.append("")

        # DNS Queries
        dns_events = [e for e in monitor.events if e.get('type') == 'dns']
        if dns_events:
            lines.append("-" * 80)
            lines.append("DNS QUERIES")
            lines.append("-" * 80)
            lines.append("")

            unique_ips = set(e.get('query_ip') for e in dns_events)
            for ip in list(unique_ips)[:20]:
                lines.append(f"  Query to: {ip}")

            if len(unique_ips) > 20:
                lines.append(f"  ... and {len(unique_ips) - 20} more IPs")
            lines.append("")

        # Listening Ports
        listening = [e for e in monitor.events if e.get('type') == 'listen']
        if listening:
            lines.append("-" * 80)
            lines.append("LISTENING PORTS")
            lines.append("-" * 80)
            lines.append("")

            for port in listening[:20]:
                lines.append(
                    f"  {port['protocol']}: {port['ip']}:{port['port']} (PID: {port['pid']})")

            if len(listening) > 20:
                lines.append(f"  ... and {len(listening) - 20} more ports")
            lines.append("")

        # Threat Assessment
        lines.append("-" * 80)
        lines.append("THREAT ASSESSMENT")
        lines.append("-" * 80)
        lines.append("")

        threat_score = 0
        reasons = []

        if data['total_connections'] > 10:
            threat_score += 2
            reasons.append(
                f"High number of connections ({data['total_connections']})")

        if data['unique_remote_ips'] > 5:
            threat_score += 2
            reasons.append(
                f"Multiple remote IPs contacted ({data['unique_remote_ips']})")

        if data['listening_ports'] > 0:
            threat_score += 3
            reasons.append(
                f"Malware listening on {data['listening_ports']} port(s) - possible C&C or botnet")

        if data['total_dns_queries'] > 5:
            threat_score += 1
            reasons.append(
                f"Suspicious DNS query activity ({data['total_dns_queries']} queries)")

        if threat_score >= 5:
            lines.append(f"  [!] RISK LEVEL: HIGH")
        elif threat_score >= 3:
            lines.append(f"  [!] RISK LEVEL: MEDIUM")
        else:
            lines.append(f"  [+] RISK LEVEL: LOW")

        lines.append(f"  Network Threat Score: {threat_score}/10")
        lines.append("")

        if reasons:
            lines.append("  Threat Indicators:")
            for i, reason in enumerate(reasons, 1):
                lines.append(f"    {i}. {reason}")

        lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        # Write report
        report_text = '\n'.join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"[+] Text report saved: {output_path}")
        return report_text

    except Exception as e:
        print(f"[-] Failed to generate text report: {e}")
        return None


def main():
    """Main entry point for network monitor"""

    # Parse arguments: [duration] [target_pid]
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    target_pid = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print("\n" + "="*70)
    print("NETWORK BEHAVIORAL MONITOR")
    print("="*70)

    # Create and run monitor
    monitor = NetworkMonitor()
    monitor.run(duration, target_pid)

    # Save reports
    save_network_report(monitor, "sha256_net.json")
    generate_text_report(monitor, "analysis_report_network.txt")

    print("\n[+] Network monitoring complete")


if __name__ == "__main__":
    import socket
    main()
