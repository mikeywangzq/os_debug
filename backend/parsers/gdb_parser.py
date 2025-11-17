"""GDB 输出解析器（回溯、寄存器等）"""

import re
from typing import Dict, List, Optional, Tuple


class GDBParser:
    """解析 GDB 输出，包括回溯（backtrace）和寄存器转储"""

    @staticmethod
    def parse_backtrace(text: str) -> List[Dict[str, str]]:
        """
        解析 GDB 回溯输出

        输入示例:
            #0  0x80100abc in panic () at kernel.c:42
            #1  0x80101234 in trap (tf=0x...) at trap.c:123

        参数:
            text: GDB backtrace 命令的输出文本

        返回:
            帧列表，每个帧包含以下键: frame_num, addr, function, file, line
        """
        frames = []
        # 正则模式: #<帧号> <地址> in <函数名> (...) at <文件>:<行号>
        pattern = r'#(\d+)\s+(?:0x)?([0-9a-fA-F]+)\s+in\s+([^\s(]+)\s*(?:\([^)]*\))?\s*(?:at\s+([^:]+):(\d+))?'

        # 逐行匹配回溯信息
        for line in text.split('\n'):
            match = re.search(pattern, line)
            if match:
                frames.append({
                    'frame_num': int(match.group(1)),  # 栈帧编号
                    'addr': match.group(2),             # 指令地址
                    'function': match.group(3),         # 函数名
                    'file': match.group(4) if match.group(4) else 'unknown',  # 源文件
                    'line': match.group(5) if match.group(5) else 'unknown'   # 行号
                })

        return frames

    @staticmethod
    def parse_registers(text: str, arch: str = 'auto') -> Dict[str, str]:
        """
        解析 GDB 寄存器转储

        输入示例:
            rax            0x0      0
            rip            0x80100abc       0x80100abc <panic+42>

        参数:
            text: GDB info registers 命令的输出
            arch: 架构类型 ('auto', 'x86_64', 'x86_32', 'riscv')

        返回:
            寄存器名到值的映射字典
        """
        registers = {}

        # 自动检测架构
        if arch == 'auto':
            if 'rax' in text or 'rip' in text:
                arch = 'x86_64'
            elif 'eax' in text or 'eip' in text:
                arch = 'x86_32'
            elif 'ra' in text or 'sp' in text and 'pc' in text:
                arch = 'riscv'

        # 正则模式: <寄存器名> <值> [附加信息]
        pattern = r'(\w+)\s+(0x[0-9a-fA-F]+|\d+)'

        # 逐行提取寄存器名和值
        for line in text.split('\n'):
            match = re.search(pattern, line)
            if match:
                reg_name = match.group(1)   # 寄存器名称
                reg_value = match.group(2)  # 寄存器值
                registers[reg_name] = reg_value

        return registers

    @staticmethod
    def parse_variable_print(text: str) -> Optional[Dict[str, any]]:
        """
        解析 GDB 变量打印输出

        输入示例:
            $1 = (struct trapframe *) 0x87ffe000
            $2 = {member1 = 0x10, member2 = 0x20}

        参数:
            text: GDB print 命令的输出

        返回:
            解析后的变量信息字典，如果无法解析则返回 None
        """
        result = {}

        # 尝试提取变量值
        value_pattern = r'\$\d+\s*=\s*(.+)'
        match = re.search(value_pattern, text)
        if match:
            result['raw_value'] = match.group(1).strip()

        # 尝试提取指针值和类型
        ptr_pattern = r'\(([^)]+)\)\s*(0x[0-9a-fA-F]+)'
        match = re.search(ptr_pattern, text)
        if match:
            result['type'] = match.group(1)    # 指针类型（如 struct trapframe *）
            result['value'] = match.group(2)   # 指针地址值

        return result if result else None

    @staticmethod
    def detect_architecture(text: str) -> str:
        """
        从 GDB 输出中检测目标架构

        参数:
            text: GDB 输出文本

        返回:
            架构名称: 'x86_64', 'x86_32', 'riscv', 或 'unknown'
        """
        text_lower = text.lower()

        # 通过特定寄存器名称识别架构
        if 'rax' in text_lower or 'rip' in text_lower or 'rsp' in text_lower:
            return 'x86_64'  # 64位 x86 寄存器
        elif 'eax' in text_lower or 'eip' in text_lower or 'esp' in text_lower:
            return 'x86_32'  # 32位 x86 寄存器
        elif any(reg in text_lower for reg in ['ra', 'sp', 'gp', 'tp', 'pc', 'a0', 'a1', 's0', 's1']):
            return 'riscv'   # RISC-V 寄存器

        return 'unknown'
