"""Parser for trapframe/exception frame dumps."""

import re
from typing import Dict, Optional


class TrapframeParser:
    """Parse trapframe dumps from kernel crashes."""

    # x86 trap numbers
    X86_TRAPS = {
        0: 'Divide Error',
        1: 'Debug Exception',
        2: 'NMI',
        3: 'Breakpoint',
        4: 'Overflow',
        5: 'Bounds Check',
        6: 'Invalid Opcode',
        7: 'Device Not Available',
        8: 'Double Fault',
        9: 'Coprocessor Segment Overrun',
        10: 'Invalid TSS',
        11: 'Segment Not Present',
        12: 'Stack Exception',
        13: 'General Protection',
        14: 'Page Fault',
        16: 'Floating Point Error',
        17: 'Alignment Check',
        18: 'Machine Check',
        19: 'SIMD Floating Point Exception',
    }

    # RISC-V exception causes
    RISCV_EXCEPTIONS = {
        0: 'Instruction Address Misaligned',
        1: 'Instruction Access Fault',
        2: 'Illegal Instruction',
        3: 'Breakpoint',
        4: 'Load Address Misaligned',
        5: 'Load Access Fault',
        6: 'Store/AMO Address Misaligned',
        7: 'Store/AMO Access Fault',
        8: 'Environment Call from U-mode',
        9: 'Environment Call from S-mode',
        11: 'Environment Call from M-mode',
        12: 'Instruction Page Fault',
        13: 'Load Page Fault',
        15: 'Store/AMO Page Fault',
    }

    @staticmethod
    def parse_trapframe(text: str, arch: str = 'auto') -> Dict:
        """
        Parse trapframe structure dump.

        Returns dict with extracted fields like:
        - trap_no, err_code, eip/rip/pc, esp/rsp/sp, cr2/stval, etc.
        """
        trapframe = {}

        # Auto-detect architecture
        if arch == 'auto':
            if 'eip' in text.lower() or 'err' in text.lower():
                arch = 'x86_32'
            elif 'rip' in text.lower():
                arch = 'x86_64'
            elif 'sepc' in text.lower() or 'scause' in text.lower() or 'stval' in text.lower():
                arch = 'riscv'

        trapframe['arch'] = arch

        # Extract numeric values
        def extract_field(field_name: str) -> Optional[str]:
            # Pattern: field_name = 0x... or field_name: 0x... or field_name 0x... (space-separated)
            # Also match hex numbers without 0x prefix (common in x86 dumps)
            pattern = rf'{field_name}\s*[=:]?\s*(0x[0-9a-fA-F]+|[0-9a-fA-F]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Normalize: add 0x prefix if not present and looks like hex
                if not value.startswith('0x') and re.match(r'^[0-9a-fA-F]+$', value):
                    # Check if it's actually hex (contains a-f) or just decimal
                    if any(c in 'abcdefABCDEF' for c in value):
                        return '0x' + value
                return value
            return None

        if arch == 'x86_32' or arch == 'x86_64':
            # x86 trapframe fields
            trapframe['trap_no'] = extract_field(r'\btrap(?:no)?\b')
            trapframe['err_code'] = extract_field(r'\berr(?:_?code)?\b')
            trapframe['eip'] = extract_field(r'e?ip')
            trapframe['cs'] = extract_field(r'cs')
            trapframe['eflags'] = extract_field(r'eflags')
            trapframe['esp'] = extract_field(r'e?sp')
            trapframe['ss'] = extract_field(r'ss')
            trapframe['cr2'] = extract_field(r'cr2')

            # Also check for register dumps in trapframe
            for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp',
                       'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp']:
                val = extract_field(reg)
                if val:
                    trapframe[reg] = val

        elif arch == 'riscv':
            # RISC-V trapframe fields
            trapframe['scause'] = extract_field(r'scause')
            trapframe['stval'] = extract_field(r'stval')
            trapframe['sepc'] = extract_field(r'sepc')
            trapframe['ra'] = extract_field(r'\bra\b')
            trapframe['sp'] = extract_field(r'\bsp\b')
            trapframe['gp'] = extract_field(r'\bgp\b')
            trapframe['tp'] = extract_field(r'\btp\b')

            for i in range(8):
                for prefix in ['a', 's', 't']:
                    reg = f'{prefix}{i}'
                    val = extract_field(reg)
                    if val:
                        trapframe[reg] = val

        return trapframe

    @staticmethod
    def decode_x86_page_fault_error_code(err_code: int) -> Dict[str, any]:
        """
        Decode x86 page fault error code.

        Bits:
        - P (bit 0): 0 = not present, 1 = protection violation
        - W (bit 1): 0 = read, 1 = write
        - U (bit 2): 0 = kernel mode, 1 = user mode
        - R (bit 3): 0 = normal, 1 = reserved bit violation
        - I (bit 4): 0 = data access, 1 = instruction fetch
        """
        return {
            'present': bool(err_code & 0x1),
            'write': bool(err_code & 0x2),
            'user_mode': bool(err_code & 0x4),
            'reserved': bool(err_code & 0x8),
            'instruction_fetch': bool(err_code & 0x10),
            'raw': err_code
        }

    @staticmethod
    def get_trap_description(trap_no: int, arch: str) -> str:
        """Get human-readable trap description."""
        if arch in ['x86_32', 'x86_64']:
            return TrapframeParser.X86_TRAPS.get(trap_no, f'Unknown trap {trap_no}')
        elif arch == 'riscv':
            return TrapframeParser.RISCV_EXCEPTIONS.get(trap_no, f'Unknown exception {trap_no}')
        return f'Unknown trap {trap_no}'
