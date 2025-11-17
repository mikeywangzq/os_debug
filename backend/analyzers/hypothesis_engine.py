"""Hypothesis Engine - Integrates all analyzers to generate hypotheses."""

from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.gdb_analyzer import GDBAnalyzer
from analyzers.trapframe_analyzer import TrapframeAnalyzer
from analyzers.pagetable_analyzer import PageTableAnalyzer


class HypothesisEngine:
    """
    Intelligent hypothesis engine that combines all analyzers
    to generate prioritized hypotheses about debugging issues.
    """

    def __init__(self):
        self.gdb_analyzer = GDBAnalyzer()
        self.trapframe_analyzer = TrapframeAnalyzer()
        self.pagetable_analyzer = PageTableAnalyzer()

    def analyze(self, text: str) -> Dict:
        """
        Main analysis entry point.

        Runs all analyzers and generates a comprehensive report with hypotheses.
        """
        result = {
            'gdb_analysis': None,
            'trapframe_analysis': None,
            'pagetable_analysis': None,
            'hypotheses': [],
            'all_findings': [],
            'summary': ''
        }

        # Run individual analyzers
        gdb_result = self.gdb_analyzer.analyze(text)
        if gdb_result.get('findings') or gdb_result.get('backtrace_analysis'):
            result['gdb_analysis'] = gdb_result

        trapframe_result = self.trapframe_analyzer.analyze(text)
        if trapframe_result.get('exception_info'):
            result['trapframe_analysis'] = trapframe_result

        pagetable_result = self.pagetable_analyzer.analyze(text)
        if pagetable_result.get('mappings'):
            result['pagetable_analysis'] = pagetable_result

        # Collect all findings
        all_findings = []
        if result['gdb_analysis']:
            all_findings.extend(result['gdb_analysis'].get('findings', []))
        if result['trapframe_analysis']:
            all_findings.extend(result['trapframe_analysis'].get('findings', []))
        if result['pagetable_analysis']:
            all_findings.extend(result['pagetable_analysis'].get('findings', []))

        result['all_findings'] = all_findings

        # Generate hypotheses by correlating findings
        result['hypotheses'] = self._generate_hypotheses(
            result['gdb_analysis'],
            result['trapframe_analysis'],
            result['pagetable_analysis']
        )

        # Generate executive summary
        result['summary'] = self._generate_summary(result)

        return result

    def _generate_hypotheses(self, gdb_analysis, trapframe_analysis, pagetable_analysis) -> List[Dict]:
        """
        Generate prioritized hypotheses by correlating findings from all analyzers.
        """
        hypotheses = []

        # Scenario 1: Kernel null pointer dereference
        if self._detect_kernel_null_pointer(gdb_analysis, trapframe_analysis):
            hypotheses.append({
                'priority': 'high',
                'scenario': 'Kernel Null Pointer Dereference',
                'evidence': self._collect_null_pointer_evidence(gdb_analysis, trapframe_analysis),
                'explanation': (
                    "The kernel attempted to dereference a null or near-null pointer. "
                    "This is one of the most common bugs in OS development."
                ),
                'suggestions': [
                    "Check the backtrace to identify which function caused the panic/fault",
                    "Look for uninitialized pointers or missing null checks",
                    "Common culprits: struct member access (ptr->field) where ptr is NULL",
                    "Use GDB to print variables: p <variable_name>",
                    "Add assertions to validate pointers before dereferencing"
                ]
            })

        # Scenario 2: User program stack overflow
        if self._detect_user_stack_overflow(trapframe_analysis):
            hypotheses.append({
                'priority': 'high',
                'scenario': 'User Program Stack Overflow',
                'evidence': self._collect_stack_overflow_evidence(trapframe_analysis),
                'explanation': (
                    "The user program's stack grew beyond its allocated region, "
                    "causing a page fault when trying to access memory below the stack base."
                ),
                'suggestions': [
                    "Check for large local variables (e.g., char buf[8192]) in user program",
                    "Look for infinite recursion in user code",
                    "Verify that user stack size is sufficient",
                    "Check if USTACKSIZE is properly defined",
                    "Try reducing local variable sizes or moving them to heap"
                ]
            })

        # Scenario 3: Invalid syscall argument
        if self._detect_invalid_syscall_arg(gdb_analysis, trapframe_analysis):
            hypotheses.append({
                'priority': 'high',
                'scenario': 'Invalid System Call Argument',
                'evidence': self._collect_syscall_evidence(gdb_analysis, trapframe_analysis),
                'explanation': (
                    "A system call received an invalid pointer from user space. "
                    "The kernel tried to copy data from/to this address and faulted."
                ),
                'suggestions': [
                    "Check syscall argument validation (e.g., argaddr, argint functions)",
                    "Verify that copyin/copyout functions are being used correctly",
                    "Ensure user pointers are within valid user address range",
                    "Check for NULL pointers passed from user space",
                    "Validate that user buffers don't cross page boundaries incorrectly"
                ]
            })

        # Scenario 4: Page table misconfiguration
        if self._detect_pagetable_issue(pagetable_analysis, trapframe_analysis):
            hypotheses.append({
                'priority': 'high',
                'scenario': 'Page Table Misconfiguration',
                'evidence': self._collect_pagetable_evidence(pagetable_analysis, trapframe_analysis),
                'explanation': (
                    "The page tables are not set up correctly, causing improper memory access."
                ),
                'suggestions': [
                    "Review the page table setup code (mappages, walkpgdir, etc.)",
                    "Check that all required mappings are created (kernel, user, devices)",
                    "Verify permission bits are set correctly (P, W, U flags)",
                    "Ensure kernel mappings are NOT marked as user-accessible",
                    "Check that physical addresses are valid and properly aligned"
                ]
            })

        # Scenario 5: Write to read-only page (Copy-on-Write)
        if self._detect_write_to_readonly(trapframe_analysis):
            hypotheses.append({
                'priority': 'medium',
                'scenario': 'Write to Read-Only Page (Possible COW)',
                'evidence': self._collect_readonly_evidence(trapframe_analysis),
                'explanation': (
                    "Attempted to write to a read-only page. If implementing copy-on-write (COW), "
                    "this is expected and should be handled in the page fault handler."
                ),
                'suggestions': [
                    "If implementing COW: handle this in usertrap/trap handler",
                    "Allocate a new physical page",
                    "Copy contents from the old page to new page",
                    "Update page table to point to new page with write permissions",
                    "If NOT implementing COW: check why page is marked read-only"
                ]
            })

        # Scenario 6: General Protection Fault / Invalid Operation
        if self._detect_general_protection(trapframe_analysis):
            hypotheses.append({
                'priority': 'high',
                'scenario': 'General Protection Fault / Invalid Operation',
                'evidence': self._collect_general_protection_evidence(trapframe_analysis),
                'explanation': (
                    "A general protection fault indicates a privilege violation or invalid operation."
                ),
                'suggestions': [
                    "Check for user mode trying to execute privileged instructions",
                    "Verify segment selector values",
                    "Look for corrupted function pointers",
                    "Check for invalid memory accesses"
                ]
            })

        # Sort hypotheses by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        hypotheses.sort(key=lambda h: priority_order.get(h['priority'], 3))

        return hypotheses

    def _detect_kernel_null_pointer(self, gdb, trapframe) -> bool:
        """Detect kernel null pointer dereference pattern."""
        if not trapframe or not trapframe.get('exception_info'):
            return False

        # Check for page fault
        exception = trapframe['exception_info']
        is_page_fault = (
            exception.get('trap_name') == 'Page Fault' or
            exception.get('description', '').lower().find('page fault') != -1
        )

        if not is_page_fault:
            return False

        # Check if any finding mentions null pointer
        findings = trapframe.get('findings', [])
        for finding in findings:
            if finding.get('category') == 'null_pointer':
                return True

        return False

    def _detect_user_stack_overflow(self, trapframe) -> bool:
        """Detect user stack overflow pattern."""
        if not trapframe or not trapframe.get('exception_info'):
            return False

        findings = trapframe.get('findings', [])
        for finding in findings:
            if 'stack' in finding.get('message', '').lower():
                return True

        # Check if error code indicates user mode
        err_analysis = trapframe.get('error_code_analysis')
        if err_analysis and err_analysis.get('user_mode'):
            # Additional heuristic: check faulting address
            # (would need CR2/STVAL parsing)
            return True

        return False

    def _detect_invalid_syscall_arg(self, gdb, trapframe) -> bool:
        """Detect invalid syscall argument pattern."""
        if not gdb or not trapframe:
            return False

        # Check backtrace for syscall-related functions
        bt_analysis = gdb.get('backtrace_analysis')
        if bt_analysis:
            frames = bt_analysis.get('frames', [])
            syscall_funcs = ['syscall', 'usertrap', 'copyin', 'copyout', 'fetchstr', 'argaddr']
            for frame in frames:
                if any(func in frame.get('function', '').lower() for func in syscall_funcs):
                    # And it's a kernel mode page fault
                    err_analysis = trapframe.get('error_code_analysis')
                    if err_analysis and not err_analysis.get('user_mode'):
                        return True

        return False

    def _detect_pagetable_issue(self, pagetable, trapframe) -> bool:
        """Detect page table configuration issues."""
        if not pagetable:
            return False

        findings = pagetable.get('findings', [])
        critical_findings = [f for f in findings if f.get('severity') in ['critical', 'high']]

        return len(critical_findings) > 0

    def _detect_write_to_readonly(self, trapframe) -> bool:
        """Detect write to read-only page."""
        if not trapframe:
            return False

        findings = trapframe.get('findings', [])
        for finding in findings:
            if finding.get('category') == 'write_to_readonly':
                return True

        return False

    def _detect_general_protection(self, trapframe) -> bool:
        """Detect general protection fault."""
        if not trapframe:
            return False

        exception = trapframe.get('exception_info', {})
        return exception.get('trap_name') == 'General Protection'

    def _collect_null_pointer_evidence(self, gdb, trapframe) -> List[str]:
        """Collect evidence for null pointer hypothesis."""
        evidence = []

        if trapframe:
            findings = trapframe.get('findings', [])
            for finding in findings:
                if finding.get('category') == 'null_pointer':
                    evidence.append(f"Trapframe: {finding.get('message', '').split(chr(10))[0]}")

        if gdb:
            bt = gdb.get('backtrace_analysis', {})
            if bt.get('frames'):
                top_frame = bt['frames'][0]
                evidence.append(f"Crashed in: {top_frame.get('function')} at {top_frame.get('location')}")

        return evidence

    def _collect_stack_overflow_evidence(self, trapframe) -> List[str]:
        """Collect evidence for stack overflow hypothesis."""
        evidence = []
        if trapframe:
            err_analysis = trapframe.get('error_code_analysis', {})
            if err_analysis.get('user_mode'):
                evidence.append("Page fault occurred in user mode")
        return evidence

    def _collect_syscall_evidence(self, gdb, trapframe) -> List[str]:
        """Collect evidence for invalid syscall argument hypothesis."""
        evidence = []

        if gdb:
            bt = gdb.get('backtrace_analysis', {})
            frames = bt.get('frames', [])
            for frame in frames:
                func = frame.get('function', '')
                if any(s in func.lower() for s in ['syscall', 'copyin', 'copyout', 'trap']):
                    evidence.append(f"In syscall path: {func}")

        if trapframe:
            err_analysis = trapframe.get('error_code_analysis', {})
            if err_analysis and not err_analysis.get('user_mode'):
                evidence.append("Kernel mode page fault (kernel handling user data)")

        return evidence

    def _collect_pagetable_evidence(self, pagetable, trapframe) -> List[str]:
        """Collect evidence for page table hypothesis."""
        evidence = []

        if pagetable:
            findings = pagetable.get('findings', [])
            for finding in findings:
                if finding.get('severity') in ['critical', 'high']:
                    evidence.append(finding.get('message', '').split('\n')[0])

        return evidence

    def _collect_readonly_evidence(self, trapframe) -> List[str]:
        """Collect evidence for write-to-readonly hypothesis."""
        evidence = []
        if trapframe:
            err_analysis = trapframe.get('error_code_analysis', {})
            if err_analysis:
                if err_analysis.get('write') and err_analysis.get('present'):
                    evidence.append("Write operation to present page (protection violation)")
        return evidence

    def _collect_general_protection_evidence(self, trapframe) -> List[str]:
        """Collect evidence for general protection fault."""
        evidence = []
        if trapframe:
            exception = trapframe.get('exception_info', {})
            evidence.append(f"Exception: {exception.get('trap_name', 'Unknown')}")
        return evidence

    def _generate_summary(self, result: Dict) -> str:
        """Generate executive summary of the analysis."""
        parts = []

        if result.get('trapframe_analysis'):
            tf = result['trapframe_analysis']
            if tf.get('summary'):
                parts.append(tf['summary'])

        if result.get('gdb_analysis'):
            gdb = result['gdb_analysis']
            bt = gdb.get('backtrace_analysis', {})
            if bt.get('summary'):
                parts.append(bt['summary'])

        num_hypotheses = len(result.get('hypotheses', []))
        if num_hypotheses > 0:
            parts.append(f"Generated {num_hypotheses} hypothesis(es)")

        return '. '.join(parts) if parts else 'Analysis complete'
