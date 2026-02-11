# ===============================
# Advanced Static Malware Analyzer
# Plug & Play Version
# ===============================

import pefile
import hashlib
import math
import re
import os
import json
from datetime import datetime

# ===============================
# CONFIG (ثابت عشان المنظومة)
# ===============================
UPLOADS_DIR = r"C:\covid_rat\uploads"
OUTPUT_DIR = r"C:\covid_rat"
OUTPUT_FILE = "Sha256_static.json"
TEXT_REPORT_FILE = "analysis_report_static.txt"

# ===============================
# Suspicious APIs + Weights
# ===============================
SUSPICIOUS_APIS = {
    "VirtualAlloc": 2,
    "VirtualProtect": 2,
    "CreateRemoteThread": 3,
    "WriteProcessMemory": 3,
    "ReadProcessMemory": 2,
    "WinExec": 2,
    "ShellExecuteA": 2,
    "URLDownloadToFileA": 3,
    "InternetOpenA": 2,
    "InternetReadFile": 2,
    "GetProcAddress": 1,
    "LoadLibraryA": 1
}

# ===============================
# Hashing
# ===============================
def calculate_hashes(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest()
    }

# ===============================
# Entropy
# ===============================
def calculate_entropy(data):
    if not data:
        return 0
    entropy = 0
    length = len(data)
    for x in range(256):
        p_x = data.count(bytes([x])) / length
        if p_x > 0:
            entropy -= p_x * math.log2(p_x)
    return round(entropy, 2)

