"""Analyzer for GDB output."""

from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.gdb_parser import GDBParser


class GDBAnalyzer:
    """Analyze GDB output and provide insights."""

    def __init__(self):
        self.parser = GDBParser()

    def analyze(self, text: str) -> Dict:
        """
        Analyze GDB output (backtrace, registers, etc.).

        Returns a dict with:
        - backtrace_analysis
        - register_analysis
        - findings (list of issues/insights)
        """
        result = {
            'backtrace_analysis': None,
            'register_analysis': None,
            'findings': [],
            'arch': 'unknown'
        }

        # Detect architecture
        arch = self.parser.detect_architecture(text)
        result['arch'] = arch

        # Parse and analyze backtrace
        backtrace = self.parser.parse_backtrace(text)
        if backtrace:
            result['backtrace_analysis'] = self._analyze_backtrace(backtrace)

        # Parse and analyze registers
        registers = self.parser.parse_registers(text, arch)
        if registers:
            result['register_analysis'] = self._analyze_registers(registers, arch)

        # Collect all findings
        if result['backtrace_analysis']:
            result['findings'].extend(result['backtrace_analysis'].get('findings', []))
        if result['register_analysis']:
            result['findings'].extend(result['register_analysis'].get('findings', []))

        return result

    def _analyze_backtrace(self, backtrace: List[Dict]) -> Dict:
        """Analyze backtrace for common patterns."""
        analysis = {
            'frames': [],
            'findings': [],
            'summary': ''
        }

        for frame in backtrace:
            frame_info = {
                'num': frame['frame_num'],
                'function': frame['function'],
                'location': f"{frame['file']}:{frame['line']}" if frame['file'] != 'unknown' else 'unknown',
                'addr': frame['addr'],
                'description': ''
            }

            # Generate human-readable description
            if frame['file'] != 'unknown':
                frame_info['description'] = (
                    f"Frame #{frame['frame_num']}: Program stopped in function `{frame['function']}()` "
                    f"at {frame['file']}:{frame['line']} (address 0x{frame['addr']})"
                )
            else:
                frame_info['description'] = (
                    f"Frame #{frame['frame_num']}: In function `{frame['function']}()` "
                    f"at address 0x{frame['addr']}"
                )

            analysis['frames'].append(frame_info)

        # Check for panic/assert patterns
        function_names = [f['function'] for f in backtrace]

        if 'panic' in function_names:
            idx = function_names.index('panic')
            if idx + 1 < len(backtrace):
                caller = backtrace[idx + 1]
                analysis['findings'].append({
                    'severity': 'high',
                    'category': 'panic',
                    'message': f"Kernel panic detected. Called from `{caller['function']}()` "
                               f"in {caller['file']}:{caller['line']}. "
                               f"Check this function for assertion failures or explicit panic calls."
                })
            else:
                analysis['findings'].append({
                    'severity': 'high',
                    'category': 'panic',
                    'message': "Kernel panic detected. This indicates a fatal error was detected."
                })

        if any(name in function_names for name in ['assert', '__assert_fail', 'assertion']):
            analysis['findings'].append({
                'severity': 'high',
                'category': 'assertion',
                'message': "Assertion failure detected. Check the assertion condition that failed."
            })

        # Generate summary
        if backtrace:
            top_frame = backtrace[0]
            analysis['summary'] = (
                f"Program crashed in `{top_frame['function']}()`. "
                f"Backtrace has {len(backtrace)} frame(s)."
            )

        return analysis

    def _analyze_registers(self, registers: Dict[str, str], arch: str) -> Dict:
        """Analyze register values for suspicious patterns."""
        analysis = {
            'registers': {},
            'findings': [],
            'summary': ''
        }

        # Convert register values to integers for analysis
        reg_values = {}
        for name, value in registers.items():
            try:
                reg_values[name] = int(value, 16) if value.startswith('0x') else int(value)
            except ValueError:
                continue

        # Architecture-specific analysis
        if arch == 'x86_64':
            self._analyze_x86_64_registers(reg_values, analysis)
        elif arch == 'x86_32':
            self._analyze_x86_32_registers(reg_values, analysis)
        elif arch == 'riscv':
            self._analyze_riscv_registers(reg_values, analysis)

        # Store formatted register info
        for name, value in registers.items():
            analysis['registers'][name] = {
                'value': value,
                'description': self._get_register_description(name, value, arch)
            }

        return analysis

    def _analyze_x86_64_registers(self, regs: Dict[str, int], analysis: Dict):
        """Analyze x86-64 specific registers."""
        # Check instruction pointer
        if 'rip' in regs:
            rip = regs['rip']
            if rip == 0 or rip == 0xdeadbeef or rip == 0xcccccccc:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_ip',
                    'message': f"Invalid instruction pointer (RIP = 0x{rip:x}). "
                               f"This likely indicates memory corruption or an invalid function pointer."
                })

        # Check stack pointer
        if 'rsp' in regs:
            rsp = regs['rsp']
            if rsp == 0:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_sp',
                    'message': "Stack pointer (RSP) is null. Stack is corrupted."
                })

        # Check for null pointers in commonly dereferenced registers
        for reg in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi']:
            if reg in regs and regs[reg] == 0:
                analysis['findings'].append({
                    'severity': 'warning',
                    'category': 'null_pointer',
                    'message': f"Register {reg.upper()} is 0x0 (NULL). "
                               f"If this register is being dereferenced, it will cause a segmentation fault."
                })

    def _analyze_x86_32_registers(self, regs: Dict[str, int], analysis: Dict):
        """Analyze x86-32 specific registers."""
        # Check instruction pointer
        if 'eip' in regs:
            eip = regs['eip']
            if eip == 0 or eip == 0xdeadbeef or eip == 0xcccccccc:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_ip',
                    'message': f"Invalid instruction pointer (EIP = 0x{eip:x}). "
                               f"This likely indicates memory corruption or an invalid function pointer."
                })

        # Check stack pointer
        if 'esp' in regs:
            esp = regs['esp']
            if esp == 0:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_sp',
                    'message': "Stack pointer (ESP) is null. Stack is corrupted."
                })

        # Check for null pointers
        for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi']:
            if reg in regs and regs[reg] == 0:
                analysis['findings'].append({
                    'severity': 'warning',
                    'category': 'null_pointer',
                    'message': f"Register {reg.upper()} is 0x0 (NULL). "
                               f"If this register is being dereferenced, it will cause a segmentation fault."
                })

    def _analyze_riscv_registers(self, regs: Dict[str, int], analysis: Dict):
        """Analyze RISC-V specific registers."""
        # Check program counter
        if 'pc' in regs or 'sepc' in regs:
            pc = regs.get('pc', regs.get('sepc', 0))
            if pc == 0 or pc == 0xdeadbeef:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_pc',
                    'message': f"Invalid program counter (PC = 0x{pc:x}). "
                               f"This likely indicates memory corruption or an invalid function pointer."
                })

        # Check stack pointer
        if 'sp' in regs:
            sp = regs['sp']
            if sp == 0:
                analysis['findings'].append({
                    'severity': 'critical',
                    'category': 'invalid_sp',
                    'message': "Stack pointer (SP) is null. Stack is corrupted."
                })

        # Check argument/saved registers for null
        for i in range(8):
            for prefix in ['a', 's']:
                reg = f'{prefix}{i}'
                if reg in regs and regs[reg] == 0:
                    analysis['findings'].append({
                        'severity': 'info',
                        'category': 'null_value',
                        'message': f"Register {reg} is 0x0 (NULL/zero)."
                    })

    def _get_register_description(self, name: str, value: str, arch: str) -> str:
        """Get human-readable description of a register."""
        descriptions = {
            # x86-64
            'rax': 'Accumulator register (return value)',
            'rbx': 'Base register',
            'rcx': 'Counter register',
            'rdx': 'Data register',
            'rsi': 'Source index (2nd argument)',
            'rdi': 'Destination index (1st argument)',
            'rbp': 'Base pointer (frame pointer)',
            'rsp': 'Stack pointer',
            'rip': 'Instruction pointer (program counter)',
            # x86-32
            'eax': 'Accumulator register (return value)',
            'ebx': 'Base register',
            'ecx': 'Counter register',
            'edx': 'Data register',
            'esi': 'Source index',
            'edi': 'Destination index',
            'ebp': 'Base pointer (frame pointer)',
            'esp': 'Stack pointer',
            'eip': 'Instruction pointer (program counter)',
            # RISC-V
            'ra': 'Return address',
            'sp': 'Stack pointer',
            'gp': 'Global pointer',
            'tp': 'Thread pointer',
            'pc': 'Program counter',
            'a0': 'Argument/return value 0',
            'a1': 'Argument/return value 1',
            's0': 'Saved register 0 / frame pointer',
            's1': 'Saved register 1',
        }

        desc = descriptions.get(name.lower(), name.upper())
        return f"{desc} = {value}"
