# 🔥 实时 GDB 集成 - 使用指南

## 📖 概述

v2.0 新增的实时 GDB 集成功能让你能够：

- ⚡ **实时连接** 到正在运行的 GDB 会话
- 🔍 **自动捕获** 程序崩溃和异常信息
- 📊 **实时监控** 调用栈、寄存器状态
- 🎯 **交互式调试** 设置断点、单步执行
- 🤖 **智能分析** 自动分析崩溃原因并给出建议

## 🚀 快速开始

### 方式一：连接到远程 GDB（推荐 xv6/QEMU）

1. **启动你的 OS 内核调试环境**

   ```bash
   # 在 xv6 目录下，启动 QEMU 并等待 GDB 连接
   make qemu-gdb

   # 在另一个终端启动 GDB
   gdb-multiarch kernel/kernel
   (gdb) target remote localhost:1234
   ```

2. **启动调试助手**

   ```bash
   cd /path/to/os_debug
   python3 backend/app.py
   ```

3. **连接到 GDB**
   - 打开浏览器访问 http://localhost:5000
   - 点击 "⚡ Real-time GDB" 标签页
   - 在 Target 输入框中输入 `localhost:1234`
   - 点击 "Connect" 按钮

4. **开始调试**
   - 点击 "Continue" 继续执行程序
   - 当程序崩溃时，系统会自动捕获信息并分析

### 方式二：调试本地程序

1. **准备可执行文件**

   ```bash
   # 编译带调试符号的程序
   gcc -g -o myprogram myprogram.c
   ```

2. **在 UI 中连接**
   - Target: `/path/to/myprogram`
   - 点击 "Connect"

3. **设置断点并运行**
   - 在 "Breakpoint location" 输入 `main`
   - 点击 "Set Breakpoint"
   - 点击 "Continue" 运行程序

## 📋 功能详解

### 自动崩溃检测

当程序发生崩溃（如 SIGSEGV、页面错误）时：

1. **自动捕获**
   - 调用栈（backtrace）
   - 寄存器状态
   - 当前帧信息

2. **自动分析**
   - 调用静态分析器分析崩溃原因
   - 生成假设和建议
   - 实时显示在界面上

3. **可视化展示**
   - 彩色高亮显示错误类型
   - 时间戳标记
   - 结构化的信息展示

### 交互式调试命令

#### 控制命令

- **Continue**: 继续执行程序直到下一个断点或崩溃
- **Step Over**: 单步执行（跳过函数调用）
- **Step Into**: 单步执行（进入函数）

#### 信息命令

- **Get Backtrace**: 获取当前调用栈
- **Get Registers**: 获取所有寄存器值

#### 断点管理

支持多种断点位置格式：

```
panic              # 函数名
main.c:42          # 文件:行号
*0x80000000        # 内存地址
```

### 实时输出

所有 GDB 的输出都会实时显示在界面上：

- 🔵 **Info**: 一般信息（程序运行、命令执行）
- 🟢 **Success**: 成功操作（连接成功、断点设置）
- 🟡 **Warning**: 警告信息（断点命中）
- 🔴 **Error**: 错误信息（连接失败、命令错误）
- ⚠️ **Crash**: 崩溃检测（自动高亮）

## 🎯 典型使用场景

### 场景 1: 调试 xv6 内核崩溃

```bash
# 终端 1: 启动 xv6
cd xv6-riscv
make qemu-gdb

# 终端 2: 启动 GDB
riscv64-linux-gnu-gdb kernel/kernel
(gdb) target remote localhost:1234

# 终端 3: 启动调试助手
cd os_debug
python3 backend/app.py

# 浏览器:
# 1. 连接到 localhost:1234
# 2. 点击 Continue
# 3. 在 xv6 shell 中触发崩溃（如运行有问题的用户程序）
# 4. 系统自动捕获并分析崩溃信息
```

### 场景 2: 调试特定函数

```bash
# 在 UI 中：
1. 连接到 GDB
2. 设置断点: "panic" 或 "trap.c:67"
3. 点击 Continue
4. 当断点命中时：
   - 查看 Backtrace
   - 查看 Registers
   - Step Into/Over 跟踪代码执行
```

### 场景 3: 分析页表问题

```bash
# 当检测到页面错误时：
1. 系统自动显示：
   - 错误地址 (stval/cr2)
   - 访问类型（读/写/执行）
   - 权限信息
2. 手动执行命令查看页表：
   - 在 GDB 命令行：(gdb) info mem
   - 或使用原有的静态分析功能粘贴页表输出
```

