import json, yaml, re, argparse, os
from datetime import datetime

class MalwareAnalyzer:
    def __init__(self, rules_path):
        with open(rules_path, 'r') as f:
            self.rules = yaml.safe_load(f)
        self.etw_events = []
        
    def load_etw(self, path):
        if not os.path.exists(path): return False
        with open(path) as f:
            data = json.load(f)
        self.etw_events = data.get('events', [])
        print(f"[+] Loaded {len(self.etw_events)} ETW events")
        return True

    def match(self, value, pattern):
        if not value: return False
        value, pattern = str(value).replace('\\', '/'), pattern.replace('\\', '/')
        if ' OR ' in pattern:
            return any(self.match(value, p.strip()) for p in pattern.split(' OR '))
        pattern = pattern.replace('*', '.*').replace('?', '.')
        try: return re.search(pattern, value, re.IGNORECASE) is not None
        except: return pattern.replace('.*', '').lower() in value.lower()

    def analyze_etw(self):
        findings = []
        score = 0
        for event in self.etw_events:
            event_type = event.get('type')
            for rule in self.rules.get('detection_rules', []):
                if rule.get('weight', 0) <= 0:
                    continue
                if event_type == 'process' and rule['field'] == 'process':
                    value = f"{event.get('name', '')}|{event.get('command', '')}"
                    if self.match(value, rule['pattern']):
                        findings.append({
                            'name': rule['name'],
                            'weight': rule['weight'],
                            'type': 'ETW',
                            'details': event
                        })
                        score += rule['weight']
                        print(f"\n[!] {rule['name']} (+{rule['weight']}) [ETW]")
                        print(f"    Process: {event.get('name')}")
                        if event.get('command'):
                            print(f"    CMD: {event.get('command')[:80]}")
                        break
                elif event_type == 'file' and rule['field'] == 'file':
                    value = event.get('path', '')
                    if self.match(value, rule['pattern']):
                        findings.append({
                            'name': rule['name'],
                            'weight': rule['weight'],
                            'type': 'ETW',
                            'details': event
                        })
                        score += rule['weight']
                        print(f"\n[!] {rule['name']} (+{rule['weight']}) [ETW]")
                        print(f"    File: {event.get('filename')}")
                        break
        return findings, score

    def compare(self, before, after):
        findings, score = [], 0
        matched = {'reg': set(), 'file': set(), 'proc': set()}
        
        b_reg, a_reg = set(before.get('registry', {})), set(after.get('registry', {}))
        for key in (a_reg - b_reg):
            if key in matched['reg']: continue
            for r in self.rules.get('detection_rules', []):
                if r.get('weight', 0) <= 0: continue
                if r['field'] == 'registry' and r['action'] == 'create' and self.match(key, r['pattern']):
                    findings.append((r['name'], r['weight'], 'REG', key))
                    score += r['weight']
                    matched['reg'].add(key)
                    break
        
        b_file, a_file = set(before.get('files', {})), set(after.get('files', {}))
        for f in (a_file - b_file):
            if f in matched['file']: continue
            for r in self.rules.get('detection_rules', []):
                if r.get('weight', 0) <= 0: continue
                if r['field'] == 'file' and r['action'] == 'create' and self.match(f, r['pattern']):
                    findings.append((r['name'], r['weight'], 'FILE', f))
                    score += r['weight']
                    matched['file'].add(f)
                    break
        
        b_procs = {f"{p['name']}|{p.get('command_line', '')}" for p in before.get('processes', [])}
        for p in after.get('processes', []):
            sig = f"{p['name']}|{p.get('command_line', '')}"
            if sig in b_procs or sig in matched['proc']: continue
            for r in self.rules.get('detection_rules', []):
                if r.get('weight', 0) <= 0: continue
                if r['field'] == 'process' and r['action'] == 'create' and self.match(sig, r['pattern']):
                    findings.append((r['name'], r['weight'], 'PROC', p['name']))
                    score += r['weight']
                    matched['proc'].add(sig)
                    break
        
        return findings, score

    def generate_text_report(self, results, before, after, output_file="analysis_report.txt"):
        """Generate a well-formatted text report"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append(" " * 25 + "MALWARE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Analysis Type: Dynamic (Snapshot + ETW)")
        lines.append("=" * 80)
        lines.append("")
        
        # Executive Summary
        lines.append("-" * 80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append("")
        
        risk = results['risk_level']
        risk_banner = {
            'CRITICAL': '!!! CRITICAL THREAT DETECTED !!!',
            'HIGH': '!! HIGH RISK DETECTED !!',
            'MEDIUM': '! MEDIUM RISK DETECTED !',
            'LOW': 'LOW RISK DETECTED',
            'CLEAN': 'NO THREATS DETECTED'
        }.get(risk, 'UNKNOWN')
        
        lines.append(f"  Overall Risk Level: {risk}")
        lines.append(f"  {risk_banner}")
        lines.append("")
        lines.append(f"  State Change Score:  {results['state_score']:>3}/100")
        lines.append(f"  ETW Behavior Score:  {results['etw_score']:>3}/100")
        lines.append(f"  Combined Score:      {results['combined_score']:>3}/100")
        lines.append("")
        
        # System State Changes
        lines.append("-" * 80)
        lines.append("PHASE 1: SYSTEM STATE CHANGES")
        lines.append("-" * 80)
        lines.append("")
        
        if results['state_findings']:
            lines.append(f"  Total Detections: {len(results['state_findings'])}")
            lines.append("")
            
            # Group by type
            reg_findings = [f for f in results['state_findings'] if f[2] == 'REG']
            file_findings = [f for f in results['state_findings'] if f[2] == 'FILE']
            proc_findings = [f for f in results['state_findings'] if f[2] == 'PROC']
            
            if reg_findings:
                lines.append("  [REGISTRY MODIFICATIONS]")
                lines.append("  " + "-" * 40)
                for name, weight, _, detail in reg_findings:
                    lines.append(f"    [!] {name}")
                    lines.append(f"        Weight: +{weight}")
                    lines.append(f"        Path: {detail}")
                    lines.append("")
            
            if file_findings:
                lines.append("  [FILE SYSTEM CHANGES]")
                lines.append("  " + "-" * 40)
                for name, weight, _, detail in file_findings:
                    lines.append(f"    [!] {name}")
                    lines.append(f"        Weight: +{weight}")
                    lines.append(f"        File: {detail}")
                    lines.append("")
            
            if proc_findings:
                lines.append("  [PROCESS CREATIONS]")
                lines.append("  " + "-" * 40)
                for name, weight, _, detail in proc_findings:
                    lines.append(f"    [!] {name}")
                    lines.append(f"        Weight: +{weight}")
                    lines.append(f"        Process: {detail}")
                    lines.append("")
        else:
            lines.append("  No state changes detected.")
            lines.append("")
        
        # ETW Behavior
        lines.append("-" * 80)
        lines.append("PHASE 2: ETW BEHAVIOR ANALYSIS")
        lines.append("-" * 80)
        lines.append("")
        
        if results['etw_findings']:
            lines.append(f"  Total Detections: {len(results['etw_findings'])}")
            lines.append("")
            
            for finding in results['etw_findings']:
                lines.append(f"  [!] {finding['name']}")
                lines.append(f"      Weight: +{finding['weight']}")
                lines.append(f"      Type: {finding['type']}")
                
                details = finding.get('details', {})
                if finding.get('type') == 'ETW':
                    if details.get('type') == 'process':
                        lines.append(f"      Process: {details.get('name', 'N/A')}")
                        if details.get('command'):
                            cmd = details['command']
                            lines.append(f"      Command: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
                        if details.get('is_obfuscated'):
                            lines.append(f"      [!] WARNING: Obfuscated command detected!")
                    elif details.get('type') == 'file':
                        lines.append(f"      File: {details.get('filename', 'N/A')}")
                        lines.append(f"      Path: {details.get('path', 'N/A')}")
                lines.append("")
        else:
            lines.append("  No ETW behavior detected.")
            lines.append("")
        
        # Detailed System Changes
        lines.append("-" * 80)
        lines.append("APPENDIX: DETAILED SYSTEM CHANGES")
        lines.append("-" * 80)
        lines.append("")
        
        # Registry changes detail
        b_reg = set(before.get('registry', {}).keys())
        a_reg = set(after.get('registry', {}).keys())
        new_reg = a_reg - b_reg
        
        if new_reg:
            lines.append("  [NEW REGISTRY KEYS]")
            lines.append("  " + "-" * 40)
            for key in sorted(new_reg)[:10]:  # Limit to first 10
                value = after['registry'].get(key, 'N/A')[:50]
                lines.append(f"    + {key}")
                lines.append(f"      Value: {value}{'...' if len(str(value)) > 50 else ''}")
                lines.append("")
            if len(new_reg) > 10:
                lines.append(f"    ... and {len(new_reg) - 10} more")
                lines.append("")
        
        # File changes detail
        b_files = set(before.get('files', {}).keys())
        a_files = set(after.get('files', {}).keys())
        new_files = a_files - b_files
        
        if new_files:
            lines.append("  [NEW FILES]")
            lines.append("  " + "-" * 40)
            for f in sorted(new_files)[:10]:
                info = after['files'].get(f, {})
                size = info.get('size', 0)
                lines.append(f"    + {f}")
                lines.append(f"      Size: {size:,} bytes")
                lines.append("")
            if len(new_files) > 10:
                lines.append(f"    ... and {len(new_files) - 10} more")
                lines.append("")
        
        # Process changes detail
        b_procs = {p['name'] for p in before.get('processes', [])}
        a_procs = {p['name'] for p in after.get('processes', [])}
        new_procs = a_procs - b_procs
        
        if new_procs:
            lines.append("  [NEW PROCESSES]")
            lines.append("  " + "-" * 40)
            for proc in sorted(new_procs)[:10]:
                lines.append(f"    + {proc}")
            if len(new_procs) > 10:
                lines.append(f"    ... and {len(new_procs) - 10} more")
            lines.append("")
        
        # Footer
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        # Write to file
        report_text = '\n'.join(lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n[+] Text report saved: {output_file}")
        return report_text

    def analyze(self, before, after, etw_path=None):
        print("=" * 70)
        print("MALWARE ANALYSIS (Snapshot + ETW)")
        print("=" * 70)
        
        has_etw = etw_path and self.load_etw(etw_path)
        
        print("\n[PHASE 1: STATE CHANGES]")
        state_findings, state_score = self.compare(before, after)
        for name, w, t, p in state_findings:
            print(f"\n[!] {name} (+{w}) [{t}]\n    {p}")
        print(f"\n  State Score: {state_score}")
        
        etw_score = 0
        etw_findings = []
        if has_etw:
            print("\n[PHASE 2: ETW BEHAVIOR]")
            etw_findings, etw_score = self.analyze_etw()
            print(f"\n  ETW Score: {etw_score}")
        else:
            print("\n[!] No ETW data available")
        
        combined = state_score + etw_score
        
        if combined >= 100:
            risk = "CRITICAL"
        elif combined >= 60:
            risk = "HIGH"
        elif combined >= 30:
            risk = "MEDIUM"
        elif combined > 0:
            risk = "LOW"
        else:
            risk = "CLEAN"
        
        print("\n" + "=" * 70)
        print("RISK ASSESSMENT")
        print("=" * 70)
        print(f"State Score: {state_score}")
        print(f"ETW Score:   {etw_score}")
        print(f"TOTAL:       {combined}")
        print(f"RISK:        {risk}")
        print("=" * 70)
        
        results = {
            'state_score': state_score,
            'etw_score': etw_score,
            'combined_score': combined,
            'risk_level': risk,
            'state_findings': state_findings,
            'etw_findings': etw_findings
        }
        
        # Generate text report
        self.generate_text_report(results, before, after)
        
        return results

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--before', required=True)
    p.add_argument('--after', required=True)
    p.add_argument('--rules', required=True)
    p.add_argument('--etw')
    args = p.parse_args()
    
    for f in [args.before, args.after, args.rules]:
        if not os.path.exists(f):
            print(f"Error: {f} not found")
            exit(1)
    
    with open(args.before) as f: before = json.load(f)
    with open(args.after) as f: after = json.load(f)
    
    analyzer = MalwareAnalyzer(args.rules)
    results = analyzer.analyze(before, after, args.etw)
    
    with open("Sha256_dynamic.json", 'w') as f:
        json.dump(results, f, indent=2)
    print("\n[+] JSON report saved")

if __name__ == '__main__':
    main()