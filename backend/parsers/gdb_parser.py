"""Parser for GDB output (backtrace, registers, etc.)."""

import re
from typing import Dict, List, Optional, Tuple


class GDBParser:
    """Parse GDB output including backtrace and register dumps."""

    @staticmethod
    def parse_backtrace(text: str) -> List[Dict[str, str]]:
        """
        Parse GDB backtrace output.

        Example input:
            #0  0x80100abc in panic () at kernel.c:42
            #1  0x80101234 in trap (tf=0x...) at trap.c:123

        Returns:
            List of frame dicts with keys: frame_num, addr, function, file, line
        """
        frames = []
        # Pattern: #<num> <addr> in <function> (...) at <file>:<line>
        pattern = r'#(\d+)\s+(?:0x)?([0-9a-fA-F]+)\s+in\s+([^\s(]+)\s*(?:\([^)]*\))?\s*(?:at\s+([^:]+):(\d+))?'

        for line in text.split('\n'):
            match = re.search(pattern, line)
            if match:
                frames.append({
                    'frame_num': int(match.group(1)),
                    'addr': match.group(2),
                    'function': match.group(3),
                    'file': match.group(4) if match.group(4) else 'unknown',
                    'line': match.group(5) if match.group(5) else 'unknown'
                })

        return frames

    @staticmethod
    def parse_registers(text: str, arch: str = 'auto') -> Dict[str, str]:
        """
        Parse GDB register dump.

        Example input:
            rax            0x0      0
            rip            0x80100abc       0x80100abc <panic+42>

        Returns:
            Dict mapping register names to values
        """
        registers = {}

        # Auto-detect architecture
        if arch == 'auto':
            if 'rax' in text or 'rip' in text:
                arch = 'x86_64'
            elif 'eax' in text or 'eip' in text:
                arch = 'x86_32'
            elif 'ra' in text or 'sp' in text and 'pc' in text:
                arch = 'riscv'

        # Pattern: <reg_name> <value> [additional info]
        pattern = r'(\w+)\s+(0x[0-9a-fA-F]+|\d+)'

        for line in text.split('\n'):
            match = re.search(pattern, line)
            if match:
                reg_name = match.group(1)
                reg_value = match.group(2)
                registers[reg_name] = reg_value

        return registers

    @staticmethod
    def parse_variable_print(text: str) -> Optional[Dict[str, any]]:
        """
        Parse GDB variable print output.

        Example:
            $1 = (struct trapframe *) 0x87ffe000
            $2 = {member1 = 0x10, member2 = 0x20}

        Returns:
            Parsed variable info
        """
        result = {}

        # Try to extract variable value
        value_pattern = r'\$\d+\s*=\s*(.+)'
        match = re.search(value_pattern, text)
        if match:
            result['raw_value'] = match.group(1).strip()

        # Try to extract pointer value
        ptr_pattern = r'\(([^)]+)\)\s*(0x[0-9a-fA-F]+)'
        match = re.search(ptr_pattern, text)
        if match:
            result['type'] = match.group(1)
            result['value'] = match.group(2)

        return result if result else None

    @staticmethod
    def detect_architecture(text: str) -> str:
        """Detect architecture from GDB output."""
        text_lower = text.lower()

        if 'rax' in text_lower or 'rip' in text_lower or 'rsp' in text_lower:
            return 'x86_64'
        elif 'eax' in text_lower or 'eip' in text_lower or 'esp' in text_lower:
            return 'x86_32'
        elif any(reg in text_lower for reg in ['ra', 'sp', 'gp', 'tp', 'pc', 'a0', 'a1', 's0', 's1']):
            return 'riscv'

        return 'unknown'
