# Network Monitor Integration Guide

## Overview

The `network_monitor.py` module provides real-time network behavioral monitoring for malware analysis. It captures and analyzes network activity including TCP/UDP connections, DNS queries, and listening ports during malware execution.

## Features

- **TCP/UDP Connection Monitoring**: Captures all outbound and inbound connections from the target process
- **DNS Query Tracking**: Monitors DNS resolution attempts
- **Listening Port Detection**: Identifies ports opened by the malware (potential C&C indicators)
- **Process-Specific Filtering**: Isolates network activity from the target malware and its child processes
- **Real-time Reporting**: Generates both JSON and human-readable text reports

## Output Files

### Primary Output: `sha256_net.json`
Location: `C:\covid_rat\` (Windows) or `$HOME/covid_rat/` (Linux)

```json
{
  "events": [
    {
      "type": "connection",
      "protocol": "TCP",
      "local_ip": "192.168.1.100",
      "local_port": 54321,
      "remote_ip": "203.0.113.45",
      "remote_port": 80,
      "state": "ESTABLISHED",
      "pid": 4521,
      "timestamp": 1234567890.123
    }
  ],
  "total_connections": 15,
  "total_dns_queries": 8,
  "listening_ports": 2,
  "unique_remote_ips": 5,
  "unique_remote_ports": 7,
  "timestamp": "2026-02-13T10:30:45.123456"
}
```

### Secondary Output: `analysis_report_network.txt`
Human-readable text report with:
- Summary statistics
- Outbound connections list
- DNS queries
- Listening ports
- Threat assessment with risk scoring

## Integration with VM Agent Pipeline

### 1. Automatic Integration in `main.py`

The network monitor is automatically executed alongside ETW monitoring:

```python
# Main.py automatically runs:
# Step 2: Concurrent execution of:
#   - Snapshot monitoring
#   - ETW behavioral analysis
#   - Network monitoring (NEW)
# Step 4: Analysis aggregates all three data sources
```

### 2. Usage from Command Line

```bash
# Run network monitor for 15 seconds targeting process PID 4521
python network_monitor.py 15 4521

# Run for 10 seconds (will monitor all processes)
python network_monitor.py 10
```

### Arguments
- `duration` (int): Monitoring duration in seconds
- `target_pid` (int, optional): PID of malware process to focus on

## Integration with Host Agent

### Data Flow

```
Malware Execution
    ↓
Host Agent
    ├→ VM Agent (via SSH/RDP)
    │   ├→ snapshot.py (before)
    │   ├→ malware.exe (execution)
    │   ├→ etw_monitor.py (behavioral)
    │   ├→ network_monitor.py (network) ← NEW
    │   └→ snapshot.py (after)
    ↓
analyzer.py
    ├→ Snapshot diff analysis
    ├→ ETW event correlation
    └→ Network activity analysis ← NEW
    ↓
Results Database
    ├→ Sha256_dynamic.json
    ├→ Sha256_net.json ← NEW
    └→ Sha256_static.json
    ↓
Web Application
    └→ Display comprehensive malware analysis report
```

### Host Agent Communication

1. **Host Agent Request**: "Analyze malware SHA256"
2. **VM Agent Execution**:
   - Downloads malware from Data Access Service
   - Executes analysis pipeline (snapshot → execute → monitor → snapshot)
   - Network monitor captures all network activity
3. **Results Upload**:
   - Network report (`sha256_net.json`) sent to Data Access Service
   - File stored: `/uploads/[sha256]_net.json`
4. **Web App Retrieval**:
   - Queries Data Access Service for network analysis
   - Displays network graph and threat indicators

## Integration with Analyzer

The analyzer now accepts `--network` parameter:

```bash
python analyzer.py \
  --before snapshot_before.json \
  --after snapshot_after.json \
  --rules 1.yaml \
  --etw etw_report.json \
  --network sha256_net.json