# ===============================
# Extract URLs & IPs
# ===============================
def extract_urls(file_path):
    urls = set()
    try:
        with open(file_path, "rb") as f:
            data = f.read().decode(errors="ignore")
            urls.update(re.findall(r"http[s]?://[^\s\"']+", data))
            urls.update(re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", data))
    except:
        pass
    return list(urls)

# ===============================
# Extract Strings (ASCII + Unicode)
# ===============================
def extract_strings(file_path, min_length=4):
    strings = {
        "ascii": [],
        "unicode": []
    }

    try:
        with open(file_path, "rb") as f:
            data = f.read()

        # ASCII Strings
        ascii_pattern = rb"[ -~]{%d,}" % min_length
        ascii_strings = re.findall(ascii_pattern, data)
        strings["ascii"] = [s.decode(errors="ignore") for s in ascii_strings]

        # Unicode Strings (UTF-16 LE)
        unicode_pattern = rb"(?:[ -~]\x00){%d,}" % min_length
        unicode_strings = re.findall(unicode_pattern, data)
        strings["unicode"] = [s.decode("utf-16le", errors="ignore") for s in unicode_strings]

    except:
        pass

    return strings

# ===============================
# Extract Resources (Fixed)
# ===============================
def extract_resources(pe):
    resources = []
    version_info = {}
    manifest_content = None

    try:
        # Version Info
        if hasattr(pe, 'FileInfo'):
            for fileinfo in pe.FileInfo:
                if fileinfo.Key == b'StringFileInfo':
                    for st in fileinfo.StringTable:
                        for key, value in st.entries.items():
                            version_info[key.decode(errors="ignore")] = value.decode(errors="ignore")

        # Resources
        if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                name = resource_type.name
                if name is None:
                    name = pefile.RESOURCE_TYPE.get(resource_type.struct.Id)
                else:
                    name = str(name)

                if hasattr(resource_type, "directory"):
                    for resource_id in resource_type.directory.entries:
                        if hasattr(resource_id, "directory"):
                            for resource_lang in resource_id.directory.entries:
                                data_rva = resource_lang.data.struct.OffsetToData
                                size = resource_lang.data.struct.Size

                                data = pe.get_data(data_rva, size)

                                if name == "RT_MANIFEST":
                                    try:
                                        manifest_content = data.decode(errors="ignore")
                                    except:
                                        pass

                                resources.append({
                                    "type": name,
                                    "size": size
                                })

    except:
        pass

    return resources, version_info, manifest_content

# ===============================
# PE Analysis
# ===============================
def analyze_pe(file_path):
    report = {
        "is_pe": False,
        "imports": [],
        "suspicious_apis": [],
        "sections": [],
        "packed": False,
        "overlay": False,
        "entropy": 0,
        "resources": [],
        "version_info": {},
        "manifest": None
    }

    try:
        pe = pefile.PE(file_path)
        report["is_pe"] = True

        # Sections
        for sec in pe.sections:
            report["sections"].append({
                "name": sec.Name.decode(errors="ignore").strip(),
                "entropy": round(sec.get_entropy(), 2),
                "size": sec.SizeOfRawData
            })

        # Imports
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in entry.imports:
                    if imp.name:
                        api = imp.name.decode(errors="ignore")
                        report["imports"].append(api)
                        if api in SUSPICIOUS_APIS:
                            report["suspicious_apis"].append(api)

        # File Entropy
        with open(file_path, "rb") as f:
            data = f.read()
            report["entropy"] = calculate_entropy(data)
            if report["entropy"] > 7.2:
                report["packed"] = True

        # Overlay Detection
        try:
            last = pe.sections[-1]
            end = last.PointerToRawData + last.SizeOfRawData
            if len(data) > end:
                report["overlay"] = True
        except:
            report["overlay"] = False

        # Extract Resources + Version + Manifest
        resources, version_info, manifest = extract_resources(pe)
        report["resources"] = resources
        report["version_info"] = version_info
        report["manifest"] = manifest

    except:
        pass

    return report

# ===============================
# Score Engine
# ===============================
def calculate_score(report):
    score = 0
    reasons = []

    if report["packed"]:
        score += 3
        reasons.append("High entropy (Packed)")

    if report["overlay"]:
        score += 2
        reasons.append("Overlay detected")

    for api in report["suspicious_apis"]:
        score += SUSPICIOUS_APIS.get(api, 1)
        reasons.append(f"Suspicious API: {api}")

    if report["entropy"] > 7.5:
        score += 2
        reasons.append("Very high entropy")

    return score, reasons

# ===============================
# Text Report Generator
# ===============================
def generate_text_report(report, output_path):
    """Generate a well-formatted text report"""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append(" " * 25 + "STATIC MALWARE ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Analysis Type: Static (PE Analysis)")
    lines.append("=" * 80)
    lines.append("")
    
    # File Information
    lines.append("-" * 80)
    lines.append("FILE INFORMATION")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"  File Name:    {report['file_info']['filename']}")
    lines.append(f"  File Path:    {report['file_info']['path']}")
    lines.append(f"  File Size:    {report['file_info']['size']:,} bytes ({report['file_info']['size']/1024:.2f} KB)")
    lines.append("")
    
    # Hashes
    lines.append("-" * 80)
    lines.append("CRYPTOGRAPHIC HASHES")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"  MD5:    {report['hashes']['md5']}")
    lines.append(f"  SHA1:   {report['hashes']['sha1']}")
    lines.append(f"  SHA256: {report['hashes']['sha256']}")
    lines.append("")

    # Strings
    if report.get('strings'):
        lines.append("-" * 80)
        lines.append("EXTRACTED STRINGS")
        lines.append("-" * 80)
        lines.append("")
        ascii_strings = report['strings'].get('ascii', [])[:20]
        unicode_strings = report['strings'].get('unicode', [])[:20]
        for s in ascii_strings:
            lines.append(f"  ASCII:   {s}")
        for s in unicode_strings:
            lines.append(f"  UNICODE: {s}")
        lines.append("  ... (truncated to 20 each) ...")
        lines.append("")

    # Resources
    if report['pe_analysis'].get('resources'):
        lines.append("-" * 80)
        lines.append("RESOURCES")
        lines.append("-" * 80)
        lines.append("")
        for res in report['pe_analysis']['resources']:
            lines.append(f"  Type: {res['type']}, Size: {res['size']}")
        lines.append("")

    # Version Info
    if report['pe_analysis'].get('version_info'):
        lines.append("-" * 80)
        lines.append("VERSION INFO")
        lines.append("-" * 80)
        lines.append("")
        for k, v in report['pe_analysis']['version_info'].items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    # Manifest
    if report['pe_analysis'].get('manifest'):
        lines.append("-" * 80)
        lines.append("MANIFEST")
        lines.append("-" * 80)
        lines.append("")
        manifest_preview = report['pe_analysis']['manifest'][:500].replace("\n", " ")
        lines.append(f"  {manifest_preview} ...")
        lines.append("")

    # Verdict
    lines.append("-" * 80)
    lines.append("VERDICT")
    lines.append("-" * 80)
    lines.append("")
    
    verdict = report['verdict']
    score = report['score']
    
    if verdict == "MALWARE":
        lines.append(f"  [!] VERDICT: {verdict}")
        lines.append(f"  [!] RISK LEVEL: HIGH")
        lines.append(f"  [!] SCORE: {score}/20")
    elif verdict == "SUSPICIOUS":
        lines.append(f"  [!] VERDICT: {verdict}")
        lines.append(f"  [!] RISK LEVEL: MEDIUM")
        lines.append(f"  [!] SCORE: {score}/20")
    else:
        lines.append(f"  [+] VERDICT: {verdict}")
        lines.append(f"  [+] RISK LEVEL: LOW")
        lines.append(f"  [+] SCORE: {score}/20")
    
    lines.append("")
    
    # Reasons
    if report['reasons']:
        lines.append("-" * 80)
        lines.append("DETECTION REASONS")
        lines.append("-" * 80)
        lines.append("")
        for i, reason in enumerate(report['reasons'], 1):
            lines.append(f"  {i}. {reason}")
        lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    # Write to file
    report_text = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"[+] Text report saved: {output_path}")
    return report_text

