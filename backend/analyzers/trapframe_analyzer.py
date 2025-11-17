"""陷阱帧/异常帧转储分析器"""

from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.trapframe_parser import TrapframeParser


class TrapframeAnalyzer:
    """分析陷阱帧转储并提供洞察"""

    def __init__(self):
        self.parser = TrapframeParser()

    def analyze(self, text: str) -> Dict:
        """
        分析陷阱帧转储

        参数:
            text: 陷阱帧转储文本

        返回:
            包含以下键的字典:
            - exception_info: 异常信息
            - error_code_analysis: 错误代码分析
            - findings: 发现的问题列表
        """
        result = {
            'exception_info': None,
            'error_code_analysis': None,
            'findings': [],
            'summary': ''
        }

        # Parse trapframe
        trapframe = self.parser.parse_trapframe(text)
        if not trapframe:
            return result

        arch = trapframe.get('arch', 'unknown')

        # Analyze exception type
        if arch in ['x86_32', 'x86_64']:
            self._analyze_x86_trapframe(trapframe, result)
        elif arch == 'riscv':
            self._analyze_riscv_trapframe(trapframe, result)

        return result

    def _analyze_x86_trapframe(self, tf: Dict, result: Dict):
        """Analyze x86 trapframe."""
        trap_no_str = tf.get('trap_no')
        if not trap_no_str:
            return

        try:
            trap_no = int(trap_no_str, 16) if trap_no_str.startswith('0x') else int(trap_no_str)
        except ValueError:
            return

        # Get trap description
        trap_desc = self.parser.get_trap_description(trap_no, tf['arch'])

        result['exception_info'] = {
            'trap_number': trap_no,
            'trap_name': trap_desc,
            'arch': tf['arch']
        }

        # Analyze Page Fault (trap 14)
        if trap_no == 14:
            self._analyze_page_fault_x86(tf, result)

        # Analyze General Protection Fault (trap 13)
        elif trap_no == 13:
            result['findings'].append({
                'severity': 'high',
                'category': 'general_protection',
                'message': "General Protection Fault detected. This usually indicates:\n"
                           "  - Accessing a segment with invalid permissions\n"
                           "  - Loading a null selector\n"
                           "  - Executing a privileged instruction in user mode\n"
                           "  - Writing to a read-only segment"
            })

        # Analyze Invalid Opcode (trap 6)
        elif trap_no == 6:
            eip = tf.get('eip', 'unknown')
            result['findings'].append({
                'severity': 'high',
                'category': 'invalid_opcode',
                'message': f"Invalid Opcode at EIP={eip}. This usually indicates:\n"
                           f"  - Jumping to invalid or corrupted code\n"
                           f"  - Executing data as code\n"
                           f"  - Function pointer corruption"
            })

        # Analyze Double Fault (trap 8)
        elif trap_no == 8:
            result['findings'].append({
                'severity': 'critical',
                'category': 'double_fault',
                'message': "Double Fault detected! This is a critical error that occurs when "
                           "the CPU fails to handle an exception (e.g., stack overflow in exception handler). "
                           "Check your interrupt/exception handlers and stack setup."
            })

        # Generate summary
        result['summary'] = f"Exception: {trap_desc} (trap #{trap_no})"

    def _analyze_page_fault_x86(self, tf: Dict, result: Dict):
        """Analyze x86 page fault in detail."""
        cr2 = tf.get('cr2')
        err_code_str = tf.get('err_code')
        eip = tf.get('eip', tf.get('rip'))

        if not cr2:
            return

        # Parse error code
        if err_code_str:
            try:
                err_code = int(err_code_str, 16) if err_code_str.startswith('0x') else int(err_code_str)
                err_info = self.parser.decode_x86_page_fault_error_code(err_code)

                result['error_code_analysis'] = {
                    'raw': hex(err_code),
                    'present': err_info['present'],
                    'write': err_info['write'],
                    'user_mode': err_info['user_mode'],
                    'reserved': err_info['reserved'],
                    'instruction_fetch': err_info['instruction_fetch'],
                    'description': self._format_error_code_description(err_info)
                }

                # Generate findings based on error code
                self._generate_page_fault_findings(cr2, err_info, eip, result)

            except ValueError:
                pass

    def _format_error_code_description(self, err_info: Dict) -> str:
        """Format page fault error code into human-readable description."""
        parts = []

        if err_info['present']:
            parts.append("Page is present but access violated permissions (protection fault)")
        else:
            parts.append("Page is not present (not mapped)")

        if err_info['write']:
            parts.append("Caused by a write operation")
        else:
            parts.append("Caused by a read operation")

        if err_info['user_mode']:
            parts.append("Occurred in user mode")
        else:
            parts.append("Occurred in kernel mode")

        if err_info['instruction_fetch']:
            parts.append("Caused by instruction fetch")

        if err_info['reserved']:
            parts.append("Reserved bit violation")

        return "\n".join(f"  - {part}" for part in parts)

    def _generate_page_fault_findings(self, cr2: str, err_info: Dict, eip: str, result: Dict):
        """Generate specific findings based on page fault details."""
        try:
            cr2_val = int(cr2, 16) if cr2.startswith('0x') else int(cr2)
        except ValueError:
            cr2_val = 0

        # Check for null pointer dereference
        if cr2_val < 0x1000:
            result['findings'].append({
                'severity': 'critical',
                'category': 'null_pointer',
                'message': f"Null pointer dereference detected! Faulting address CR2={cr2} is very close to 0x0.\n"
                           f"  - This typically means a null or uninitialized pointer was dereferenced.\n"
                           f"  - Check the code at EIP={eip} for pointer dereferences.\n"
                           f"  - Look for struct member accesses like `ptr->field` where ptr is NULL."
            })

        # User mode accessing kernel space
        elif err_info['user_mode'] and cr2_val >= 0x80000000:
            result['findings'].append({
                'severity': 'high',
                'category': 'user_kernel_access',
                'message': f"User mode attempted to access kernel space! CR2={cr2}\n"
                           f"  - User programs cannot access addresses >= 0x80000000\n"
                           f"  - This may be due to a bad pointer in user code\n"
                           f"  - Or a missing page table mapping"
            })

        # Kernel mode page fault
        elif not err_info['user_mode']:
            if err_info['present']:
                result['findings'].append({
                    'severity': 'high',
                    'category': 'kernel_protection_fault',
                    'message': f"Kernel mode protection fault at CR2={cr2}\n"
                               f"  - Attempted to {'write' if err_info['write'] else 'read'} a page without proper permissions\n"
                               f"  - Check if trying to write to a read-only kernel page\n"
                               f"  - Or accessing a user page without proper checks"
                })
            else:
                result['findings'].append({
                    'severity': 'high',
                    'category': 'kernel_page_not_present',
                    'message': f"Kernel accessed unmapped memory at CR2={cr2}\n"
                               f"  - This may be due to:\n"
                               f"    • Invalid pointer passed to kernel (e.g., from syscall)\n"
                               f"    • Kernel bug (accessing uninitialized pointer)\n"
                               f"    • Stack overflow\n"
                               f"  - Fault occurred at EIP={eip}"
                })

        # Write to read-only page
        elif err_info['present'] and err_info['write']:
            result['findings'].append({
                'severity': 'high',
                'category': 'write_to_readonly',
                'message': f"Attempted to write to a read-only page at CR2={cr2}\n"
                           f"  - The page is mapped but not writable\n"
                           f"  - Check page table permissions (W bit)\n"
                           f"  - Common in copy-on-write implementations"
            })

    def _analyze_riscv_trapframe(self, tf: Dict, result: Dict):
        """Analyze RISC-V trapframe."""
        scause_str = tf.get('scause')
        if not scause_str:
            return

        try:
            scause = int(scause_str, 16) if scause_str.startswith('0x') else int(scause_str)

            # Check if it's an interrupt (MSB set) or exception
            is_interrupt = (scause & 0x8000000000000000) != 0
            cause_code = scause & 0x7FFFFFFFFFFFFFFF

            if is_interrupt:
                result['exception_info'] = {
                    'type': 'interrupt',
                    'code': cause_code,
                    'description': f'Interrupt {cause_code}'
                }
            else:
                # It's an exception
                exception_desc = self.parser.get_trap_description(cause_code, 'riscv')
                result['exception_info'] = {
                    'type': 'exception',
                    'code': cause_code,
                    'description': exception_desc
                }

                # Analyze specific exceptions
                if cause_code in [12, 13, 15]:  # Page faults
                    self._analyze_page_fault_riscv(tf, cause_code, result)
                elif cause_code == 2:  # Illegal instruction
                    result['findings'].append({
                        'severity': 'high',
                        'category': 'illegal_instruction',
                        'message': "Illegal instruction exception. This usually indicates:\n"
                                   "  - Executing invalid or corrupted code\n"
                                   "  - Jumping to a data region\n"
                                   "  - Function pointer corruption"
                    })

            result['summary'] = f"Exception: {result['exception_info']['description']}"

        except ValueError:
            pass

    def _analyze_page_fault_riscv(self, tf: Dict, cause_code: int, result: Dict):
        """Analyze RISC-V page fault."""
        stval = tf.get('stval')
        sepc = tf.get('sepc')

        if not stval:
            return

        try:
            stval_val = int(stval, 16) if stval.startswith('0x') else int(stval)
        except ValueError:
            stval_val = 0

        fault_type = {
            12: 'instruction fetch',
            13: 'load (read)',
            15: 'store (write)'
        }.get(cause_code, 'unknown')

        # Check for null pointer
        if stval_val < 0x1000:
            result['findings'].append({
                'severity': 'critical',
                'category': 'null_pointer',
                'message': f"Null pointer dereference! Faulting address STVAL={stval}\n"
                           f"  - Attempted {fault_type} from address near 0x0\n"
                           f"  - Check code at SEPC={sepc} for null pointer usage"
            })
        else:
            result['findings'].append({
                'severity': 'high',
                'category': 'page_fault',
                'message': f"Page fault on {fault_type} at STVAL={stval}\n"
                           f"  - Page is not mapped or lacks proper permissions\n"
                           f"  - Fault occurred at SEPC={sepc}\n"
                           f"  - Check page table setup and permissions"
            })