## 🔧 高级配置

### 自定义 GDB 参数

修改 `backend/gdb/gdb_bridge.py` 中的启动参数：

```python
def start(self, gdb_args: List[str] = None) -> bool:
    args = gdb_args or []
    # 添加自定义参数
    args += ['--quiet', '--nx']  # 静默模式，不加载 .gdbinit
```

### 调整超时时间

在 `backend/gdb/gdb_bridge.py` 中：

```python
def execute_mi_command(self, command: str, timeout: float = 5.0):
    # 修改 timeout 参数以适应较慢的操作
```

### 禁用自动监控

如果你想手动控制监控：

```javascript
// 在 frontend/gdb_client.js 中修改
this.socket.emit('gdb_connect', {
    target: target,
    auto_monitor: false  // 禁用自动监控
});
```

## 📊 架构说明

### 数据流

```
浏览器 (WebSocket)
    ↓↑
Flask-SocketIO
    ↓↑
GDB Session Manager
    ↓↑
GDB Monitor (后台线程)
    ↓↑
GDB Bridge (pygdbmi)
    ↓↑
GDB/MI Interface
    ↓↑
GDB 进程
    ↓↑
目标程序 (xv6/QEMU)
```

### 核心组件

1. **GDB Bridge** (`backend/gdb/gdb_bridge.py`)
   - 与 GDB/MI 接口通信
   - 执行命令并解析结果

2. **GDB Monitor** (`backend/gdb/gdb_monitor.py`)
   - 在独立线程中监控事件
   - 自动捕获崩溃信息

3. **WebSocket Handler** (`backend/gdb/websocket_handler.py`)
   - 处理前端请求
   - 管理多个会话

4. **GDB Client** (`frontend/gdb_client.js`)
   - WebSocket 通信
   - UI 更新和事件处理

## ⚠️ 注意事项

### 安全性

- 默认只允许 localhost 连接
- 不支持执行危险的 shell 命令
- 每个 WebSocket 连接独立的 GDB 会话

### 限制

- 需要 GDB 7.0+ (支持 MI v2)
- 一个会话同时只能连接一个 GDB 实例
- 超长输出可能被截断（最大 1MB）

### 常见问题

**Q: 连接失败 "Failed to start GDB"**
- 确保系统已安装 GDB
- 检查 GDB 路径：`which gdb`
- 对于交叉编译环境，可能需要 `gdb-multiarch`

**Q: 无法连接到 remote target**
- 确保 QEMU/gdbserver 已启动
- 检查端口是否正确（默认 1234）
- 尝试手动连接：`gdb -ex "target remote localhost:1234"`

**Q: 断点不生效**
- 确保程序带有调试符号（-g 编译）
- 检查函数名拼写
- 尝试使用地址：`*0x80000000`

**Q: 自动分析没有触发**
- 检查浏览器控制台是否有错误
- 确保静态分析 API 正常工作
- 尝试手动在 "Static Analysis" 标签页分析

## 🎓 教学建议

### 对于教师

1. **课堂演示**
   - 实时展示内核调试过程
   - 让学生看到崩溃的实时分析
   - 演示如何逐步追踪 bug

2. **作业指导**
   - 要求学生使用实时调试功能
   - 提交调试过程的截图
   - 记录崩溃分析结果

### 对于学生

1. **学习路径**
   - 先使用静态分析熟悉工具
   - 然后尝试实时调试简单程序
   - 最后调试完整的 OS 内核

2. **最佳实践**
   - 始终设置 panic 断点
   - 崩溃后立即查看 backtrace
   - 结合静态分析和实时调试

## 📚 参考资源

- [GDB/MI 协议文档](https://sourceware.org/gdb/onlinedocs/gdb/GDB_002fMI.html)
- [pygdbmi 库文档](https://github.com/cs01/pygdbmi)
- [Flask-SocketIO 文档](https://flask-socketio.readthedocs.io/)
- [xv6 调试指南](https://pdos.csail.mit.edu/6.828/)

## 🤝 反馈与贡献

遇到问题或有改进建议？

- 提交 Issue 描述问题
- 查看 `docs/GDB_INTEGRATION_DESIGN.md` 了解技术细节
- 贡献代码改进功能

---

**v2.0** | 实时 GDB 集成 | 让 OS 调试更简单 🚀