# ===============================
# Final Analyzer
# ===============================
def analyze_file(file_path):
    report = {}

    report["file_info"] = {
        "path": file_path,
        "filename": os.path.basename(file_path),
        "size": os.path.getsize(file_path)
    }

    report["hashes"] = calculate_hashes(file_path)
    report["urls"] = extract_urls(file_path)
    report["strings"] = extract_strings(file_path)

    pe_report = analyze_pe(file_path)
    report["pe_analysis"] = pe_report

    score, reasons = calculate_score(pe_report)
    report["score"] = score
    report["reasons"] = reasons

    if score >= 7:
        verdict = "MALWARE"
    elif score >= 4:
        verdict = "SUSPICIOUS"
    else:
        verdict = "CLEAN"

    report["verdict"] = verdict
    return report

# ===============================
# Save Reports
# ===============================
def save_report(report):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # JSON report
    json_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print(f"[+] JSON report saved: {json_path}")
    
    # Text report
    text_path = os.path.join(OUTPUT_DIR, TEXT_REPORT_FILE)
    generate_text_report(report, text_path)
    
    return json_path, text_path

# ===============================
# MAIN
# ===============================
def main():
    if not os.path.exists(UPLOADS_DIR):
        print(f"[!] Uploads directory not found: {UPLOADS_DIR}")
        return

    exe_files = [
        os.path.join(UPLOADS_DIR, f)
        for f in os.listdir(UPLOADS_DIR)
        if f.lower().endswith(".exe")
    ]

    if not exe_files:
        print("[!] No EXE files found")
        return

    for exe in exe_files:
        print(f"\n{'='*60}")
        print(f"[*] Analyzing: {exe}")
        print(f"{'='*60}")
        report = analyze_file(exe)
        save_report(report)
        print(f"\n[+] Analysis complete for: {os.path.basename(exe)}")
        print(f"    Verdict: {report['verdict']}")
        print(f"    Score: {report['score']}/20")

    print(f"\n{'='*60}")
    print("[*] All analyses complete")

if __name__ == "__main__":
    main()