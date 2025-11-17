"""
GDB Bridge - GDB 连接和命令执行模块

使用 pygdbmi 库与 GDB/MI 接口通信
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from pygdbmi.gdbcontroller import GdbController

logger = logging.getLogger(__name__)


class GDBBridge:
    """
    GDB 连接桥接器

    提供与 GDB 的双向通信能力，执行命令并解析结果
    """

    def __init__(self, gdb_path: str = 'gdb'):
        """
        初始化 GDB Bridge

        Args:
            gdb_path: GDB 可执行文件路径（默认从 PATH 查找）
        """
        self.gdb_path = gdb_path
        self.gdb_controller: Optional[GdbController] = None
        self.connected = False
        self.target_attached = False

    def start(self, gdb_args: List[str] = None) -> bool:
        """
        启动新的 GDB 进程

        Args:
            gdb_args: 传递给 GDB 的额外参数

        Returns:
            bool: 成功返回 True
        """
        try:
            args = gdb_args or []
            # 始终使用 MI 模式
            args = ['--interpreter=mi'] + args

            logger.info(f"Starting GDB: {self.gdb_path} {' '.join(args)}")

            self.gdb_controller = GdbController(
                command=[self.gdb_path] + args,
                time_to_check_for_additional_output_sec=0.1
            )

            self.connected = True
            logger.info("GDB started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start GDB: {e}")
            return False

    def connect_to_target(self, target: str) -> Dict[str, Any]:
        """
        连接到调试目标

        Args:
            target: 目标字符串，可以是：
                   - 可执行文件路径: /path/to/program
                   - 远程目标: localhost:1234
                   - 核心转储: /path/to/core

        Returns:
            dict: 连接结果
        """
        if not self.connected:
            return {'success': False, 'error': 'GDB not started'}

        try:
            # 判断目标类型
            if ':' in target:
                # 远程目标
                cmd = f'-target-select remote {target}'
                logger.info(f"Connecting to remote target: {target}")
            elif os.path.exists(target):
                # 本地文件
                cmd = f'-file-exec-and-symbols {target}'
                logger.info(f"Loading file: {target}")
            else:
                return {'success': False, 'error': f'Invalid target: {target}'}

            response = self.execute_mi_command(cmd)

            if self._is_success_response(response):
                self.target_attached = True
                return {'success': True, 'message': 'Connected to target'}
            else:
                error_msg = self._extract_error(response)
                return {'success': False, 'error': error_msg}

        except Exception as e:
            logger.error(f"Failed to connect to target: {e}")
            return {'success': False, 'error': str(e)}

    def execute_mi_command(self, command: str, timeout: float = 5.0) -> List[Dict]:
        """
        执行 GDB/MI 命令

        Args:
            command: MI 命令（如 -exec-run, -stack-list-frames）
            timeout: 超时时间（秒）

        Returns:
            list: MI 响应列表
        """
        if not self.gdb_controller:
            return [{'type': 'error', 'message': 'GDB not started'}]

        try:
            logger.debug(f"Executing MI command: {command}")
            responses = self.gdb_controller.write(
                command,
                timeout_sec=timeout,
                raise_error_on_timeout=False
            )

            logger.debug(f"Received {len(responses)} responses")
            return responses

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return [{'type': 'error', 'message': str(e)}]

    def execute_cli_command(self, command: str) -> Dict[str, Any]:
        """
        执行 GDB CLI 命令（通过 MI 的 -interpreter-exec）

        Args:
            command: CLI 命令（如 bt, info registers）

        Returns:
            dict: 解析后的结果
        """
        # 使用 MI 命令执行 CLI 命令
        mi_cmd = f'-interpreter-exec console "{command}"'
        responses = self.execute_mi_command(mi_cmd)

        # 提取输出
        output_lines = []
        for resp in responses:
            if resp.get('type') == 'console':
                payload = resp.get('payload', '')
                # 去除转义字符
                output_lines.append(payload.strip('"').replace('\\n', '\n'))

        return {
            'success': True,
            'command': command,
            'output': ''.join(output_lines)
        }

    def get_backtrace(self) -> Dict[str, Any]:
        """
        获取调用栈

        Returns:
            dict: 包含 frames 列表的结果
        """
        responses = self.execute_mi_command('-stack-list-frames')

        for resp in responses:
            if resp.get('message') == 'done':
                payload = resp.get('payload', {})
                frames = payload.get('stack', [])
                return {
                    'success': True,
                    'frames': frames
                }

        return {'success': False, 'frames': []}

    def get_registers(self) -> Dict[str, Any]:
        """
        获取寄存器值

        Returns:
            dict: 寄存器名到值的映射
        """
        # 获取所有寄存器的值（十六进制格式）
        responses = self.execute_mi_command('-data-list-register-values x')

        registers = {}
        for resp in responses:
            if resp.get('message') == 'done':
                payload = resp.get('payload', {})
                register_values = payload.get('register-values', [])

                for reg in register_values:
                    number = reg.get('number')
                    value = reg.get('value')
                    # 获取寄存器名称
                    name_resp = self.execute_mi_command(f'-data-list-register-names {number}')
                    for nr in name_resp:
                        if nr.get('message') == 'done':
                            names = nr.get('payload', {}).get('register-names', [])
                            if names:
                                registers[names[0]] = value

                return {'success': True, 'registers': registers}

        return {'success': False, 'registers': {}}

    def read_memory(self, address: str, size: int = 256) -> Dict[str, Any]:
        """
        读取内存

        Args:
            address: 内存地址（如 0x80000000）
            size: 读取字节数

        Returns:
            dict: 内存内容
        """
        cmd = f'-data-read-memory-bytes {address} {size}'
        responses = self.execute_mi_command(cmd)

        for resp in responses:
            if resp.get('message') == 'done':
                payload = resp.get('payload', {})
                memory = payload.get('memory', [])
                if memory:
                    return {
                        'success': True,
                        'address': memory[0].get('begin'),
                        'contents': memory[0].get('contents')
                    }

        return {'success': False, 'contents': ''}

    def set_breakpoint(self, location: str) -> Dict[str, Any]:
        """
        设置断点

        Args:
            location: 断点位置（函数名、文件:行号、地址）

        Returns:
            dict: 断点信息
        """
        cmd = f'-break-insert {location}'
        responses = self.execute_mi_command(cmd)

        for resp in responses:
            if resp.get('message') == 'done':
                payload = resp.get('payload', {})
                bkpt = payload.get('bkpt', {})
                return {
                    'success': True,
                    'number': bkpt.get('number'),
                    'address': bkpt.get('addr'),
                    'location': location
                }

        return {'success': False}

    def continue_execution(self) -> Dict[str, Any]:
        """继续执行程序"""
        responses = self.execute_mi_command('-exec-continue')
        return {'success': True, 'responses': responses}

    def step_over(self) -> Dict[str, Any]:
        """单步执行（跳过函数）"""
        responses = self.execute_mi_command('-exec-next')
        return {'success': True, 'responses': responses}

    def step_into(self) -> Dict[str, Any]:
        """单步执行（进入函数）"""
        responses = self.execute_mi_command('-exec-step')
        return {'success': True, 'responses': responses}

    def stop(self):
        """停止 GDB 进程"""
        if self.gdb_controller:
            logger.info("Stopping GDB")
            self.gdb_controller.exit()
            self.gdb_controller = None
            self.connected = False
            self.target_attached = False

    def _is_success_response(self, responses: List[Dict]) -> bool:
        """检查响应是否成功"""
        for resp in responses:
            if resp.get('message') == 'done':
                return True
            if resp.get('message') == 'error':
                return False
        return False

    def _extract_error(self, responses: List[Dict]) -> str:
        """从响应中提取错误信息"""
        for resp in responses:
            if resp.get('message') == 'error':
                payload = resp.get('payload', {})
                return payload.get('msg', 'Unknown error')
        return 'Unknown error'

    def __del__(self):
        """清理资源"""
        self.stop()
