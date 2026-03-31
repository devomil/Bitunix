#!/usr/bin/env python3
"""
Automated Code Review Tool for Bitunix Trading Bot
Scans for security issues, performance problems, and code quality issues
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Finding:
    """Code review finding"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Security, Performance, Quality, Error Handling
    file: str
    line: int
    issue: str
    recommendation: str
    code_snippet: str = ""


class CodeReviewer:
    """Automated code reviewer for Python trading bots"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.findings: List[Finding] = []
        
        # Dangerous patterns to search for
        self.security_patterns = {
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']': 'Hardcoded API key detected',
            r'secret\s*=\s*["\'][^"\']+["\']': 'Hardcoded secret detected',
            r'password\s*=\s*["\'][^"\']+["\']': 'Hardcoded password detected',
            r'verify\s*=\s*False': 'SSL verification disabled',
            r'shell\s*=\s*True': 'Shell injection vulnerability',
            r'eval\s*\(': 'Dangerous eval() usage',
            r'exec\s*\(': 'Dangerous exec() usage',
            r'pickle\.loads': 'Unsafe pickle deserialization',
        }
        
        self.performance_patterns = {
            r'requests\.(get|post|put|delete)\([^)]*\)(?!.*timeout)': 'No timeout on HTTP request',
            r'time\.sleep\(': 'Blocking sleep in code',
            r'if\s+\w+\s+in\s+\[': 'Inefficient list membership check',
        }
    
    def review(self) -> List[Finding]:
        """Run complete code review"""
        print(f"🔍 Reviewing code in: {self.project_path}")
        
        # Find all Python files
        python_files = list(self.project_path.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files")
        
        for py_file in python_files:
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            self.review_file(py_file)
        
        # Check for missing files
        self.check_project_structure()
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.findings.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return self.findings
    
    def review_file(self, file_path: Path):
        """Review a single Python file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Pattern-based checks
            self.check_security_patterns(file_path, content, lines)
            self.check_performance_patterns(file_path, content, lines)
            
            # AST-based checks
            try:
                tree = ast.parse(content)
                self.check_ast_issues(file_path, tree, lines)
            except SyntaxError:
                self.findings.append(Finding(
                    severity='HIGH',
                    category='Quality',
                    file=str(file_path.relative_to(self.project_path)),
                    line=0,
                    issue='Syntax error in file',
                    recommendation='Fix syntax errors'
                ))
        
        except Exception as e:
            print(f"⚠️  Error reviewing {file_path}: {e}")
    
    def check_security_patterns(self, file_path: Path, content: str, lines: List[str]):
        """Check for security anti-patterns"""
        for pattern, issue in self.security_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                
                self.findings.append(Finding(
                    severity='CRITICAL',
                    category='Security',
                    file=str(file_path.relative_to(self.project_path)),
                    line=line_num,
                    issue=issue,
                    recommendation='Move sensitive data to environment variables',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
    
    def check_performance_patterns(self, file_path: Path, content: str, lines: List[str]):
        """Check for performance issues"""
        for pattern, issue in self.performance_patterns.items():
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                recommendation = {
                    'No timeout on HTTP request': 'Add timeout parameter: requests.get(url, timeout=10)',
                    'Blocking sleep in code': 'Consider using async/await or threading',
                    'Inefficient list membership check': 'Use set for O(1) lookups instead of list',
                }.get(issue, 'Review for optimization opportunity')
                
                self.findings.append(Finding(
                    severity='MEDIUM',
                    category='Performance',
                    file=str(file_path.relative_to(self.project_path)),
                    line=line_num,
                    issue=issue,
                    recommendation=recommendation,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
    
    def check_ast_issues(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for issues using AST analysis"""
        
        class IssueVisitor(ast.NodeVisitor):
            def __init__(self, reviewer, file_path, lines):
                self.reviewer = reviewer
                self.file_path = file_path
                self.lines = lines
                self.function_lengths = []
            
            def visit_ExceptHandler(self, node):
                """Check exception handling"""
                # Bare except
                if node.type is None:
                    self.reviewer.findings.append(Finding(
                        severity='HIGH',
                        category='Error Handling',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue='Bare except clause catches all exceptions',
                        recommendation='Specify exception types: except (ValueError, KeyError):',
                        code_snippet=self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else ''
                    ))
                
                # Empty except block
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    self.reviewer.findings.append(Finding(
                        severity='MEDIUM',
                        category='Error Handling',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue='Empty except block silently ignores errors',
                        recommendation='Add logging or proper error handling',
                        code_snippet=self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else ''
                    ))
                
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                """Check function complexity"""
                # Function length
                func_length = (node.end_lineno or node.lineno) - node.lineno
                if func_length > 50:
                    self.reviewer.findings.append(Finding(
                        severity='LOW',
                        category='Quality',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue=f'Function {node.name} is {func_length} lines long',
                        recommendation='Break into smaller functions for better maintainability',
                        code_snippet=f'def {node.name}(...):'
                    ))
                
                # Missing docstring
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    self.reviewer.findings.append(Finding(
                        severity='LOW',
                        category='Quality',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue=f'Function {node.name} missing docstring',
                        recommendation='Add docstring explaining purpose, parameters, and return value',
                        code_snippet=f'def {node.name}(...):'
                    ))
                
                # Too many arguments
                args_count = len(node.args.args) + len(node.args.kwonlyargs)
                if args_count > 5:
                    self.reviewer.findings.append(Finding(
                        severity='LOW',
                        category='Quality',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue=f'Function {node.name} has {args_count} parameters',
                        recommendation='Consider using a config object or breaking into smaller functions',
                        code_snippet=f'def {node.name}(...):'
                    ))
                
                self.generic_visit(node)
            
            def visit_Try(self, node):
                """Check try-except blocks"""
                # Try without except
                if not node.handlers:
                    self.reviewer.findings.append(Finding(
                        severity='MEDIUM',
                        category='Error Handling',
                        file=str(self.file_path.relative_to(self.reviewer.project_path)),
                        line=node.lineno,
                        issue='Try block without except handler',
                        recommendation='Add appropriate exception handling',
                        code_snippet=self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else ''
                    ))
                
                self.generic_visit(node)
        
        visitor = IssueVisitor(self, file_path, lines)
        visitor.visit(tree)
    
    def check_project_structure(self):
        """Check for missing important files"""
        important_files = {
            '.gitignore': 'MEDIUM',
            'requirements.txt': 'HIGH',
            'README.md': 'LOW',
            '.env.example': 'MEDIUM',
        }
        
        for file_name, severity in important_files.items():
            if not (self.project_path / file_name).exists():
                self.findings.append(Finding(
                    severity=severity,
                    category='Quality',
                    file='',
                    line=0,
                    issue=f'Missing {file_name}',
                    recommendation=f'Create {file_name} file'
                ))
        
        # Check if .env is tracked
        gitignore_path = self.project_path / '.gitignore'
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if '.env' not in gitignore_content:
                self.findings.append(Finding(
                    severity='CRITICAL',
                    category='Security',
                    file='.gitignore',
                    line=0,
                    issue='.env file not in .gitignore',
                    recommendation='Add .env to .gitignore to prevent committing secrets'
                ))
    
    def generate_report(self) -> str:
        """Generate formatted report"""
        report = ["=" * 80]
        report.append("🔍 BITUNIX CODE REVIEW REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        
        for finding in self.findings:
            by_severity[finding.severity] += 1
            by_category[finding.category] += 1
        
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Issues: {len(self.findings)}")
        report.append("")
        report.append("By Severity:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = by_severity.get(severity, 0)
            if count > 0:
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                report.append(f"  {emoji[severity]} {severity}: {count}")
        
        report.append("")
        report.append("By Category:")
        for category, count in sorted(by_category.items()):
            report.append(f"  • {category}: {count}")
        
        report.append("")
        report.append("=" * 80)
        report.append("📋 DETAILED FINDINGS")
        report.append("=" * 80)
        report.append("")
        
        # Detailed findings
        for i, finding in enumerate(self.findings, 1):
            emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(finding.severity, '⚪')
            
            report.append(f"{i}. {emoji} [{finding.severity}] {finding.category}")
            report.append(f"   File: {finding.file}:{finding.line}")
            report.append(f"   Issue: {finding.issue}")
            report.append(f"   Fix: {finding.recommendation}")
            if finding.code_snippet:
                report.append(f"   Code: {finding.code_snippet}")
            report.append("")
        
        report.append("=" * 80)
        report.append("✅ NEXT STEPS")
        report.append("=" * 80)
        report.append("")
        report.append("1. Fix CRITICAL issues immediately (security risks)")
        report.append("2. Address HIGH issues this week (major bugs/risks)")
        report.append("3. Plan MEDIUM issues for next sprint")
        report.append("4. Address LOW issues during refactoring")
        report.append("")
        
        return "\n".join(report)
    
    def save_json(self, output_path: str):
        """Save findings as JSON"""
        data = {
            'total_issues': len(self.findings),
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'findings': [asdict(f) for f in self.findings]
        }
        
        for finding in self.findings:
            data['by_severity'][finding.severity] += 1
            data['by_category'][finding.category] += 1
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 JSON report saved to: {output_path}")


def main():
    """Run code review"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated code review for Bitunix')
    parser.add_argument('path', nargs='?', default='.', help='Project path to review')
    parser.add_argument('--json', help='Save JSON report to file')
    parser.add_argument('--output', '-o', help='Save text report to file')
    
    args = parser.parse_args()
    
    reviewer = CodeReviewer(args.path)
    findings = reviewer.review()
    
    report = reviewer.generate_report()
    print(report)
    
    if args.json:
        reviewer.save_json(args.json)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"💾 Report saved to: {args.output}")
    
    # Exit with error code if critical issues found
    critical_count = sum(1 for f in findings if f.severity == 'CRITICAL')
    if critical_count > 0:
        print(f"\n⚠️  WARNING: {critical_count} CRITICAL issues found!")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
