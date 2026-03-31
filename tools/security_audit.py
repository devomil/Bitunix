#!/usr/bin/env python3
"""
Security-focused audit tool for cryptocurrency trading bots
Focuses on financial safety, API security, and data protection
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
import subprocess
import sys


@dataclass
class SecurityIssue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    file: str
    line: int
    evidence: str
    remediation: str
    cwe: str = ""  # Common Weakness Enumeration


class SecurityAuditor:
    """Deep security audit for trading applications"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues: List[SecurityIssue] = []
        
    def audit(self) -> List[SecurityIssue]:
        """Run comprehensive security audit"""
        print("🔒 Running Security Audit...")
        print("=" * 80)
        
        self.check_secrets_in_code()
        self.check_git_history_leaks()
        self.check_dependencies()
        self.check_api_security()
        self.check_financial_safeguards()
        self.check_input_validation()
        self.check_logging_security()
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.issues.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return self.issues
    
    def check_secrets_in_code(self):
        """Scan for hardcoded secrets"""
        print("🔍 Checking for hardcoded secrets...")
        
        secret_patterns = [
            (r'api[_-]?key\s*[=:]\s*["\']([a-zA-Z0-9]{20,})["\']', 'API Key'),
            (r'secret[_-]?key\s*[=:]\s*["\']([a-zA-Z0-9]{20,})["\']', 'Secret Key'),
            (r'password\s*[=:]\s*["\']([^"\']+)["\']', 'Password'),
            (r'token\s*[=:]\s*["\']([a-zA-Z0-9]{20,})["\']', 'Token'),
            (r'(sk|pk)_live_[a-zA-Z0-9]{24,}', 'API Key'),
            (r'[0-9a-f]{32,}', 'Potential Secret Hash'),
        ]
        
        for py_file in self.project_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for pattern, secret_type in secret_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Skip comments and examples
                        line_content = lines[line_num - 1].strip()
                        if line_content.startswith('#') or 'example' in line_content.lower():
                            continue
                        
                        self.issues.append(SecurityIssue(
                            severity='CRITICAL',
                            title=f'Hardcoded {secret_type} Detected',
                            description=f'Found potential hardcoded {secret_type.lower()} in source code',
                            file=str(py_file.relative_to(self.project_path)),
                            line=line_num,
                            evidence=line_content[:100],
                            remediation='Move to environment variables using python-dotenv or secrets manager',
                            cwe='CWE-798'
                        ))
            
            except Exception as e:
                print(f"  ⚠️  Error scanning {py_file}: {e}")
    
    def check_git_history_leaks(self):
        """Check if .env or secrets files are in Git"""
        print("🔍 Checking Git history for leaked secrets...")
        
        sensitive_files = ['.env', 'secrets.json', 'credentials.json', 'config.ini']
        
        try:
            # Check current tracked files
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                tracked_files = result.stdout.split('\n')
                
                for sensitive in sensitive_files:
                    if any(sensitive in f for f in tracked_files):
                        self.issues.append(SecurityIssue(
                            severity='CRITICAL',
                            title=f'Sensitive File Tracked in Git: {sensitive}',
                            description=f'{sensitive} is tracked by Git and may contain secrets',
                            file=sensitive,
                            line=0,
                            evidence=f'Found in: git ls-files',
                            remediation=f'Remove from Git: git rm --cached {sensitive} && echo "{sensitive}" >> .gitignore',
                            cwe='CWE-200'
                        ))
        
        except FileNotFoundError:
            print("  ℹ️  Git not found or not a Git repository")
        except Exception as e:
            print(f"  ⚠️  Error checking Git: {e}")
    
    def check_dependencies(self):
        """Check for vulnerable dependencies"""
        print("🔍 Checking dependencies for vulnerabilities...")
        
        requirements_file = self.project_path / 'requirements.txt'
        
        if not requirements_file.exists():
            self.issues.append(SecurityIssue(
                severity='HIGH',
                title='Missing requirements.txt',
                description='No requirements.txt found for dependency tracking',
                file='',
                line=0,
                evidence='File not found',
                remediation='Create requirements.txt: pip freeze > requirements.txt',
                cwe='CWE-1104'
            ))
            return
        
        # Try to run safety check if available
        try:
            result = subprocess.run(
                ['safety', 'check', '--file', str(requirements_file), '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("  ✅ No known vulnerabilities in dependencies")
            else:
                print("  ⚠️  Vulnerabilities found in dependencies")
                # Parse safety output if needed
        
        except FileNotFoundError:
            print("  ℹ️  'safety' package not installed. Install with: pip install safety")
        except Exception as e:
            print(f"  ⚠️  Error checking dependencies: {e}")
    
    def check_api_security(self):
        """Check for API security issues"""
        print("🔍 Checking API security practices...")
        
        for py_file in self.project_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # SSL verification disabled
                if 'verify=False' in content or 'verify = False' in content:
                    matches = re.finditer(r'verify\s*=\s*False', content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        self.issues.append(SecurityIssue(
                            severity='CRITICAL',
                            title='SSL Verification Disabled',
                            description='HTTPS requests with SSL verification disabled',
                            file=str(py_file.relative_to(self.project_path)),
                            line=line_num,
                            evidence=lines[line_num - 1].strip(),
                            remediation='Remove verify=False or set verify=True',
                            cwe='CWE-295'
                        ))
                
                # No timeout on requests
                if 'requests.' in content:
                    patterns = [
                        r'requests\.(get|post|put|delete|patch)\([^)]*\)',
                    ]
                    
                    for pattern in patterns:
                        for match in re.finditer(pattern, content):
                            if 'timeout' not in match.group(0):
                                line_num = content[:match.start()].count('\n') + 1
                                self.issues.append(SecurityIssue(
                                    severity='MEDIUM',
                                    title='HTTP Request Without Timeout',
                                    description='Request can hang indefinitely',
                                    file=str(py_file.relative_to(self.project_path)),
                                    line=line_num,
                                    evidence=lines[line_num - 1].strip(),
                                    remediation='Add timeout: requests.get(url, timeout=10)',
                                    cwe='CWE-400'
                                ))
            
            except Exception as e:
                print(f"  ⚠️  Error scanning {py_file}: {e}")
    
    def check_financial_safeguards(self):
        """Check for financial safety mechanisms"""
        print("🔍 Checking financial safeguards...")
        
        safeguards_found = {
            'max_order_size': False,
            'max_position_size': False,
            'stop_loss': False,
            'daily_loss_limit': False,
            'order_validation': False,
        }
        
        keywords = {
            'max_order_size': ['max_order', 'order_limit', 'max_size'],
            'max_position_size': ['max_position', 'position_limit'],
            'stop_loss': ['stop_loss', 'stoploss', 'max_loss'],
            'daily_loss_limit': ['daily_loss', 'loss_limit', 'max_daily_loss'],
            'order_validation': ['validate_order', 'check_order', 'verify_order'],
        }
        
        for py_file in self.project_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8').lower()
                
                for safeguard, terms in keywords.items():
                    if any(term in content for term in terms):
                        safeguards_found[safeguard] = True
            
            except Exception:
                pass
        
        # Report missing safeguards
        for safeguard, found in safeguards_found.items():
            if not found:
                self.issues.append(SecurityIssue(
                    severity='HIGH' if safeguard in ['max_order_size', 'max_position_size'] else 'MEDIUM',
                    title=f'Missing Financial Safeguard: {safeguard}',
                    description=f'No {safeguard.replace("_", " ")} mechanism detected',
                    file='',
                    line=0,
                    evidence='Pattern not found in codebase',
                    remediation=f'Implement {safeguard.replace("_", " ")} checks before order execution',
                    cwe='CWE-754'
                ))
    
    def check_input_validation(self):
        """Check for input validation issues"""
        print("🔍 Checking input validation...")
        
        dangerous_functions = [
            ('eval(', 'Code Injection', 'CWE-95'),
            ('exec(', 'Code Injection', 'CWE-95'),
            ('__import__(', 'Arbitrary Module Import', 'CWE-95'),
            ('open(', 'File Access', 'CWE-22'),
            ('pickle.loads(', 'Insecure Deserialization', 'CWE-502'),
        ]
        
        for py_file in self.project_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for func, vuln_type, cwe in dangerous_functions:
                    if func in content:
                        for match in re.finditer(re.escape(func), content):
                            line_num = content[:match.start()].count('\n') + 1
                            self.issues.append(SecurityIssue(
                                severity='HIGH',
                                title=f'Dangerous Function: {func}',
                                description=f'Use of {func} can lead to {vuln_type}',
                                file=str(py_file.relative_to(self.project_path)),
                                line=line_num,
                                evidence=lines[line_num - 1].strip(),
                                remediation=f'Avoid {func} or implement strict validation',
                                cwe=cwe
                            ))
            
            except Exception as e:
                print(f"  ⚠️  Error scanning {py_file}: {e}")
    
    def check_logging_security(self):
        """Check for sensitive data in logs"""
        print("🔍 Checking logging security...")
        
        sensitive_log_patterns = [
            (r'log.*api[_-]?key', 'API key logged'),
            (r'log.*password', 'Password logged'),
            (r'log.*secret', 'Secret logged'),
            (r'print.*api[_-]?key', 'API key printed'),
            (r'print.*password', 'Password printed'),
        ]
        
        for py_file in self.project_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for pattern, issue in sensitive_log_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count('\n') + 1
                        self.issues.append(SecurityIssue(
                            severity='HIGH',
                            title='Sensitive Data in Logs',
                            description=issue,
                            file=str(py_file.relative_to(self.project_path)),
                            line=line_num,
                            evidence=lines[line_num - 1].strip(),
                            remediation='Redact sensitive data before logging',
                            cwe='CWE-532'
                        ))
            
            except Exception as e:
                print(f"  ⚠️  Error scanning {py_file}: {e}")
    
    def generate_report(self) -> str:
        """Generate security audit report"""
        report = ["=" * 80]
        report.append("🔒 SECURITY AUDIT REPORT - BITUNIX TRADING BOT")
        report.append("=" * 80)
        report.append("")
        
        # Executive summary
        critical = sum(1 for i in self.issues if i.severity == 'CRITICAL')
        high = sum(1 for i in self.issues if i.severity == 'HIGH')
        medium = sum(1 for i in self.issues if i.severity == 'MEDIUM')
        low = sum(1 for i in self.issues if i.severity == 'LOW')
        
        report.append("📊 EXECUTIVE SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Security Issues: {len(self.issues)}")
        report.append("")
        report.append(f"  🔴 CRITICAL: {critical} (Immediate action required)")
        report.append(f"  🟠 HIGH:     {high} (Fix within 24 hours)")
        report.append(f"  🟡 MEDIUM:   {medium} (Fix within 1 week)")
        report.append(f"  🟢 LOW:      {low} (Fix when possible)")
        report.append("")
        
        if critical > 0:
            report.append("⚠️  CRITICAL ISSUES FOUND - DO NOT USE IN PRODUCTION")
        elif high > 0:
            report.append("⚠️  HIGH SEVERITY ISSUES - USE WITH CAUTION")
        else:
            report.append("✅ No critical or high severity issues found")
        
        report.append("")
        report.append("=" * 80)
        report.append("🔍 DETAILED FINDINGS")
        report.append("=" * 80)
        report.append("")
        
        for i, issue in enumerate(self.issues, 1):
            emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(issue.severity, '⚪')
            
            report.append(f"{i}. {emoji} [{issue.severity}] {issue.title}")
            if issue.file:
                report.append(f"   📁 File: {issue.file}:{issue.line}")
            report.append(f"   📝 Description: {issue.description}")
            if issue.evidence:
                report.append(f"   🔍 Evidence: {issue.evidence}")
            report.append(f"   💡 Remediation: {issue.remediation}")
            if issue.cwe:
                report.append(f"   🔗 Reference: https://cwe.mitre.org/data/definitions/{issue.cwe.split('-')[1]}.html")
            report.append("")
        
        report.append("=" * 80)
        report.append("✅ SECURITY CHECKLIST")
        report.append("=" * 80)
        report.append("")
        report.append("Before deploying to production:")
        report.append("  [ ] All CRITICAL issues resolved")
        report.append("  [ ] All HIGH issues resolved")
        report.append("  [ ] API keys in environment variables only")
        report.append("  [ ] .env file in .gitignore")
        report.append("  [ ] SSL verification enabled")
        report.append("  [ ] Max order size limits implemented")
        report.append("  [ ] Error handling for all API calls")
        report.append("  [ ] Logging redacts sensitive data")
        report.append("  [ ] Dependencies scanned for vulnerabilities")
        report.append("  [ ] Test on demo/testnet account first")
        report.append("")
        
        return "\n".join(report)


def main():
    """Run security audit"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security audit for Bitunix trading bot')
    parser.add_argument('path', nargs='?', default='.', help='Project path to audit')
    parser.add_argument('--json', help='Save JSON report to file')
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor(args.path)
    issues = auditor.audit()
    
    report = auditor.generate_report()
    print("\n" + report)
    
    if args.json:
        with open(args.json, 'w') as f:
            json.dump([asdict(i) for i in issues], f, indent=2)
        print(f"💾 JSON report saved to: {args.json}")
    
    # Exit with error code if critical issues found
    critical_count = sum(1 for i in issues if i.severity == 'CRITICAL')
    if critical_count > 0:
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
