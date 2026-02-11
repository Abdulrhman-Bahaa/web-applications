import os

# Paths
zip_dir = r"C:\covid_rat\uploads"
json_dir = r"C:\covid_rat"

# Find the zip file
zip_files = [f for f in os.listdir(zip_dir) if f.lower().endswith(".zip")]

if not zip_files:
    print("[-] No zip file found.")
    exit()

# Take the first zip file
zip_name = os.path.splitext(zip_files[0])[0]
print(f"[+] Found ZIP: {zip_name}.zip")

# Original files
static_json_old = os.path.join(json_dir, "Sha256_static.json")
dynamic_json_old = os.path.join(json_dir, "Sha256_dynamic.json")
static_txt_old = os.path.join(json_dir, "analysis_report_static.txt")
dynamic_txt_old = os.path.join(json_dir, "analysis_report.txt")

# New file names
static_json_new = os.path.join(json_dir, f"{zip_name}_static.json")
dynamic_json_new = os.path.join(json_dir, f"{zip_name}_dynamic.json")
static_txt_new = os.path.join(json_dir, f"{zip_name}_static.txt")
dynamic_txt_new = os.path.join(json_dir, f"{zip_name}_dynamic.txt")

# Rename JSON files
if os.path.exists(static_json_old):
    os.rename(static_json_old, static_json_new)
    print(f"[+] Renamed to {zip_name}_static.json")
else:
    print("[-] Sha256_static.json not found")

if os.path.exists(dynamic_json_old):
    os.rename(dynamic_json_old, dynamic_json_new)
    print(f"[+] Renamed to {zip_name}_dynamic.json")
else:
    print("[-] Sha256_dynamic.json not found")

# Rename TXT files
if os.path.exists(static_txt_old):
    os.rename(static_txt_old, static_txt_new)
    print(f"[+] Renamed to {zip_name}_static.txt")
else:
    print("[-] analysis_report_static.txt not found")

if os.path.exists(dynamic_txt_old):
    os.rename(dynamic_txt_old, dynamic_txt_new)
    print(f"[+] Renamed to {zip_name}_dynamic.txt")
else:
    print("[-] analysis_report.txt not found")

print("[+] All files renamed successfully")