```

### Analysis Scoring Integration

Network findings contribute to the malware threat score:

```python
threat_score += 2  # High connection count (>10)
threat_score += 2  # Multiple remote IPs (>5)
threat_score += 3  # Listening ports (C&C indicator)
threat_score += 1  # Suspicious DNS activity (>5 queries)
```

**Risk Levels**:
- 0-2: LOW
- 3-4: MEDIUM
- 5+: HIGH

## Threat Indicators

### High-Risk Indicators

1. **Listening Ports**: Malware opening listening ports suggests C&C server or P2P capability
2. **Multiple Remote IPs**: Contacting many IPs indicates potential botnet or data exfiltration
3. **DNS Flooding**: Excessive DNS queries may indicate DGA (Domain Generation Algorithm)
4. **Unusual Protocols**: Mix of TCP and UDP to same destinations

### Medium-Risk Indicators

1. **Outbound Connections**: Standard connections to known C&C or malicious IPs
2. **DNS Resolution**: Domain lookups (especially if combined with HTTP traffic)
3. **Port Scanning**: Multiple ports on same host

### Data Collection Points

The network monitor tracks:

```
├── TCP Connections
│   ├── Established
│   ├── Listening
│   └── Time-wait (cleanup indicators)
├── UDP Connections
│   └── All UDP traffic
├── DNS Queries (via port 53 monitoring)
├── Process Association
│   ├── Direct connections from malware
│   ├── Child process connections
│   └── Network pattern analysis
└── Timing Information
    └── Event timestamps for correlation
```

## Files Modified

1. **`network_monitor.py`** (NEW)
   - Core network monitoring module
   - Real-time connection tracking
   - DNS query detection
   - Report generation

2. **`main.py`** (UPDATED)
   - Added `net_proc` subprocess
   - Integrated network monitoring execution
   - Added `sha256_net.json` to cleanup

3. **`analyzer.py`** (UPDATED)
   - Added `--network` argument
   - Network data integration into results
   - Enhanced threat scoring

## Usage Examples

### Example 1: Basic Network Analysis

```python
from network_monitor import NetworkMonitor, save_network_report

# Create monitor
monitor = NetworkMonitor()

# Run monitoring for 20 seconds on target PID 1234
monitor.run(duration=20, target_pid=1234)

# Save report
save_network_report(monitor, "sha256_net.json")
```

### Example 2: Integration with Main Pipeline

```bash
# Standard execution - network monitoring included automatically
python main.py "C:\covid_rat\uploads\malware.exe"

# View generated reports
cat Sha256_net.json       # Machine-readable
cat analysis_report_network.txt  # Human-readable
```

### Example 3: Standalone Monitoring

```bash
# Monitor all network activity for 30 seconds
python network_monitor.py 30

# Monitor specific process for 15 seconds
python network_monitor.py 15 2841
```

## Performance Considerations

- **Polling Interval**: 500ms for connection monitoring (configurable)
- **Memory**: Minimal - events stored in memory during monitoring
- **CPU**: Low overhead (psutil is optimized)
- **Concurrent Execution**: Runs in parallel with ETW and snapshot monitors

## Future Enhancements

1. **YARA Rules Integration**: Correlate network IPs/domains with YARA threat intelligence
2. **Geolocation**: Map remote IPs to geographic locations
3. **Whois Lookup**: Identify ASN and domain ownership
4. **SSL/TLS Certificate Extraction**: Monitor HTTPS connections
5. **Packet Capture**: Integrate with scapy for deep packet inspection
6. **Botnet Signature Detection**: Identify known botnet C&C patterns
7. **Traffic Encryption Detection**: Flag suspicious encrypted tunnels

## Troubleshooting

### Issue: "No module named 'psutil'"
```bash
pip install psutil
```

### Issue: Permission Denied on network monitoring
- Windows: Ensure running as Administrator
- Linux: May need elevated privileges for raw socket access

### Issue: Network report not generated
- Check output directory exists: `C:\covid_rat\` or `$HOME/covid_rat/`
- Verify write permissions
- Check disk space

### Issue: Missing network events
- Verify process PID is correct
- Check if firewall is blocking monitoring
- Increase monitoring duration

## Testing

To test the network monitor:

```bash
# Terminal 1: Run network monitor
python network_monitor.py 30

# Terminal 2: Generate network traffic
python -c "import socket; s = socket.socket(); s.connect(('8.8.8.8', 53))"

# Check reports
cat sha256_net.json
cat analysis_report_network.txt
```

## References

- [psutil Documentation](https://psutil.readthedocs.io/)
- [Socket Programming Guide](https://docs.python.org/3/library/socket.html)
- [Network Monitoring Best Practices](https://owasp.org/www-community/attacks/Network_Eavesdropping)

---

**Version**: 1.0
**Last Updated**: February 13, 2026
**Status**: Production Ready
