"""
GDB Monitor - 实时监控 GDB 事件

在独立线程中监控 GDB 的异步事件（断点、崩溃、信号等）
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from .gdb_bridge import GDBBridge

logger = logging.getLogger(__name__)


class GDBMonitor:
    """
    GDB 事件监控器

    在后台线程中监控 GDB 事件，自动捕获崩溃信息并推送到前端
    """

    def __init__(self, bridge: GDBBridge, socketio=None):
        """
        初始化 GDB 监控器

        Args:
            bridge: GDB 桥接器实例
            socketio: Flask-SocketIO 实例（用于推送事件）
        """
        self.bridge = bridge
        self.socketio = socketio
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.event_callbacks: Dict[str, List[Callable]] = {
            'stopped': [],
            'breakpoint-hit': [],
            'signal-received': [],
            'exited': []
        }

    def start_monitoring(self):
        """开始监控（在独立线程中运行）"""
        if self.monitoring:
            logger.warning("Monitor already running")
            return False

        if not self.bridge.connected:
            logger.error("Cannot start monitoring: GDB not connected")
            return False

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="GDBMonitor"
        )
        self.monitor_thread.start()
        logger.info("GDB monitoring started")
        return True

    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            return

        logger.info("Stopping GDB monitoring")
        self.monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None

    def register_callback(self, event_type: str, callback: Callable):
        """
        注册事件回调函数

        Args:
            event_type: 事件类型（stopped, breakpoint-hit, signal-received, exited）
            callback: 回调函数，接收事件数据作为参数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    def _monitor_loop(self):
        """监控循环（在独立线程中运行）"""
        logger.info("Monitor loop started")

        while self.monitoring:
            try:
                # 检查 GDB 控制器是否还在运行
                if not self.bridge.gdb_controller:
                    logger.warning("GDB controller lost, stopping monitor")
                    break

                # 获取输出（非阻塞）
                responses = self.bridge.gdb_controller.get_gdb_response(
                    timeout_sec=0.5,
                    raise_error_on_timeout=False
                )

                # 处理响应
                for response in responses:
                    self._handle_response(response)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(0.1)  # 避免快速失败循环

        logger.info("Monitor loop stopped")
        self.monitoring = False

    def _handle_response(self, response: Dict[str, Any]):
        """
        处理 GDB 响应

        Args:
            response: GDB/MI 响应字典
        """
        msg_type = response.get('type')
        message = response.get('message')
        payload = response.get('payload', {})

        # 调试输出
        if msg_type == 'console':
            # 控制台输出（如打印语句）
            self._emit_event('console_output', {
                'text': payload
            })
        elif msg_type == 'log':
            # GDB 日志
            logger.debug(f"GDB log: {payload}")

        # 异步通知（重要事件）
        elif msg_type == 'notify':
            if message == 'stopped':
                # 程序停止事件
                self._on_stopped(payload)
            elif message == 'running':
                # 程序继续运行
                self._emit_event('running', payload)
            elif message == 'thread-created':
                # 线程创建
                self._emit_event('thread_created', payload)

        # 结果消息
        elif msg_type == 'result':
            # 命令执行结果（通常由 execute_mi_command 处理）
            pass

    def _on_stopped(self, payload: Dict[str, Any]):
        """
        处理程序停止事件

        Args:
            payload: 停止事件的负载数据
        """
        reason = payload.get('reason', 'unknown')
        logger.info(f"Program stopped: {reason}")

        # 触发回调
        for callback in self.event_callbacks['stopped']:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in stopped callback: {e}")

        # 根据停止原因处理
        if reason == 'breakpoint-hit':
            self._on_breakpoint_hit(payload)
        elif reason == 'signal-received':
            self._on_signal_received(payload)
        elif reason == 'exited-normally' or reason == 'exited':
            self._on_exited(payload)
        else:
            # 其他停止原因（如单步执行）
            self._auto_capture_state(reason)

    def _on_breakpoint_hit(self, payload: Dict[str, Any]):
        """
        处理断点命中事件

        Args:
            payload: 断点事件数据
        """
        bkptno = payload.get('bkptno', '?')
        logger.info(f"Breakpoint {bkptno} hit")

        # 触发回调
        for callback in self.event_callbacks['breakpoint-hit']:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in breakpoint-hit callback: {e}")

        # 自动捕获状态
        state = self._auto_capture_state('breakpoint')
        state['breakpoint_number'] = bkptno

        # 推送到前端
        self._emit_event('breakpoint_hit', state)

    def _on_signal_received(self, payload: Dict[str, Any]):
        """
        处理信号接收事件（如 SIGSEGV）

        Args:
            payload: 信号事件数据
        """
        signal_name = payload.get('signal-name', 'UNKNOWN')
        signal_meaning = payload.get('signal-meaning', '')
        logger.warning(f"Signal received: {signal_name} - {signal_meaning}")

        # 触发回调
        for callback in self.event_callbacks['signal-received']:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in signal-received callback: {e}")

        # 自动捕获完整调试信息
        state = self._auto_capture_state('signal')
        state['signal'] = {
            'name': signal_name,
            'meaning': signal_meaning
        }

        # 推送到前端（高优先级）
        self._emit_event('crash_detected', state)

    def _on_exited(self, payload: Dict[str, Any]):
        """
        处理程序退出事件

        Args:
            payload: 退出事件数据
        """
        exit_code = payload.get('exit-code', '0')
        logger.info(f"Program exited with code {exit_code}")

        # 触发回调
        for callback in self.event_callbacks['exited']:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in exited callback: {e}")

        # 推送到前端
        self._emit_event('program_exited', {
            'exit_code': exit_code
        })

    def _auto_capture_state(self, reason: str) -> Dict[str, Any]:
        """
        自动捕获程序状态

        在程序停止时自动抓取调用栈、寄存器等信息

        Args:
            reason: 停止原因

        Returns:
            dict: 捕获的状态信息
        """
        state = {
            'reason': reason,
            'timestamp': time.time()
        }

        try:
            # 获取调用栈
            bt_result = self.bridge.get_backtrace()
            if bt_result.get('success'):
                state['backtrace'] = bt_result.get('frames', [])

            # 获取寄存器
            reg_result = self.bridge.get_registers()
            if reg_result.get('success'):
                state['registers'] = reg_result.get('registers', {})

            # 如果是信号，获取当前帧的详细信息
            if reason == 'signal':
                frame_info = self.bridge.execute_cli_command('info frame')
                state['frame_info'] = frame_info.get('output', '')

        except Exception as e:
            logger.error(f"Error capturing state: {e}")
            state['capture_error'] = str(e)

        return state

    def _emit_event(self, event_name: str, data: Dict[str, Any]):
        """
        向前端发送事件

        Args:
            event_name: 事件名称
            data: 事件数据
        """
        if self.socketio:
            try:
                self.socketio.emit(f'gdb_{event_name}', data)
                logger.debug(f"Emitted event: gdb_{event_name}")
            except Exception as e:
                logger.error(f"Failed to emit event {event_name}: {e}")
        else:
            logger.debug(f"No socketio instance, event {event_name} not sent")

    def get_status(self) -> Dict[str, Any]:
        """
        获取监控器状态

        Returns:
            dict: 状态信息
        """
        return {
            'monitoring': self.monitoring,
            'gdb_connected': self.bridge.connected,
            'target_attached': self.bridge.target_attached,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False
        }
