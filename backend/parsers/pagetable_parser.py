"""Parser for page table dumps."""

import re
from typing import Dict, List, Tuple, Optional


class PageTableParser:
    """Parse page table dumps and extract mappings."""

    @staticmethod
    def parse_page_table_entry(text: str, arch: str = 'auto') -> List[Dict]:
        """
        Parse page table entries.

        Example formats:
        x86: VA 0x0 -> PA 0x2000 (PTE: 0x2003) flags: P W U
        RISC-V: 0x0000000000000000 -> 0x0000000080000000 rwxu-

        Returns list of mappings with VA, PA, and flags.
        """
        mappings = []

        # Detect architecture
        if arch == 'auto':
            if 'rwx' in text.lower() or 'daguxwrv' in text.lower():
                arch = 'riscv'
            else:
                arch = 'x86'

        for line in text.split('\n'):
            mapping = {}

            # Try to extract VA -> PA mapping
            # Pattern 1: VA 0x... -> PA 0x... or 0x... -> 0x...
            va_pa_pattern = r'(?:VA\s+)?(0x[0-9a-fA-F]+)\s*(?:->|→)\s*(?:PA\s+)?(0x[0-9a-fA-F]+)'
            match = re.search(va_pa_pattern, line, re.IGNORECASE)

            if match:
                mapping['va'] = match.group(1)
                mapping['pa'] = match.group(2)

                # Extract flags
                if arch == 'x86':
                    # x86 flags: P (present), W (write), U (user), etc.
                    flags = []
                    if re.search(r'\bP\b', line):
                        flags.append('P')
                    if re.search(r'\bW\b', line):
                        flags.append('W')
                    if re.search(r'\bU\b', line):
                        flags.append('U')
                    if re.search(r'\bA\b', line):
                        flags.append('A')
                    if re.search(r'\bD\b', line):
                        flags.append('D')
                    if re.search(r'\bPS\b', line):
                        flags.append('PS')

                    mapping['flags'] = flags
                    mapping['present'] = 'P' in flags
                    mapping['writable'] = 'W' in flags
                    mapping['user'] = 'U' in flags

                elif arch == 'riscv':
                    # RISC-V flags: rwxu or daguxwrv format
                    flag_pattern = r'([r-][w-][x-][u-]|[daguxwrv-]+)'
                    flag_match = re.search(flag_pattern, line)
                    if flag_match:
                        flag_str = flag_match.group(1)
                        mapping['flags_raw'] = flag_str
                        mapping['readable'] = 'r' in flag_str
                        mapping['writable'] = 'w' in flag_str
                        mapping['executable'] = 'x' in flag_str
                        mapping['user'] = 'u' in flag_str
                        mapping['valid'] = 'v' in flag_str.lower()

                mapping['arch'] = arch
                mappings.append(mapping)

        return mappings

    @staticmethod
    def parse_pte_value(pte: int, arch: str) -> Dict:
        """
        Parse a raw PTE value and extract flag bits.

        Args:
            pte: Raw PTE value (integer)
            arch: 'x86_32', 'x86_64', or 'riscv'

        Returns:
            Dict with parsed flags
        """
        result = {'raw': hex(pte)}

        if arch in ['x86_32', 'x86_64']:
            # x86 PTE format
            result['present'] = bool(pte & 0x1)
            result['writable'] = bool(pte & 0x2)
            result['user'] = bool(pte & 0x4)
            result['write_through'] = bool(pte & 0x8)
            result['cache_disable'] = bool(pte & 0x10)
            result['accessed'] = bool(pte & 0x20)
            result['dirty'] = bool(pte & 0x40)
            result['page_size'] = bool(pte & 0x80)
            result['global'] = bool(pte & 0x100)

            # Extract physical address
            if arch == 'x86_32':
                result['phys_addr'] = pte & 0xFFFFF000
            else:  # x86_64
                result['phys_addr'] = pte & 0x000FFFFFFFFFF000

        elif arch == 'riscv':
            # RISC-V PTE format (Sv39/Sv48)
            result['valid'] = bool(pte & 0x1)
            result['readable'] = bool(pte & 0x2)
            result['writable'] = bool(pte & 0x4)
            result['executable'] = bool(pte & 0x8)
            result['user'] = bool(pte & 0x10)
            result['global'] = bool(pte & 0x20)
            result['accessed'] = bool(pte & 0x40)
            result['dirty'] = bool(pte & 0x80)

            # PPN (physical page number) is in bits 10-53
            result['ppn'] = (pte >> 10) & 0xFFFFFFFFFFF
            result['phys_addr'] = result['ppn'] << 12

        return result

    @staticmethod
    def extract_address_range(text: str) -> List[Tuple[str, str]]:
        """
        Extract virtual address ranges from text.

        Example: [0x0000 - 0x1000] or 0x0..0x1000

        Returns list of (start, end) tuples.
        """
        ranges = []

        # Pattern: [0x... - 0x...] or 0x...0x... or 0x...-0x...
        pattern = r'\[?(0x[0-9a-fA-F]+)\s*[-–.]+\s*(0x[0-9a-fA-F]+)\]?'

        for match in re.finditer(pattern, text):
            ranges.append((match.group(1), match.group(2)))

        return ranges
