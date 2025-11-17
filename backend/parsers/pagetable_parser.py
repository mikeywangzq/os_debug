"""页表转储解析器"""

import re
from typing import Dict, List, Tuple, Optional


class PageTableParser:
    """解析页表转储并提取虚拟地址到物理地址的映射"""

    @staticmethod
    def parse_page_table_entry(text: str, arch: str = 'auto') -> List[Dict]:
        """
        解析页表条目

        输入格式示例:
        x86:    VA 0x0 -> PA 0x2000 (PTE: 0x2003) flags: P W U
        RISC-V: 0x0000000000000000 -> 0x0000000080000000 rwxu-

        参数:
            text: 页表转储文本
            arch: 架构类型 ('auto', 'x86', 'riscv')

        返回:
            映射列表，每个映射包含虚拟地址(VA)、物理地址(PA)和标志位
        """
        mappings = []

        # 自动检测架构
        if arch == 'auto':
            if 'rwx' in text.lower() or 'daguxwrv' in text.lower():
                arch = 'riscv'
            else:
                arch = 'x86'

        # 逐行解析页表条目
        for line in text.split('\n'):
            mapping = {}

            # 尝试提取 VA -> PA 映射
            # 匹配模式: VA 0x... -> PA 0x... 或 0x... -> 0x...
            va_pa_pattern = r'(?:VA\s+)?(0x[0-9a-fA-F]+)\s*(?:->|→)\s*(?:PA\s+)?(0x[0-9a-fA-F]+)'
            match = re.search(va_pa_pattern, line, re.IGNORECASE)

            if match:
                mapping['va'] = match.group(1)  # 虚拟地址
                mapping['pa'] = match.group(2)  # 物理地址

                # 提取标志位
                if arch == 'x86':
                    # x86 标志位: P (present存在), W (write可写), U (user用户), 等
                    flags = []
                    if re.search(r'\bP\b', line):
                        flags.append('P')   # Present 页面存在
                    if re.search(r'\bW\b', line):
                        flags.append('W')   # Writable 可写
                    if re.search(r'\bU\b', line):
                        flags.append('U')   # User 用户可访问
                    if re.search(r'\bA\b', line):
                        flags.append('A')   # Accessed 已访问
                    if re.search(r'\bD\b', line):
                        flags.append('D')   # Dirty 已修改
                    if re.search(r'\bPS\b', line):
                        flags.append('PS')  # Page Size 页大小

                    mapping['flags'] = flags
                    mapping['present'] = 'P' in flags
                    mapping['writable'] = 'W' in flags
                    mapping['user'] = 'U' in flags

                elif arch == 'riscv':
                    # RISC-V 标志位格式: rwxu 或 daguxwrv
                    flag_pattern = r'([r-][w-][x-][u-]|[daguxwrv-]+)'
                    flag_match = re.search(flag_pattern, line)
                    if flag_match:
                        flag_str = flag_match.group(1)
                        mapping['flags_raw'] = flag_str
                        mapping['readable'] = 'r' in flag_str    # Readable 可读
                        mapping['writable'] = 'w' in flag_str    # Writable 可写
                        mapping['executable'] = 'x' in flag_str  # Executable 可执行
                        mapping['user'] = 'u' in flag_str        # User 用户可访问
                        mapping['valid'] = 'v' in flag_str.lower()  # Valid 有效

                mapping['arch'] = arch
                mappings.append(mapping)

        return mappings

    @staticmethod
    def parse_pte_value(pte: int, arch: str) -> Dict:
        """
        解析原始 PTE 值并提取标志位

        参数:
            pte: 原始页表条目值（整数）
            arch: 架构类型 ('x86_32', 'x86_64', 'riscv')

        返回:
            包含解析后标志位的字典
        """
        result = {'raw': hex(pte)}

        if arch in ['x86_32', 'x86_64']:
            # x86 PTE 格式位定义
            result['present'] = bool(pte & 0x1)        # 位0: 页面存在
            result['writable'] = bool(pte & 0x2)       # 位1: 可写
            result['user'] = bool(pte & 0x4)           # 位2: 用户可访问
            result['write_through'] = bool(pte & 0x8)  # 位3: 写穿透
            result['cache_disable'] = bool(pte & 0x10) # 位4: 禁用缓存
            result['accessed'] = bool(pte & 0x20)      # 位5: 已访问
            result['dirty'] = bool(pte & 0x40)         # 位6: 已修改
            result['page_size'] = bool(pte & 0x80)     # 位7: 页面大小
            result['global'] = bool(pte & 0x100)       # 位8: 全局页

            # 提取物理地址（页帧地址）
            if arch == 'x86_32':
                result['phys_addr'] = pte & 0xFFFFF000  # 32位: 位12-31
            else:  # x86_64
                result['phys_addr'] = pte & 0x000FFFFFFFFFF000  # 64位: 位12-51

        elif arch == 'riscv':
            # RISC-V PTE 格式 (Sv39/Sv48 分页模式)
            result['valid'] = bool(pte & 0x1)          # 位0: 有效
            result['readable'] = bool(pte & 0x2)       # 位1: 可读
            result['writable'] = bool(pte & 0x4)       # 位2: 可写
            result['executable'] = bool(pte & 0x8)     # 位3: 可执行
            result['user'] = bool(pte & 0x10)          # 位4: 用户可访问
            result['global'] = bool(pte & 0x20)        # 位5: 全局映射
            result['accessed'] = bool(pte & 0x40)      # 位6: 已访问
            result['dirty'] = bool(pte & 0x80)         # 位7: 已修改

            # PPN (物理页号) 位于位 10-53
            result['ppn'] = (pte >> 10) & 0xFFFFFFFFFFF
            result['phys_addr'] = result['ppn'] << 12  # 左移12位得到物理地址

        return result

    @staticmethod
    def extract_address_range(text: str) -> List[Tuple[str, str]]:
        """
        从文本中提取虚拟地址范围

        输入示例: [0x0000 - 0x1000] 或 0x0..0x1000

        参数:
            text: 包含地址范围的文本

        返回:
            (起始地址, 结束地址) 元组的列表
        """
        ranges = []

        # 匹配模式: [0x... - 0x...] 或 0x...0x... 或 0x...-0x...
        pattern = r'\[?(0x[0-9a-fA-F]+)\s*[-–.]+\s*(0x[0-9a-fA-F]+)\]?'

        for match in re.finditer(pattern, text):
            ranges.append((match.group(1), match.group(2)))

        return ranges
