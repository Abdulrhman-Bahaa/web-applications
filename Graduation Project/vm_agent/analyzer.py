import json, yaml, re, argparse, os
from datetime import datetime

class MalwareAnalyzer:
    def __init__(self, rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        self.etw_events = []
        self.detected_signatures = set()

    def load_etw(self, path):
        if not os.path.exists(path): return False
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.etw_events = data.get('events', [])
        print(f"[+] Loaded {len(self.etw_events)} ETW events")
        return True

    def match(self, value, pattern):
        if not value: return False
        value, pattern = str(value).replace('\\','/'), pattern.replace('\\','/')
        if ' OR ' in pattern:
            return any(self.match(value, p.strip()) for p in pattern.split(' OR '))
        pattern = pattern.replace('*','.*').replace('?','.')
        try:
            return re.search(pattern, value, re.IGNORECASE) is not None
        except:
            return pattern.replace('.*','').lower() in value.lower()

    def get_signature(self, rule_name, value):
        normalized = str(value).lower().replace('\\', '/').replace(' ', '')
        return f"{rule_name}|{normalized}"

    def analyze_etw(self):
        findings = []
        score = 0
        for event in self.etw_events:
            event_type = event.get('type')
            if event_type in ['network', 'thread']:
                continue
            for rule in self.rules.get('detection_rules', []):
                if rule.get('weight', 0) <= 0:
                    continue
                matched = False
                value = ""
                if event_type == 'process' and rule['field'] == 'process':
                    value = f"{event.get('name', '')}|{event.get('command', '')}"
                    matched = self.match(value, rule['pattern'])
                elif event_type == 'file' and rule['field'] == 'file':
                    value = event.get('path', '')
                    matched = self.match(value, rule['pattern'])
                elif event_type == 'registry' and rule['field'] == 'registry':
                    value = f"{event.get('operation', '')}|{event.get('path', '')}|{event.get('value_name', '')}"
                    matched = self.match(value, rule['pattern'])
                elif event_type == 'image_load' and rule['field'] == 'image_load':
                    value = f"{event.get('process', '')}|{event.get('image_path', '')}"
                    matched = self.match(value, rule['pattern'])
                if matched:
                    sig = self.get_signature(rule['name'], value)
                    if sig in self.detected_signatures:
                        continue
                    self.detected_signatures.add(sig)
                    findings.append({
                        'name': rule['name'],
                        'weight': rule['weight'],
                        'type': 'ETW',
                        'details': event
                    })
                    score += rule['weight']
                    break
        return findings, score

    def compare(self, before, after):
        events = []
        before_registry = before.get('registry', {})
        after_registry = after.get('registry', {})
        before_files = before.get('files', {})
        after_files = after.get('files', {})
        before_procs = before.get('processes', [])
        after_procs = after.get('processes', [])

        b_reg, a_reg = set(before_registry.keys()), set(after_registry.keys())
        for key in (a_reg - b_reg):
            events.append({"field": "registry", "action": "create", "value": key})
        for key in (b_reg - a_reg):
            events.append({"field": "registry", "action": "delete", "value": key})
        for key in (a_reg & b_reg):
            if before_registry[key] != after_registry[key]:
                events.append({"field": "registry", "action": "modify", "value": key})

        b_file, a_file = set(before_files.keys()), set(after_files.keys())
        for f in (a_file - b_file):
            events.append({"field": "file", "action": "create", "value": f})
            file_info = after_files.get(f, {})
            if file_info.get('hidden', False) or (file_info.get('attributes', 0) & 2):
                events.append({"field": "file", "action": "hide", "value": f})
        for f in (b_file - a_file):
            events.append({"field": "file", "action": "delete", "value": f})
        for f in (a_file & b_file):
            b_info = before_files[f]
            a_info = after_files[f]
            if b_info != a_info:
                events.append({"field": "file", "action": "modify", "value": f})
                if b_info.get('size') != a_info.get('size') or b_info.get('hash') != a_info.get('hash'):
                    events.append({"field": "file", "action": "content_changed", "value": f})
                if b_info.get('permissions') != a_info.get('permissions'):
                    events.append({"field": "file", "action": "permission_changed", "value": f})
                if b_info.get('created') != a_info.get('created') or b_info.get('modified') != a_info.get('modified'):
                    events.append({"field": "file", "action": "timestomp", "value": f})

        deleted_files = {f: before_files[f] for f in (b_file - a_file)}
        created_files = {f: after_files[f] for f in (a_file - b_file)}
        for d_path, d_info in list(deleted_files.items()):
            for c_path, c_info in list(created_files.items()):
                if d_info.get('hash') == c_info.get('hash') and d_path != c_path:
                    events.append({"field": "file", "action": "move", "value": f"{d_path} -> {c_path}"})
                    if d_path in deleted_files:
                        del deleted_files[d_path]
                    if c_path in created_files:
                        del created_files[c_path]
                    break
        for c_path, c_info in created_files.items():
            for existing_path, existing_info in after_files.items():
                if c_path != existing_path and c_info.get('hash') == existing_info.get('hash'):
                    events.append({"field": "file", "action": "copy", "value": f"{existing_path} -> {c_path}"})

        b_procs = {f"{p['name']}|{p.get('command_line', '')}": p for p in before_procs}
        a_procs = {f"{p['name']}|{p.get('command_line', '')}": p for p in after_procs}
        b_sigs = set(b_procs.keys())
        a_sigs = set(a_procs.keys())

        for sig in (a_sigs - b_sigs):
            p = a_procs[sig]
            events.append({"field": "process", "action": "create", "value": p['name'], "details": p})
            parent = p.get('parent_name', '')
            if parent in ['explorer.exe', 'svchost.exe', 'lsass.exe', 'services.exe'] and p['name'] not in [parent, 'explorer.exe']:
                events.append({"field": "process", "action": "suspicious_spawn", "value": p['name'], "parent": parent})
            if p.get('image_path') and p.get('mapped_image') and p['image_path'] != p.get('mapped_image'):
                events.append({"field": "process", "action": "hollow", "value": p['name']})
            if p.get('integrity_level') == 'System' and p.get('parent_integrity') == 'Medium':
                events.append({"field": "process", "action": "privilege_escalation", "value": p['name']})

        for sig in (b_sigs - a_sigs):
            p = b_procs[sig]
            events.append({"field": "process", "action": "delete", "value": p['name']})

        for sig in (b_sigs & a_sigs):
            b_p = b_procs[sig]
            a_p = a_procs[sig]
            if b_p != a_p:
                events.append({"field": "process", "action": "modify", "value": a_p['name']})
            if b_p.get('memory_protection') != a_p.get('memory_protection'):
                events.append({"field": "process", "action": "memory_changed", "value": a_p['name']})
            b_modules = set(b_p.get('modules', []))
            a_modules = set(a_p.get('modules', []))
            for mod in (a_modules - b_modules):
                events.append({"field": "process", "action": "dll_load", "value": f"{a_p['name']}:{mod}"})
                if any(sus in mod.lower() for sus in ['\\appdata\\', '\\temp\\', '\\downloads\\', '\\programdata\\']):
                    events.append({"field": "process", "action": "suspicious_dll", "value": f"{a_p['name']}:{mod}"})
            for mod in (b_modules - a_modules):
                events.append({"field": "process", "action": "dll_unload", "value": f"{a_p['name']}:{mod}"})
            b_threads = b_p.get('thread_count', 0)
            a_threads = a_p.get('thread_count', 0)
            if a_threads > b_threads * 2 and a_threads > 10:
                events.append({"field": "process", "action": "thread_spike", "value": f"{a_p['name']}:{b_threads}->{a_threads}"})
            if b_p.get('is_suspended') == False and a_p.get('is_suspended') == True:
                events.append({"field": "process", "action": "suspend", "value": a_p['name']})
            elif b_p.get('is_suspended') == True and a_p.get('is_suspended') == False:
                events.append({"field": "process", "action": "resume", "value": a_p['name']})
            b_handles = set(h.get('name', '') for h in b_p.get('handles', []))
            a_handles = set(h.get('name', '') for h in a_p.get('handles', []))
            for h in (a_handles - b_handles):
                if 'mutex' in h.lower() or 'mutant' in h.lower():
                    events.append({"field": "process", "action": "mutex_create", "value": h})

        findings, score = self.apply_rules(events)
        return findings, score

    def apply_rules(self, events):
        findings = []
        score = 0
        for event in events:
            for rule in self.rules.get('detection_rules', []):
                if rule.get('weight', 0) <= 0:
                    continue
                if rule.get('field') != event.get('field'):
                    continue
                if rule.get('action') != event.get('action'):
                    continue
                if not self.match(event.get('value', ''), rule.get('pattern', '')):
                    continue
                sig = self.get_signature(rule['name'], event.get('value', ''))
                if sig in self.detected_signatures:
                    continue
                self.detected_signatures.add(sig)
                finding = {
                    'name': rule['name'],
                    'weight': rule['weight'],
                    'field': event['field'],
                    'action': event['action'],
                    'value': event.get('value', ''),
                    'details': event.get('details', {})
                }
                findings.append(finding)
                score += rule['weight']
                break
        return findings, score

    def analyze(self, before, after, etw_path=None):
        self.detected_signatures = set()
        print("="*70)
        print("MALWARE ANALYSIS (Snapshot + ETW)")
        print("="*70)
        has_etw = etw_path and self.load_etw(etw_path)
        print("\n[PHASE 1: STATE CHANGES]")
        state_findings, state_score = self.compare(before, after)
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
        if combined >= 100: risk="CRITICAL"
        elif combined >= 60: risk="HIGH"
        elif combined >= 30: risk="MEDIUM"
        elif combined > 0: risk="LOW"
        else: risk="CLEAN"
        print("\n" + "="*70)
        print("RISK ASSESSMENT")
        print("="*70)
        print(f"State Score: {state_score}")
        print(f"ETW Score:   {etw_score}")
        print(f"TOTAL:       {combined}")
        print(f"RISK:        {risk}")
        print("="*70)
        results = {
            'state_score': state_score,
            'etw_score': etw_score,
            'combined_score': combined,
            'risk_level': risk,
            'state_findings': state_findings,
            'etw_findings': etw_findings
        }
        return results


####################################################################################################
####################################################################################################
####################################################################################################
#                                                                                                  #
#                                    OUTPUT GENERATION SECTION                                     #
#                                                                                                  #
#                           This section handles all output files:                                 #
#                           - JSON report (machine-readable)                                       #
#                           - TXT report (human-readable)                                          #
#                                                                                                  #
####################################################################################################
####################################################################################################
####################################################################################################


def generate_text_report(results, output_file="analysis_report.txt"):
    lines = []
    lines.append("="*80)
    lines.append(" " * 25 + "MALWARE ANALYSIS REPORT")
    lines.append("="*80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Analysis Type: Dynamic (Snapshot + ETW)")
    lines.append("="*80)
    lines.append("")
    lines.append("-"*80)
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-"*80)
    lines.append("")
    risk = results['risk_level']
    risk_banner = {
        'CRITICAL':'!!! CRITICAL THREAT DETECTED !!!',
        'HIGH':'!! HIGH RISK DETECTED !!',
        'MEDIUM':'! MEDIUM RISK DETECTED !',
        'LOW':'LOW RISK DETECTED',
        'CLEAN':'NO THREATS DETECTED'
    }.get(risk,'UNKNOWN')
    lines.append(f"  Overall Risk Level: {risk}")
    lines.append(f"  {risk_banner}")
    lines.append("")
    lines.append(f"  State Change Score:  {results['state_score']:>3}/100")
    lines.append(f"  ETW Behavior Score:  {results['etw_score']:>3}/100")
    lines.append(f"  Combined Score:      {results['combined_score']:>3}/100")
    lines.append("")

    lines.append("-"*80)
    lines.append("PHASE 1: SYSTEM STATE CHANGES")
    lines.append("-"*80)
    lines.append("")
    state_findings = results.get('state_findings', [])
    if state_findings:
        lines.append(f"  Total Detections: {len(state_findings)}")
        lines.append("")
        reg_findings = [f for f in state_findings if f.get('field') == 'registry']
        file_findings = [f for f in state_findings if f.get('field') == 'file']
        proc_findings = [f for f in state_findings if f.get('field') == 'process']
        if reg_findings:
            lines.append("  [REGISTRY OPERATIONS]")
            lines.append("  " + "-" * 40)
            for f in reg_findings[:5]:
                lines.append(f"    [!] {f['name']} (+{f['weight']})")
                lines.append(f"        Action: {f['action']} | Key: {f['value'][:50]}")
                lines.append("")
            if len(reg_findings) > 5:
                lines.append(f"    ... and {len(reg_findings) - 5} more")
                lines.append("")
        if file_findings:
            lines.append("  [FILE SYSTEM OPERATIONS]")
            lines.append("  " + "-" * 40)
            for f in file_findings[:5]:
                lines.append(f"    [!] {f['name']} (+{f['weight']})")
                lines.append(f"        Action: {f['action']} | Path: {f['value'][:50]}")
                lines.append("")
            if len(file_findings) > 5:
                lines.append(f"    ... and {len(file_findings) - 5} more")
                lines.append("")
        if proc_findings:
            lines.append("  [PROCESS OPERATIONS]")
            lines.append("  " + "-" * 40)
            for f in proc_findings[:5]:
                lines.append(f"    [!] {f['name']} (+{f['weight']})")
                lines.append(f"        Action: {f['action']} | Process: {f['value'][:50]}")
                lines.append("")
            if len(proc_findings) > 5:
                lines.append(f"    ... and {len(proc_findings) - 5} more")
                lines.append("")
    else:
        lines.append("  No state changes detected.")
        lines.append("")

    lines.append("-"*80)
    lines.append("PHASE 2: ETW BEHAVIOR ANALYSIS")
    lines.append("-"*80)
    lines.append("")
    etw_findings = results.get('etw_findings', [])
    if etw_findings:
        lines.append(f"  Total Detections: {len(etw_findings)}")
        lines.append("")
        for f in etw_findings[:10]:
            lines.append(f"  [!] {f['name']} (+{f['weight']}) [ETW]")
            details = f.get('details', {})
            event_type = details.get('type', 'unknown')
            if event_type == 'process':
                lines.append(f"      Process: {details.get('name', 'N/A')}")
                if details.get('command'):
                    cmd = details['command']
                    lines.append(f"      Command: {cmd[:80]}{'...' if len(cmd) > 80 else ''}")
            elif event_type == 'file':
                lines.append(f"      File: {details.get('filename', details.get('path', 'N/A'))}")
            elif event_type == 'registry':
                lines.append(f"      Registry: [{details.get('operation', 'N/A')}] {details.get('path', 'N/A')[:60]}")
            elif event_type == 'image_load':
                lines.append(f"      DLL: {details.get('process', 'N/A')} loaded {details.get('image_path', 'N/A')[:50]}")
            lines.append("")
        if len(etw_findings) > 10:
            lines.append(f"  ... and {len(etw_findings) - 10} more detections")
            lines.append("")
    else:
        lines.append("  No ETW behavior detected.")
        lines.append("")

    lines.append("="*80)
    lines.append("END OF REPORT")
    lines.append("="*80)

    report_text = '\n'.join(lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n[+] Text report saved: {output_file}")
    return report_text


def save_json_report(results, filename="Sha256_dynamic.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] JSON report saved: {filename}")


####################################################################################################
####################################################################################################
####################################################################################################
#                                                                                                  #
#                                       MAIN ENTRY POINT                                           #
#                                                                                                  #
####################################################################################################
####################################################################################################
####################################################################################################


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

    with open(args.before, encoding='utf-8') as f: 
        before = json.load(f)
    with open(args.after, encoding='utf-8') as f: 
        after = json.load(f)

    analyzer = MalwareAnalyzer(args.rules)
    results = analyzer.analyze(before, after, args.etw)

    ################################################################################################
    #                              GENERATE OUTPUT FILES                                           #
    ################################################################################################
    
    # Generate human-readable text report
    generate_text_report(results)
    
    # Generate machine-readable JSON report
    save_json_report(results)


if __name__ == '__main__':
    main()