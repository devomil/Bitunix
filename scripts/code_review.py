#!/usr/bin/env python3
"""
Comprehensive Code Review Script for Bitunix
Analyzes Python codebase for:
1. Security vulnerabilities
2. Performance bottlenecks
3. Code quality issues
4. Missing error handling
5. Opportunities to simplify
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys


@dataclass
class Finding:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # SECURITY, PERFORMANCE, QUALITY, ERROR_HANDLING, SIMPLIFICATION
    file: str
    line: int
    issue: str
    recommendation: str
    code_snippet: str = ""


class CodeReviewer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.findings: List[Finding] = []
        self.stats = {
            "files_analyzed": 0,
            "lines_of_code": 0,
            "functions": 0,
            "classes": 0,
        }

    def analyze_project(self):
        """Main entry point for code analysis"""
        print("🔍 Starting comprehensive code review of Bitunix...")
        
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_skip(f)]
        
        print(f"📁 Found {len(python_files)} Python files to analyze\n")
        
        for file_path in python_files:
            self.analyze_file(file_path)
        
        self.generate_report()

    def _should_skip(self, path: Path) -> bool:
        """Skip common non-source directories"""
        skip_dirs = {".git", "__pycache__", "venv", "env", ".venv", "node_modules", ".pytest_cache", "dist", "build"}
        return any(skip_dir in path.parts for skip_dir in skip_dirs)

    def analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            self.stats["files_analyzed"] += 1
            self.stats["lines_of_code"] += len(lines)
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                self.analyze_ast(tree, file_path, lines)
            except SyntaxError as e:
                self.findings.append(Finding(
                    severity="CRITICAL",
                    category="QUALITY",
                    file=str(file_path.relative_to(self.root_path)),
                    line=e.lineno or 0,
                    issue=f"Syntax error: {e.msg}",
                    recommendation="Fix syntax error before proceeding"
                ))
                return
            
            # Text-based security checks
            self.check_security_patterns(content, file_path, lines)
            
            # Code quality checks
            self.check_code_quality(content, file_path, lines)
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")

    def analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]):
        """Analyze Python AST for issues"""
        
        for node in ast.walk(tree):
            # Count functions and classes
            if isinstance(node, ast.FunctionDef):
                self.stats["functions"] += 1
                self.check_function(node, file_path, lines)
            elif isinstance(node, ast.ClassDef):
                self.stats["classes"] += 1
                self.check_class(node, file_path, lines)
            
            # Security checks
            elif isinstance(node, ast.Call):
                self.check_dangerous_calls(node, file_path, lines)
            
            # Performance checks
            elif isinstance(node, (ast.For, ast.While)):
                self.check_loop_performance(node, file_path, lines)
            
            # Error handling
            elif isinstance(node, ast.Try):
                self.check_exception_handling(node, file_path, lines)

    def check_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str]):
        """Analyze function for issues"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Check function length
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_length = node.end_lineno - node.lineno
            if func_length > 50:
                self.findings.append(Finding(
                    severity="MEDIUM",
                    category="SIMPLIFICATION",
                    file=rel_path,
                    line=node.lineno,
                    issue=f"Function '{node.name}' is {func_length} lines long",
                    recommendation="Consider breaking this function into smaller, focused functions (aim for <50 lines)"
                ))
        
        # Check for missing docstring
        if not ast.get_docstring(node) and not node.name.startswith('_'):
            self.findings.append(Finding(
                severity="LOW",
                category="QUALITY",
                file=rel_path,
                line=node.lineno,
                issue=f"Public function '{node.name}' lacks docstring",
                recommendation="Add a docstring describing parameters, return value, and purpose"
            ))
        
        # Check for too many parameters
        if len(node.args.args) > 5:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="SIMPLIFICATION",
                file=rel_path,
                line=node.lineno,
                issue=f"Function '{node.name}' has {len(node.args.args)} parameters",
                recommendation="Consider using a config object or dataclass to group related parameters"
            ))
        
        # Check cyclomatic complexity (simple version - count branching statements)
        complexity = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler)))
        if complexity > 10:
            self.findings.append(Finding(
                severity="HIGH",
                category="SIMPLIFICATION",
                file=rel_path,
                line=node.lineno,
                issue=f"Function '{node.name}' has high complexity (score: {complexity})",
                recommendation="Refactor to reduce branching logic and improve testability"
            ))

    def check_class(self, node: ast.ClassDef, file_path: Path, lines: List[str]):
        """Analyze class for issues"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self.findings.append(Finding(
                severity="LOW",
                category="QUALITY",
                file=rel_path,
                line=node.lineno,
                issue=f"Class '{node.name}' lacks docstring",
                recommendation="Add a docstring describing the class purpose and responsibilities"
            ))
        
        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 15:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="SIMPLIFICATION",
                file=rel_path,
                line=node.lineno,
                issue=f"Class '{node.name}' has {len(methods)} methods",
                recommendation="Consider splitting into smaller, focused classes (Single Responsibility Principle)"
            ))

    def check_dangerous_calls(self, node: ast.Call, file_path: Path, lines: List[str]):
        """Check for dangerous function calls"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        dangerous_funcs = {
            'eval': ('CRITICAL', 'Arbitrary code execution risk'),
            'exec': ('CRITICAL', 'Arbitrary code execution risk'),
            'compile': ('HIGH', 'Dynamic code compilation risk'),
            '__import__': ('HIGH', 'Dynamic import can be unsafe'),
            'pickle.loads': ('HIGH', 'Pickle deserialization vulnerability'),
            'yaml.load': ('HIGH', 'Use yaml.safe_load() instead'),
        }
        
        func_name = self._get_call_name(node)
        
        for danger, (severity, desc) in dangerous_funcs.items():
            if func_name and danger in func_name:
                self.findings.append(Finding(
                    severity=severity,
                    category="SECURITY",
                    file=rel_path,
                    line=node.lineno,
                    issue=f"Dangerous function call: {func_name}",
                    recommendation=f"{desc}. Validate all inputs or use safer alternatives"
                ))

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract function name from call node"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
            return '.'.join(parts)
        return ""

    def check_loop_performance(self, node: ast.For | ast.While, file_path: Path, lines: List[str]):
        """Check for potential performance issues in loops"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Check for nested loops (O(n²) or worse)
        nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n is not node]
        if len(nested_loops) >= 2:
            self.findings.append(Finding(
                severity="HIGH",
                category="PERFORMANCE",
                file=rel_path,
                line=node.lineno,
                issue="Deeply nested loops detected (O(n³) or worse)",
                recommendation="Consider using better data structures (sets, dicts) or algorithms to reduce complexity"
            ))
        elif len(nested_loops) == 1:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="PERFORMANCE",
                file=rel_path,
                line=node.lineno,
                issue="Nested loops detected (O(n²))",
                recommendation="Profile this code section and consider optimization if it's a hot path"
            ))
        
        # Check for list appends in loop (could use list comprehension)
        if isinstance(node, ast.For):
            appends = [n for n in ast.walk(node) if isinstance(n, ast.Call) and 
                      isinstance(n.func, ast.Attribute) and n.func.attr == 'append']
            if appends and len(node.body) <= 3:
                self.findings.append(Finding(
                    severity="LOW",
                    category="SIMPLIFICATION",
                    file=rel_path,
                    line=node.lineno,
                    issue="Loop with append() could be simplified",
                    recommendation="Consider using list comprehension for better readability and performance"
                ))

    def check_exception_handling(self, node: ast.Try, file_path: Path, lines: List[str]):
        """Check exception handling patterns"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Check for bare except
        for handler in node.handlers:
            if handler.type is None:
                self.findings.append(Finding(
                    severity="HIGH",
                    category="ERROR_HANDLING",
                    file=rel_path,
                    line=handler.lineno,
                    issue="Bare except clause catches all exceptions",
                    recommendation="Catch specific exceptions. Use 'except Exception:' at minimum, or specific exception types"
                ))
            
            # Check for pass in except (silently swallowing errors)
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.findings.append(Finding(
                    severity="HIGH",
                    category="ERROR_HANDLING",
                    file=rel_path,
                    line=handler.lineno,
                    issue="Exception silently ignored with 'pass'",
                    recommendation="Log the error or handle it appropriately. Silent failures make debugging impossible"
                ))
            
            # Check for catching Exception without re-raising
            if handler.type and isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(handler))
                has_log = any(
                    isinstance(n, ast.Call) and 
                    isinstance(n.func, ast.Attribute) and 
                    n.func.attr in ('log', 'error', 'warning', 'exception', 'debug', 'info')
                    for n in ast.walk(handler)
                )
                if not has_raise and not has_log:
                    self.findings.append(Finding(
                        severity="MEDIUM",
                        category="ERROR_HANDLING",
                        file=rel_path,
                        line=handler.lineno,
                        issue="Catching Exception without logging or re-raising",
                        recommendation="Log the exception for debugging, or re-raise if you can't handle it"
                    ))

    def check_security_patterns(self, content: str, file_path: Path, lines: List[str]):
        """Text-based security pattern matching"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Hardcoded password detected', 
             'Use environment variables or secure credential management'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Hardcoded API key detected',
             'Use environment variables (os.getenv) or a secrets manager'),
            (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Hardcoded secret key detected',
             'Use environment variables or configuration files (not in git)'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'MEDIUM', 'Hardcoded token detected',
             'Use environment variables or secure storage'),
            (r'SELECT\s+.*\s+FROM\s+.*\+', 'CRITICAL', 'Potential SQL injection via string concatenation',
             'Use parameterized queries or an ORM'),
            (r'execute\(.*%.*\)', 'CRITICAL', 'Potential SQL injection via string formatting',
             'Use parameterized queries with placeholders'),
            (r'shell\s*=\s*True', 'CRITICAL', 'subprocess with shell=True is dangerous',
             'Use shell=False and pass arguments as a list'),
            (r'md5\(', 'HIGH', 'MD5 is cryptographically broken',
             'Use SHA-256 or better for hashing, bcrypt/argon2 for passwords'),
            (r'sha1\(', 'MEDIUM', 'SHA-1 is deprecated',
             'Use SHA-256 or better'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, severity, issue, recommendation in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.findings.append(Finding(
                        severity=severity,
                        category="SECURITY",
                        file=rel_path,
                        line=i,
                        issue=issue,
                        recommendation=recommendation,
                        code_snippet=line.strip()
                    ))

    def check_code_quality(self, content: str, file_path: Path, lines: List[str]):
        """Text-based code quality checks"""
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Check for print statements (should use logging)
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and 'if __name__' not in ''.join(lines[max(0, i-5):i+5]):
                self.findings.append(Finding(
                    severity="LOW",
                    category="QUALITY",
                    file=rel_path,
                    line=i,
                    issue="Using print() instead of logging",
                    recommendation="Use the logging module for better control and production readiness"
                ))
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.findings.append(Finding(
                    severity="LOW",
                    category="QUALITY",
                    file=rel_path,
                    line=i,
                    issue=f"Line exceeds 120 characters ({len(line)} chars)",
                    recommendation="Break long lines for better readability (PEP 8 recommends 79-120)"
                ))
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                self.findings.append(Finding(
                    severity="LOW",
                    category="QUALITY",
                    file=rel_path,
                    line=i,
                    issue="Unresolved TODO/FIXME comment",
                    recommendation="Track technical debt in issues or resolve before production",
                    code_snippet=line.strip()
                ))
        
        # Check for commented-out code (heuristic)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') and len(stripped) > 2:
                # Simple heuristic: comments with code-like patterns
                if re.search(r'#\s*(def |class |import |return |if |for |while |\w+\s*=)', stripped):
                    self.findings.append(Finding(
                        severity="LOW",
                        category="QUALITY",
                        file=rel_path,
                        line=i,
                        issue="Commented-out code detected",
                        recommendation="Remove dead code. Git preserves history if you need it back"
                    ))
                    break  # Only report once per file

    def generate_report(self):
        """Generate prioritized findings report"""
        print("\n" + "="*80)
        print("📊 CODE REVIEW COMPLETE")
        print("="*80)
        
        print(f"\n📈 Statistics:")
        print(f"  Files analyzed: {self.stats['files_analyzed']}")
        print(f"  Lines of code: {self.stats['lines_of_code']:,}")
        print(f"  Functions: {self.stats['functions']}")
        print(f"  Classes: {self.stats['classes']}")
        print(f"  Total findings: {len(self.findings)}")
        
        # Group by category and severity
        by_category = defaultdict(list)
        by_severity = defaultdict(list)
        
        for finding in self.findings:
            by_category[finding.category].append(finding)
            by_severity[finding.severity].append(finding)
        
        print(f"\n📋 Findings by Category:")
        for category in ["SECURITY", "PERFORMANCE", "ERROR_HANDLING", "QUALITY", "SIMPLIFICATION"]:
            count = len(by_category[category])
            print(f"  {category}: {count}")
        
        print(f"\n🚨 Findings by Severity:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = len(by_severity[severity])
            if count > 0:
                print(f"  {severity}: {count}")
        
        # Detailed findings
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        sorted_findings = sorted(self.findings, key=lambda x: (
            severity_order.index(x.severity),
            x.category,
            x.file,
            x.line
        ))
        
        print("\n" + "="*80)
        print("🔍 DETAILED FINDINGS (Prioritized)")
        print("="*80)
        
        current_severity = None
        for i, finding in enumerate(sorted_findings, 1):
            if finding.severity != current_severity:
                current_severity = finding.severity
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}.get(current_severity, "⚫")
                print(f"\n{emoji} {current_severity} SEVERITY")
                print("-" * 80)
            
            print(f"\n[{i}] {finding.category} - {finding.file}:{finding.line}")
            print(f"    Issue: {finding.issue}")
            print(f"    ➜ {finding.recommendation}")
            if finding.code_snippet:
                print(f"    Code: {finding.code_snippet}")
        
        # Save JSON report
        self.save_json_report(sorted_findings)
        
        print("\n" + "="*80)
        print("✅ Review complete! JSON report saved to: code_review_report.json")
        print("="*80)

    def save_json_report(self, sorted_findings: List[Finding]):
        """Save findings to JSON file"""
        report = {
            "metadata": {
                "project": "Bitunix",
                "files_analyzed": self.stats["files_analyzed"],
                "lines_of_code": self.stats["lines_of_code"],
                "functions": self.stats["functions"],
                "classes": self.stats["classes"],
                "total_findings": len(self.findings),
            },
            "summary": {
                severity: len([f for f in self.findings if f.severity == severity])
                for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            },
            "findings": [asdict(f) for f in sorted_findings]
        }
        
        with open("code_review_report.json", "w") as f:
            json.dump(report, f, indent=2)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    reviewer = CodeReviewer(root)
    reviewer.analyze_project()


if __name__ == "__main__":
    main()
