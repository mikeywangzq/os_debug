"""
WebSocket Handler - WebSocket 事件处理

处理前端的 GDB 相关 WebSocket 请求
"""

import logging
from typing import Dict, Any, Optional
from flask_socketio import emit, join_room, leave_room
from .gdb_bridge import GDBBridge
from .gdb_monitor import GDBMonitor

logger = logging.getLogger(__name__)


class GDBSessionManager:
    """
    GDB 会话管理器

    管理多个 GDB 会话（每个 WebSocket 连接一个会话）
    """

    def __init__(self, socketio):
        """
        初始化会话管理器

        Args:
            socketio: Flask-SocketIO 实例
        """
        self.socketio = socketio
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str) -> bool:
        """
        创建新的 GDB 会话

        Args:
            session_id: 会话 ID（通常是 WebSocket session ID）

        Returns:
            bool: 创建成功返回 True
        """
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists")
            return False

        bridge = GDBBridge()
        monitor = GDBMonitor(bridge, self.socketio)

        self.sessions[session_id] = {
            'bridge': bridge,
            'monitor': monitor,
            'connected': False
        }

        logger.info(f"Created GDB session: {session_id}")
        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            dict: 会话对象，不存在返回 None
        """
        return self.sessions.get(session_id)

    def destroy_session(self, session_id: str):
        """
        销毁会话

        Args:
            session_id: 会话 ID
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        # 停止监控
        monitor: GDBMonitor = session['monitor']
        monitor.stop_monitoring()

        # 关闭 GDB
        bridge: GDBBridge = session['bridge']
        bridge.stop()

        # 删除会话
        del self.sessions[session_id]
        logger.info(f"Destroyed GDB session: {session_id}")

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有会话"""
        return self.sessions


def register_websocket_handlers(socketio, session_manager: GDBSessionManager):
    """
    注册 WebSocket 事件处理器

    Args:
        socketio: Flask-SocketIO 实例
        session_manager: 会话管理器
    """

    @socketio.on('connect')
    def handle_connect():
        """处理 WebSocket 连接"""
        from flask import request
        session_id = request.sid
        logger.info(f"WebSocket connected: {session_id}")

        # 创建 GDB 会话
        session_manager.create_session(session_id)

        # 加入房间（用于广播）
        join_room(session_id)

        emit('connected', {'session_id': session_id})

    @socketio.on('disconnect')
    def handle_disconnect():
        """处理 WebSocket 断开"""
        from flask import request
        session_id = request.sid
        logger.info(f"WebSocket disconnected: {session_id}")

        # 销毁会话
        session_manager.destroy_session(session_id)

        leave_room(session_id)

    @socketio.on('gdb_start')
    def handle_gdb_start(data: Dict[str, Any]):
        """
        处理启动 GDB 请求

        Args:
            data: {
                'gdb_args': ['-q', '--nx'],  // 可选的 GDB 参数
            }
        """
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        gdb_args = data.get('gdb_args', [])

        # 启动 GDB
        success = bridge.start(gdb_args)

        if success:
            logger.info(f"GDB started for session {session_id}")
            emit('gdb_started', {'success': True})
        else:
            logger.error(f"Failed to start GDB for session {session_id}")
            emit('gdb_started', {'success': False, 'error': 'Failed to start GDB'})

    @socketio.on('gdb_connect')
    def handle_gdb_connect(data: Dict[str, Any]):
        """
        处理连接到调试目标的请求

        Args:
            data: {
                'target': 'localhost:1234' | '/path/to/program' | '/path/to/core',
                'auto_monitor': true  // 是否自动启动监控
            }
        """
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        monitor: GDBMonitor = session['monitor']

        target = data.get('target')
        if not target:
            emit('gdb_connect_result', {
                'success': False,
                'error': 'Target not specified'
            })
            return

        # 如果 GDB 还未启动，先启动
        if not bridge.connected:
            bridge.start()

        # 连接到目标
        result = bridge.connect_to_target(target)

        if result.get('success'):
            session['connected'] = True

            # 启动监控（如果请求）
            auto_monitor = data.get('auto_monitor', True)
            if auto_monitor:
                monitor.start_monitoring()

            logger.info(f"Connected to target '{target}' for session {session_id}")

        emit('gdb_connect_result', result)

    @socketio.on('gdb_command')
    def handle_gdb_command(data: Dict[str, Any]):
        """
        处理执行 GDB 命令请求

        Args:
            data: {
                'command': 'backtrace',  // 命令
                'type': 'cli' | 'mi',    // 命令类型
                'args': {}               // 可选参数
            }
        """
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']

        if not bridge.connected:
            emit('command_result', {
                'success': False,
                'error': 'GDB not connected'
            })
            return

        command = data.get('command')
        cmd_type = data.get('type', 'cli')

        try:
            if cmd_type == 'cli':
                result = bridge.execute_cli_command(command)
            else:
                # MI 命令
                responses = bridge.execute_mi_command(command)
                result = {
                    'success': True,
                    'command': command,
                    'responses': responses
                }

            emit('command_result', result)

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            emit('command_result', {
                'success': False,
                'error': str(e)
            })

    @socketio.on('gdb_breakpoint')
    def handle_set_breakpoint(data: Dict[str, Any]):
        """
        处理设置断点请求

        Args:
            data: {
                'location': 'panic' | 'main.c:42' | '*0x80000000'
            }
        """
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        location = data.get('location')

        result = bridge.set_breakpoint(location)
        emit('breakpoint_result', result)

    @socketio.on('gdb_continue')
    def handle_continue():
        """处理继续执行请求"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        result = bridge.continue_execution()
        emit('continue_result', result)

    @socketio.on('gdb_step_over')
    def handle_step_over():
        """处理单步执行（跳过函数）"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        result = bridge.step_over()
        emit('step_result', result)

    @socketio.on('gdb_step_into')
    def handle_step_into():
        """处理单步执行（进入函数）"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        result = bridge.step_into()
        emit('step_result', result)

    @socketio.on('gdb_get_backtrace')
    def handle_get_backtrace():
        """处理获取调用栈请求"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        result = bridge.get_backtrace()
        emit('backtrace_result', result)

    @socketio.on('gdb_get_registers')
    def handle_get_registers():
        """处理获取寄存器请求"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        result = bridge.get_registers()
        emit('registers_result', result)

    @socketio.on('gdb_read_memory')
    def handle_read_memory(data: Dict[str, Any]):
        """
        处理读取内存请求

        Args:
            data: {
                'address': '0x80000000',
                'size': 256
            }
        """
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        address = data.get('address')
        size = data.get('size', 256)

        result = bridge.read_memory(address, size)
        emit('memory_result', result)

    @socketio.on('gdb_disconnect')
    def handle_gdb_disconnect():
        """处理断开 GDB 连接"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        bridge: GDBBridge = session['bridge']
        monitor: GDBMonitor = session['monitor']

        # 停止监控
        monitor.stop_monitoring()

        # 停止 GDB
        bridge.stop()

        session['connected'] = False

        emit('gdb_disconnected', {'success': True})
        logger.info(f"GDB disconnected for session {session_id}")

    @socketio.on('gdb_status')
    def handle_get_status():
        """处理获取状态请求"""
        from flask import request
        session_id = request.sid

        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        monitor: GDBMonitor = session['monitor']
        status = monitor.get_status()

        emit('status_result', status)

    logger.info("WebSocket handlers registered")
