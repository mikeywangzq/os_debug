"""陷阱帧/异常帧转储解析器"""

import re
from typing import Dict, Optional


class TrapframeParser:
    """解析内核崩溃时的陷阱帧（Trapframe）转储信息"""

    # x86 架构陷阱编号映射表
    X86_TRAPS = {
        0: 'Divide Error',                    # 除法错误
        1: 'Debug Exception',                 # 调试异常
        2: 'NMI',                             # 不可屏蔽中断
        3: 'Breakpoint',                      # 断点
        4: 'Overflow',                        # 溢出
        5: 'Bounds Check',                    # 边界检查
        6: 'Invalid Opcode',                  # 无效操作码
        7: 'Device Not Available',            # 设备不可用
        8: 'Double Fault',                    # 双重错误
        9: 'Coprocessor Segment Overrun',     # 协处理器段溢出
        10: 'Invalid TSS',                    # 无效 TSS
        11: 'Segment Not Present',            # 段不存在
        12: 'Stack Exception',                # 栈异常
        13: 'General Protection',             # 一般保护错误
        14: 'Page Fault',                     # 页面错误（最常见）
        16: 'Floating Point Error',           # 浮点错误
        17: 'Alignment Check',                # 对齐检查
        18: 'Machine Check',                  # 机器检查
        19: 'SIMD Floating Point Exception',  # SIMD 浮点异常
    }

    # RISC-V 异常原因码映射表
    RISCV_EXCEPTIONS = {
        0: 'Instruction Address Misaligned',    # 指令地址未对齐
        1: 'Instruction Access Fault',          # 指令访问错误
        2: 'Illegal Instruction',               # 非法指令
        3: 'Breakpoint',                        # 断点
        4: 'Load Address Misaligned',           # 加载地址未对齐
        5: 'Load Access Fault',                 # 加载访问错误
        6: 'Store/AMO Address Misaligned',      # 存储/原子操作地址未对齐
        7: 'Store/AMO Access Fault',            # 存储/原子操作访问错误
        8: 'Environment Call from U-mode',      # 用户模式环境调用（系统调用）
        9: 'Environment Call from S-mode',      # 管理员模式环境调用
        11: 'Environment Call from M-mode',     # 机器模式环境调用
        12: 'Instruction Page Fault',           # 指令页面错误
        13: 'Load Page Fault',                  # 加载页面错误
        15: 'Store/AMO Page Fault',             # 存储/原子操作页面错误
    }

    @staticmethod
    def parse_trapframe(text: str, arch: str = 'auto') -> Dict:
        """
        解析陷阱帧结构转储

        参数:
            text: 陷阱帧转储文本
            arch: 架构类型 ('auto', 'x86_32', 'x86_64', 'riscv')

        返回:
            包含提取字段的字典，如：
            - trap_no（陷阱编号）, err_code（错误码）
            - eip/rip/pc（程序计数器）, esp/rsp/sp（栈指针）
            - cr2/stval（故障地址）等
        """
        trapframe = {}

        # 自动检测架构类型
        if arch == 'auto':
            if 'eip' in text.lower() or 'err' in text.lower():
                arch = 'x86_32'
            elif 'rip' in text.lower():
                arch = 'x86_64'
            elif 'sepc' in text.lower() or 'scause' in text.lower() or 'stval' in text.lower():
                arch = 'riscv'

        trapframe['arch'] = arch

        # 提取数值字段的辅助函数
        def extract_field(field_name: str) -> Optional[str]:
            """
            从文本中提取指定字段的值

            匹配模式: field_name = 0x... 或 field_name: 0x...
            """
            pattern = rf'{field_name}\s*[=:]\s*(0x[0-9a-fA-F]+|\d+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
            return None

        if arch == 'x86_32' or arch == 'x86_64':
            # 提取 x86 陷阱帧字段
            trapframe['trap_no'] = extract_field(r'trap(?:no)?')      # 陷阱编号
            trapframe['err_code'] = extract_field(r'err(?:_?code)?')  # 错误代码
            trapframe['eip'] = extract_field(r'e?ip')                 # 指令指针
            trapframe['cs'] = extract_field(r'cs')                    # 代码段
            trapframe['eflags'] = extract_field(r'eflags')            # 标志寄存器
            trapframe['esp'] = extract_field(r'e?sp')                 # 栈指针
            trapframe['ss'] = extract_field(r'ss')                    # 栈段
            trapframe['cr2'] = extract_field(r'cr2')                  # 故障地址（页面错误时）

            # 同时检查陷阱帧中的通用寄存器
            for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp',
                       'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp']:
                val = extract_field(reg)
                if val:
                    trapframe[reg] = val

        elif arch == 'riscv':
            # 提取 RISC-V 陷阱帧字段
            trapframe['scause'] = extract_field(r'scause')  # 异常原因
            trapframe['stval'] = extract_field(r'stval')    # 故障地址/非法指令
            trapframe['sepc'] = extract_field(r'sepc')      # 异常程序计数器
            trapframe['ra'] = extract_field(r'\bra\b')      # 返回地址
            trapframe['sp'] = extract_field(r'\bsp\b')      # 栈指针
            trapframe['gp'] = extract_field(r'\bgp\b')      # 全局指针
            trapframe['tp'] = extract_field(r'\btp\b')      # 线程指针

            # 提取参数、保存和临时寄存器
            for i in range(8):
                for prefix in ['a', 's', 't']:  # a=参数, s=保存, t=临时
                    reg = f'{prefix}{i}'
                    val = extract_field(reg)
                    if val:
                        trapframe[reg] = val

        return trapframe

    @staticmethod
    def decode_x86_page_fault_error_code(err_code: int) -> Dict[str, any]:
        """
        解码 x86 页面错误的错误代码

        错误代码位定义:
        - P (bit 0): 0 = 页面不存在, 1 = 保护违规
        - W (bit 1): 0 = 读操作, 1 = 写操作
        - U (bit 2): 0 = 内核模式, 1 = 用户模式
        - R (bit 3): 0 = 正常, 1 = 保留位违规
        - I (bit 4): 0 = 数据访问, 1 = 指令获取

        参数:
            err_code: 错误代码整数值

        返回:
            包含各位标志的字典
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
        """
        获取陷阱编号的人类可读描述

        参数:
            trap_no: 陷阱编号
            arch: 架构类型 ('x86_32', 'x86_64', 'riscv')

        返回:
            陷阱/异常的描述字符串
        """
        if arch in ['x86_32', 'x86_64']:
            return TrapframeParser.X86_TRAPS.get(trap_no, f'未知陷阱 {trap_no}')
        elif arch == 'riscv':
            return TrapframeParser.RISCV_EXCEPTIONS.get(trap_no, f'未知异常 {trap_no}')
        return f'未知陷阱 {trap_no}'
