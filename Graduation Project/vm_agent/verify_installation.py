#!/usr/bin/env python3
"""
Network Monitor Implementation Verification Script
Validates that all components are correctly installed and integrated.
"""

import os
import sys
import json
import subprocess


class VerificationReport:
    def __init__(self):
        self.checks = []
        self.vm_agent_dir = os.path.dirname(os.path.abspath(__file__))

    def check(self, name, condition, details=""):
        """Record a check result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.checks.append((name, condition, details))
        print(f"{status} - {name}")
        if details:
            print(f"      {details}")

    def file_exists(self, filename):
        """Check if file exists"""
        path = os.path.join(self.vm_agent_dir, filename)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        self.check(f"File: {filename}", exists,
                   f"Size: {size} bytes" if exists else "")
        return exists

    def module_importable(self, module_name):
        """Check if module can be imported"""
        try:
            __import__(module_name)
            self.check(f"Module: {module_name}", True, "Importable")
            return True
        except ImportError as e:
            self.check(f"Module: {module_name}", False, str(e))
            return False

    def python_version(self):
        """Check Python version"""
        version = sys.version_info
        required = (3, 7)
        ok = version >= required
        self.check(
            "Python Version",
            ok,
            f"Current: {version.major}.{version.minor}.{version.micro}, Required: {required[0]}.{required[1]}+"
        )
        return ok

    def dependencies(self):
        """Check required dependencies"""
        print("\n" + "="*60)
        print("DEPENDENCY CHECKS")
        print("="*60)

        deps = {
            'psutil': 'psutil (Network monitoring)',
            'json': 'json (Built-in)',
            'subprocess': 'subprocess (Built-in)',
            'threading': 'threading (Built-in)',
            'socket': 'socket (Built-in)',
        }

        for module, description in deps.items():
            try:
                __import__(module)
                self.check(description, True, "Available")
            except ImportError:
                self.check(
                    description, False, "Install: pip install psutil" if module == 'psutil' else "")

    def file_checks(self):
        """Check for required files"""
        print("\n" + "="*60)
        print("FILE CHECKS")
        print("="*60)

        required_files = {
            'network_monitor.py': 'Core module',
            'main.py': 'Main pipeline orchestrator',
            'analyzer.py': 'Analysis engine',
            'etw_monitor.py': 'ETW behavioral monitor',
            'snapshot.py': 'System snapshot tool',
            'static.py': 'Static analysis tool',
            '1.yaml': 'Detection rules',
            'NETWORK_MONITOR_README.md': 'API documentation',
            'NETWORK_ARCHITECTURE.md': 'Architecture guide',
            'QUICK_START_NETWORK.md': 'Quick start guide',
            'IMPLEMENTATION_SUMMARY.md': 'Implementation summary',
            'INTEGRATION_CHECKLIST.md': 'Integration checklist',
        }

        results = {}
        for filename, description in required_files.items():
            path = os.path.join(self.vm_agent_dir, filename)
            exists = os.path.exists(path)
            results[filename] = exists
            status = "✅" if exists else "❌"
            print(f"{status} {filename:30} - {description}")

        return all(results.values())

    def integration_checks(self):
        """Check integration points"""
        print("\n" + "="*60)
        print("INTEGRATION CHECKS")
        print("="*60)

        # Check main.py has network_monitor call
        main_py_path = os.path.join(self.vm_agent_dir, 'main.py')
        with open(main_py_path, 'r') as f:
            main_content = f.read()

        checks = {
            'network_monitor.py subprocess': 'network_monitor.py' in main_content,
            'net_proc definition': 'net_proc' in main_content,
            'sha256_net.json cleanup': 'sha256_net.json' in main_content,
        }

        for check_name, result in checks.items():
            self.check(f"main.py integration: {check_name}", result)

        # Check analyzer.py has --network parameter
        analyzer_py_path = os.path.join(self.vm_agent_dir, 'analyzer.py')
        with open(analyzer_py_path, 'r') as f:
            analyzer_content = f.read()

        analyzer_checks = {
            '--network parameter': '--network' in analyzer_content,
            'network data loading': "args.network" in analyzer_content,
            'network_analysis results': 'network_analysis' in analyzer_content,
        }

        for check_name, result in analyzer_checks.items():
            self.check(f"analyzer.py integration: {check_name}", result)

        return all(checks.values()) and all(analyzer_checks.values())

    def code_quality(self):
        """Check code quality"""
        print("\n" + "="*60)
        print("CODE QUALITY CHECKS")
        print("="*60)

        network_monitor_path = os.path.join(
            self.vm_agent_dir, 'network_monitor.py')

        with open(network_monitor_path, 'r') as f:
            content = f.read()
            lines = len(content.split('\n'))
            has_docstrings = '"""' in content
            has_error_handling = 'except' in content
            has_comments = '#' in content

        self.check("Lines of code", lines > 400, f"Total: {lines} lines")
        self.check("Has docstrings", has_docstrings, "Module documented")
        self.check("Error handling", has_error_handling,
                   "Exception handling present")
        self.check("Code comments", has_comments, "Comments present")

    def report(self):
        """Generate verification report"""
        print("\n" + "="*60)
        print("NETWORK MONITOR VERIFICATION REPORT")
        print("="*60)

        self.python_version()
        self.dependencies()
        self.file_checks()
        self.integration_checks()
        self.code_quality()

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        total = len(self.checks)
        passed = sum(1 for _, condition, _ in self.checks if condition)
        failed = total - passed

        print(f"Total Checks: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        if failed == 0:
            print("\n🎉 ALL CHECKS PASSED - System is ready for production!")
            return True
        else:
            print("\n⚠️  Some checks failed - Please review above")
            return False


def main():
    """Run verification"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "NETWORK MONITOR VERIFICATION SUITE" + " "*14 + "║")
    print("║" + " "*15 + "Version 1.0 - February 13, 2026" + " "*15 + "║")
    print("╚" + "="*58 + "╝")

    verifier = VerificationReport()
    success = verifier.report()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
