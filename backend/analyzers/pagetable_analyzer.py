"""Analyzer for page table dumps."""

from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.pagetable_parser import PageTableParser


class PageTableAnalyzer:
    """Analyze page table dumps and check for common errors."""

    def __init__(self):
        self.parser = PageTableParser()

    def analyze(self, text: str) -> Dict:
        """
        Analyze page table dump.

        Returns dict with:
        - mappings (list of VA->PA mappings)
        - visualization
        - findings (errors/warnings)
        """
        result = {
            'mappings': [],
            'visualization': '',
            'findings': [],
            'summary': ''
        }

        # Parse page table entries
        mappings = self.parser.parse_page_table_entry(text)
        if not mappings:
            return result

        result['mappings'] = mappings

        # Generate visualization
        result['visualization'] = self._visualize_mappings(mappings)

        # Run checks for common errors
        self._check_for_errors(mappings, result)

        # Generate summary
        result['summary'] = f"Found {len(mappings)} page table mappings"

        return result

    def _visualize_mappings(self, mappings: List[Dict]) -> str:
        """Create text visualization of page table mappings."""
        lines = []
        lines.append("Page Table Mappings:")
        lines.append("=" * 80)

        for mapping in mappings:
            va = mapping.get('va', 'unknown')
            pa = mapping.get('pa', 'unknown')
            arch = mapping.get('arch', 'unknown')

            # Format flags
            if arch == 'x86':
                flags = mapping.get('flags', [])
                flags_str = ' '.join(flags) if flags else 'none'
                perm = []
                if 'W' in flags:
                    perm.append('write')
                else:
                    perm.append('read-only')
                if 'U' in flags:
                    perm.append('user')
                else:
                    perm.append('kernel')
                if not mapping.get('present', True):
                    perm.append('NOT PRESENT')

                perm_str = ', '.join(perm)

            elif arch == 'riscv':
                perm = []
                if mapping.get('readable'):
                    perm.append('R')
                if mapping.get('writable'):
                    perm.append('W')
                if mapping.get('executable'):
                    perm.append('X')
                if mapping.get('user'):
                    perm.append('U')
                else:
                    perm.append('S')  # Supervisor mode

                perm_str = ''.join(perm) if perm else 'none'
            else:
                perm_str = 'unknown'

            lines.append(f"  VA {va:16s} -> PA {pa:16s}  |  Permissions: {perm_str}")

        return '\n'.join(lines)

    def _check_for_errors(self, mappings: List[Dict], result: Dict):
        """Check page table mappings for common errors."""
        for mapping in mappings:
            arch = mapping.get('arch', 'unknown')
            va = mapping.get('va', 'unknown')
            pa = mapping.get('pa', 'unknown')

            try:
                va_int = int(va, 16) if va.startswith('0x') else int(va, 16)
            except (ValueError, AttributeError):
                continue

            if arch == 'x86':
                self._check_x86_mapping(mapping, va_int, result)
            elif arch == 'riscv':
                self._check_riscv_mapping(mapping, va_int, result)

    def _check_x86_mapping(self, mapping: Dict, va_int: int, result: Dict):
        """Check x86 page table mapping for errors."""
        flags = mapping.get('flags', [])
        present = mapping.get('present', True)
        writable = mapping.get('writable', False)
        user = mapping.get('user', False)
        va = mapping.get('va')

        # Check 1: Kernel space marked as user-accessible
        if va_int >= 0x80000000 and user:
            result['findings'].append({
                'severity': 'critical',
                'category': 'security_violation',
                'message': f"CRITICAL: Kernel address {va} is marked as user-accessible (U bit set)!\n"
                           f"  - This is a serious security vulnerability\n"
                           f"  - User programs can read/write kernel memory\n"
                           f"  - Kernel mappings should NOT have the U (user) bit set"
            })

        # Check 2: Kernel code marked as writable
        if 0x80100000 <= va_int < 0x80200000 and writable:
            result['findings'].append({
                'severity': 'high',
                'category': 'code_writable',
                'message': f"WARNING: Kernel code region {va} is marked as writable (W bit set)\n"
                           f"  - Code should generally be read-only for security\n"
                           f"  - This can enable code injection attacks\n"
                           f"  - Consider removing the W bit for executable pages"
            })

        # Check 3: Page not present
        if not present:
            result['findings'].append({
                'severity': 'info',
                'category': 'not_present',
                'message': f"Page at {va} is not present (P bit = 0)\n"
                           f"  - Accessing this address will trigger a page fault\n"
                           f"  - This may be intentional (demand paging, copy-on-write)\n"
                           f"  - Or it may indicate an incomplete page table setup"
            })

        # Check 4: User space marked as non-user
        if va_int < 0x80000000 and not user:
            result['findings'].append({
                'severity': 'warning',
                'category': 'user_space_kernel_only',
                'message': f"User space address {va} is marked as kernel-only (U bit = 0)\n"
                           f"  - User programs cannot access this address\n"
                           f"  - This will cause a page fault in user mode\n"
                           f"  - Make sure this is intentional"
            })

    def _check_riscv_mapping(self, mapping: Dict, va_int: int, result: Dict):
        """Check RISC-V page table mapping for errors."""
        readable = mapping.get('readable', False)
        writable = mapping.get('writable', False)
        executable = mapping.get('executable', False)
        user = mapping.get('user', False)
        valid = mapping.get('valid', True)
        va = mapping.get('va')

        # In RISC-V, kernel space is typically high addresses
        # Check for kernel space marked as user-accessible
        if va_int >= 0x80000000 and user:
            result['findings'].append({
                'severity': 'critical',
                'category': 'security_violation',
                'message': f"CRITICAL: Kernel address {va} is marked as user-accessible (U bit set)!\n"
                           f"  - This is a serious security vulnerability\n"
                           f"  - User programs can access kernel memory\n"
                           f"  - Kernel mappings should NOT have the U bit set"
            })

        # Check for writable + executable (W+X violation)
        if writable and executable:
            result['findings'].append({
                'severity': 'high',
                'category': 'wx_violation',
                'message': f"WARNING: Page {va} is both writable and executable (W+X)\n"
                           f"  - This violates the W^X security principle\n"
                           f"  - Pages should be either writable OR executable, not both\n"
                           f"  - This enables code injection attacks"
            })

        # Check for invalid page
        if not valid:
            result['findings'].append({
                'severity': 'info',
                'category': 'invalid_page',
                'message': f"Page at {va} is not valid (V bit = 0)\n"
                           f"  - Accessing this address will trigger a page fault\n"
                           f"  - This may be intentional or indicate incomplete setup"
            })

        # Check for page with no permissions
        if not readable and not writable and not executable and valid:
            result['findings'].append({
                'severity': 'warning',
                'category': 'no_permissions',
                'message': f"Page {va} is valid but has no R/W/X permissions\n"
                           f"  - This is likely a page table directory entry, not a leaf\n"
                           f"  - Or an error in permission setup"
            })
