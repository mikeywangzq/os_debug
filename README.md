<div align="center">

# 🔍 OS 调试助手

### 操作系统课程的智能调试伴侣

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

*几秒内将神秘的内核崩溃转化为可操作的见解*

**📚 [文档中心](docs/README.md)** | **🚀 [快速开始](#-快速开始)** | **📖 [使用指南](#-使用指南)** | **💡 [示例场景](#-真实场景示例)**

---

### 🔥 v2.0 新功能：实时 GDB 集成

<table>
<tr>
<td width="50%" align="center">
<img src="https://img.icons8.com/fluency/96/connection-sync.png" width="80"/>
<h4>实时连接</h4>
<p>直接连接到运行中的 GDB 会话</p>
</td>
<td width="50%" align="center">
<img src="https://img.icons8.com/fluency/96/speed.png" width="80"/>
<h4>自动分析</h4>
<p>崩溃时自动捕获并分析</p>
</td>
</tr>
<tr>
<td width="50%" align="center">
<img src="https://img.icons8.com/fluency/96/bug.png" width="80"/>
<h4>交互式调试</h4>
<p>设置断点、单步执行、查看状态</p>
</td>
<td width="50%" align="center">
<img src="https://img.icons8.com/fluency/96/real-time-sync.png" width="80"/>
<h4>实时监控</h4>
<p>WebSocket 推送调试信息</p>
</td>
</tr>
</table>

**🎓 v2.0 快速体验**:
```bash
# 1. 安装依赖
pip3 install -r backend/requirements.txt

# 2. 测试 GDB 集成
python3 test_gdb_integration.py

# 3. 启动服务器
python3 backend/app.py

# 4. 浏览器访问 http://localhost:5000
# 5. 点击 "⚡ Real-time GDB" 标签页开始使用！
```

**📖 详细文档**: [使用指南](docs/GDB_INTEGRATION_GUIDE.md) • [技术设计](docs/GDB_INTEGRATION_DESIGN.md) • [发布说明](V2.0_RELEASE_NOTES.md)

---

</div>

## 🎯 为什么需要 OS 调试助手？

<table>
<tr>
<td width="50%">

### ❌ 传统的 OS 调试方式
- 😫 盯着十六进制转储数小时
- 🤯 难以理解的 GDB 寄存器输出
- 📚 海量的页表转储信息
- ❓ 从崩溃到修复没有清晰路径
- 🔄 学生反复犯同样的错误

</td>
<td width="50%">

### ✅ 使用 OS 调试助手
- ⚡ 瞬间分析崩溃转储
- 🎯 人类可读的解释说明
- 🔍 自动检测错误模式
- 💡 按优先级排序的修复建议
- 📈 学习调试最佳实践

</td>
</tr>
</table>

---

## 🌟 核心功能

<table>
<tr>
<td width="25%" align="center">
<img src="https://img.icons8.com/fluency/96/stack.png" width="64"/>
<h3>GDB 分析</h3>
<p>解析回溯、分析寄存器、检测空指针</p>
</td>
<td width="25%" align="center">
<img src="https://img.icons8.com/fluency/96/error.png" width="64"/>
<h3>异常解码器</h3>
<p>解码陷阱帧、错误码、故障地址</p>
</td>
<td width="25%" align="center">
<img src="https://img.icons8.com/fluency/96/memory-slot.png" width="64"/>
<h3>页表检查器</h3>
<p>可视化映射、检测安全违规</p>
</td>
<td width="25%" align="center">
<img src="https://img.icons8.com/fluency/96/artificial-intelligence.png" width="64"/>
<h3>智能假设</h3>
<p>AI 驱动的根因分析</p>
</td>
</tr>
</table>

### 🔬 详细能力

#### 1️⃣ **GDB 输出分析**
```python
✓ 解析并人性化显示栈回溯
✓ 分析寄存器值的可疑模式
✓ 检测空指针（0x0, 0xdeadbeef）
✓ 识别无效的指令/栈指针
✓ 识别 panic() 和断言失败
```

#### 2️⃣ **陷阱帧/异常分析**
```python
✓ 解码陷阱编号（x86: 0-19, RISC-V 异常）
✓ 解析 x86 和 RISC-V 异常帧
✓ 解码缺页错误码（P/W/U/R/I 位）
✓ 提取故障地址（CR2/STVAL）
✓ 区分内核态与用户态故障
```

#### 3️⃣ **页表安全扫描器**
```python
✓ 可视化 VA → PA 映射
✓ 检测内核页面标记为用户可访问（严重！）
✓ 发现可写代码页（W^X 违规）
✓ 检查缺失的 Present 位
✓ 验证权限一致性
```

#### 4️⃣ **智能假设引擎**
核心亮点 - 关联所有发现以生成优先级排序的理论：

| 假设类型 | 触发条件 | 优先级 |
|---------|---------|---------|
| 🎯 空指针解引用 | 故障地址 < 0x1000 | 高 |
| 📚 栈溢出 | 用户态故障靠近栈基址 | 高 |
| 🔐 无效系统调用参数 | copyin/copyout 中内核故障 | 高 |
| ⚙️ 页表配置错误 | 检测到安全违规 | 严重 |
| 📝 写时复制故障 | 写入只读的已存在页 | 中 |
| ⚠️ 一般保护故障 | 陷阱 13，权限违规 | 高 |

---

## 🚀 快速开始

### ⚡ 一键启动
```bash
# 克隆并运行
git clone https://github.com/yourusername/os_debug.git
cd os_debug
chmod +x run.sh
./run.sh
```

### 📦 手动安装

<details>
<summary><b>点击展开详细步骤</b></summary>

**前置要求：**
- Python 3.7 或更高版本
- pip 包管理器

**步骤 1：克隆仓库**
```bash
git clone https://github.com/yourusername/os_debug.git
cd os_debug
```

**步骤 2：安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

**步骤 3：测试后端**
```bash
cd ..
python3 test_analyzer.py
```

**步骤 4：启动 Web 服务器**
```bash
cd backend
python app.py
```

**步骤 5：打开浏览器**
```
🌐 http://localhost:5000
```

**步骤 6：测试实时 GDB 功能（v2.0 新增）**
```bash
# 测试 GDB 集成
python3 test_gdb_integration.py

# 确保系统已安装 GDB
gdb --version

# 对于 RISC-V/ARM 等架构，可能需要
apt-get install gdb-multiarch
```

**可选：启用 AI 增强**
```bash
# 安装 AI 依赖（可选）
pip install openai  # 或 anthropic

# 设置 API 密钥
export OPENAI_API_KEY="your-key-here"
export ENABLE_AI=true

# 重启服务器
python app.py
```
查看 [AI_SETUP.md](AI_SETUP.md) 了解详细配置。

</details>

---

## 📖 使用指南

### 🎯 两种使用模式

**OS 调试助手提供两种互补的调试模式：**

<table>
<tr>
<th width="50%">📝 静态分析模式</th>
<th width="50%">⚡ 实时 GDB 模式</th>
</tr>
<tr>
<td>

**适用场景：**
- 分析已有的调试输出
- 事后分析崩溃日志
- 快速检查页表/寄存器

**工作流程：**
1. 复制调试输出
2. 粘贴到工具
3. 点击分析
4. 获得见解

</td>
<td>

**适用场景：** (v2.0 新增)
- 实时调试运行中的程序
- 交互式单步调试
- 自动捕获崩溃

**工作流程：**
1. 连接到 GDB
2. 设置断点
3. 运行程序
4. 自动分析崩溃

</td>
</tr>
</table>

---

### 🎬 静态分析：简单的 3 步工作流

```mermaid
graph LR
    A[📋 复制调试输出] --> B[📝 粘贴到工具]
    B --> C[🔍 点击分析]
    C --> D[💡 获得见解]
```

1. **复制** GDB、QEMU 或内核崩溃的调试输出
2. **粘贴** 到 Web 界面
3. **分析** 并立即获得专家见解

### 📥 支持的输入类型

<table>
<tr>
<th>输入类型</th>
<th>示例命令</th>
<th>显示内容</th>
</tr>
<tr>
<td>🔙 GDB 回溯</td>
<td><code>(gdb) bt</code></td>
<td>函数调用栈</td>
</tr>
<tr>
<td>🔢 GDB 寄存器</td>
<td><code>(gdb) info registers</code></td>
<td>CPU 寄存器状态</td>
</tr>
<tr>
<td>💥 陷阱帧</td>
<td>QEMU 崩溃输出</td>
<td>异常详情</td>
</tr>
<tr>
<td>🗺️ 页表</td>
<td>自定义转储函数</td>
<td>内存映射</td>
</tr>
</table>

### 🖥️ 架构支持矩阵

| 架构 | 状态 | 常见于 |
|-----|------|--------|
| 🔵 x86-32 | ✅ 完全支持 | xv6-x86, Pintos |
| 🔷 x86-64 | ✅ 完全支持 | 现代系统 |
| 🟢 RISC-V | ✅ 完全支持 | xv6-riscv |
| 🔶 ARM | ⏳ 计划中 | 未来版本 |
| 🟠 MIPS | ⏳ 计划中 | 未来版本 |

### ⚡ 实时 GDB 快速示例 (v2.0)

**场景：调试 xv6 内核崩溃**

```bash
# 终端 1: 启动 xv6 调试环境
cd xv6-riscv
make qemu-gdb

# 终端 2: 启动 GDB
riscv64-linux-gnu-gdb kernel/kernel
(gdb) target remote localhost:1234

# 浏览器: http://localhost:5000
# 1. 点击 "⚡ Real-time GDB" 标签
# 2. Target: localhost:1234
# 3. 点击 "Connect" - 状态变为绿色 ✓
# 4. 点击 "Set Breakpoint" - 输入 "panic"
# 5. 点击 "Continue"
# 6. 在 xv6 中触发错误
# 7. 🎉 系统自动捕获并分析！
```

**输出效果：**
- 🟢 实时显示连接状态
- 🔴 自动检测到 SIGSEGV
- 📊 自动显示调用栈和寄存器
- 🤖 自动生成假设和建议
- ⚡ 全程无需手动复制粘贴！

👉 [查看完整 GDB 使用教程](docs/GDB_INTEGRATION_GUIDE.md)

---

## 💡 真实场景示例

### 🐛 场景 1：空指针解引用

<table>
<tr><td width="50%">

**输入（来自 GDB）：**
```gdb
scause: 0x000000000000000d
stval:  0x0000000000000000
sepc:   0x80003456

#0 panic() at kernel.c:127
#1 kerneltrap() at trap.c:141
#2 mycpu() at proc.c:67
```

</td><td width="50%">

**输出（分析结果）：**
```
🎯 假设：内核空指针解引用
   优先级：高

📊 证据：
   ✓ STVAL 寄存器 = 0x0（NULL）
   ✓ 加载页面错误（scause 13）
   ✓ 在 mycpu() 函数中崩溃

💡 建议：
   1. 检查 mycpu() 中的 ptr->field 访问
   2. 验证 struct proc 初始化
   3. 在解引用前添加 NULL 检查
```

</td></tr>
</table>

### 🔐 场景 2：安全漏洞

<table>
<tr><td width="50%">

**输入（页表转储）：**
```
VA 0x80000000 -> PA 0x80000000
Flags: P W U

VA 0x80001000 -> PA 0x80001000
Flags: P W U
```

</td><td width="50%">

**输出（分析结果）：**
```
🚨 严重：检测到安全违规！

⚠️ 问题：内核内存用户可访问
   地址：0x80000000（内核空间）
   标志：U 位已设置（用户可访问）

💥 影响：
   → 用户程序可以读取内核内存
   → 用户程序可以写入内核内存
   → 可能导致系统完全沦陷

🔧 修复：从内核映射中移除 U 标志
```

</td></tr>
</table>

### 📚 场景 3：栈溢出

<table>
<tr><td width="50%">

**输入（x86 陷阱帧）：**
```
trap 14 (Page Fault)
err code: 6 (U=1, W=1, P=0)
cr2: 0x00003fb0
eip: 0x80104f3a

In user mode
```

</td><td width="50%">

**输出（分析结果）：**
```
🎯 假设：用户栈溢出
   优先级：高

📊 证据：
   ✓ 用户态页面错误
   ✓ 写入未映射页面
   ✓ 地址接近典型栈基址

💡 根本原因：
   • 大型局部变量（char buf[8192]）
   • 无限递归
   • 栈大小不足

🔧 解决方案：
   1. 减小局部变量大小
   2. 将缓冲区移到堆上
   3. 检查递归调用
   4. 增加 USTACKSIZE
```

</td></tr>
</table>

---

## 🏗️ 系统架构

### 📐 系统设计

```
┌─────────────────────────────────────────────────────────┐
│                  Web 浏览器（UI）                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │   输入面板     │  │   分析按钮     │  │   输出面板  │ │
│  └────────────────┘  └────────────────┘  └────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/JSON
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Flask 后端（Python）                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │         假设引擎（大脑 🧠）                     │    │
│  └──────┬────────────┬────────────┬─────────────────┘   │
│         │            │            │                      │
│    ┌────▼────┐  ┌───▼────┐  ┌───▼────┐                 │
│    │   GDB   │  │  陷阱  │  │  页表  │                 │
│    │  分析器 │  │  分析器│  │  分析器│                 │
│    └────┬────┘  └───┬────┘  └───┬────┘                 │
│         │           │           │                        │
│    ┌────▼────┐  ┌───▼────┐  ┌───▼────┐                 │
│    │   GDB   │  │  陷阱  │  │  页表  │                 │
│    │  解析器 │  │  解析器│  │  解析器│                 │
│    └─────────┘  └────────┘  └────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### 📁 项目结构

```
os_debug/
│
├── 🎨 frontend/                  # Web 界面
│   ├── index.html               # 主页面
│   ├── style.css                # 精美样式
│   └── app.js                   # 前端逻辑
│
├── 🧠 backend/                   # 分析引擎
│   ├── analyzers/               # 核心分析模块
│   │   ├── gdb_analyzer.py      # GDB 输出分析
│   │   ├── trapframe_analyzer.py # 异常分析
│   │   ├── pagetable_analyzer.py # 内存映射检查
│   │   └── hypothesis_engine.py  # 智能假设生成
│   │
│   ├── parsers/                 # 文本解析工具
│   │   ├── gdb_parser.py        # 解析 GDB 格式
│   │   ├── trapframe_parser.py  # 解析异常转储
│   │   └── pagetable_parser.py  # 解析页表
│   │
│   ├── app.py                   # Flask Web 服务器
│   └── requirements.txt         # Python 依赖
│
├── 📚 examples/                  # 示例调试场景
│   ├── example1_null_pointer.txt
│   ├── example2_page_table.txt
│   └── example3_x86_pagefault.txt
│
├── 🧪 test_analyzer.py          # 自动化测试套件
├── 🚀 run.sh                    # 快速启动脚本
└── 📖 README.md                 # 本文件
```

---

## 🧪 测试与质量

### ✅ 运行测试

```bash
python3 test_analyzer.py
```

**预期输出：**
```
================================================================================
测试 1：空指针解引用（RISC-V）
================================================================================
✓ 摘要：程序在 `panic()` 中崩溃。回溯有 3 个帧。
✓ 检测到空指针模式
✓ 生成了假设

================================================================================
测试 2：页表配置错误
================================================================================
✓ 发现 4 个页表映射
✓ 检测到 2 个严重安全违规
✓ 生成了详细警告

================================================================================
所有测试成功完成！✨
================================================================================
```

### 🎓 尝试内置示例

1. 启动 Web 服务器
2. 点击 **"加载示例"** 按钮
3. 查看真实崩溃分析效果

---

## 🎯 适用人群

<table>
<tr>
<td width="33%" align="center">
<h3>🎓 学生</h3>
<p>学习操作系统课程，例如：</p>
<ul align="left">
<li>MIT 6.S081 (xv6)</li>
<li>Stanford CS140 (Pintos)</li>
<li>MIT 6.828 (JOS)</li>
<li>Harvard CS161 (OS161)</li>
</ul>
</td>
<td width="33%" align="center">
<h3>👨‍🏫 助教</h3>
<p>优势：</p>
<ul align="left">
<li>更快的答疑时间</li>
<li>一致的解释说明</li>
<li>识别常见错误</li>
<li>专注概念而非调试</li>
</ul>
</td>
<td width="33%" align="center">
<h3>🔧 OS 爱好者</h3>
<p>适合：</p>
<ul align="left">
<li>自学者</li>
<li>初级内核开发者</li>
<li>嵌入式系统开发者</li>
<li>系统程序员</li>
</ul>
</td>
</tr>
</table>

---

## 📊 影响与成功指标

> **目标：** 帮助学生减少卡壳时间，增加学习时间

| 指标 | 目标 | 状态 |
|-----|------|------|
| 💡 "恍然大悟"时刻报告数 | 100+ | 📈 增长中 |
| ⏱️ 每个 Bug 平均节省时间 | 30+ 分钟 | ✅ 已达成 |
| 🎯 假设准确率 | 90%+ | ✅ 已达成 |
| 👥 学生采用率 | 每课程 50%+ | 📈 增长中 |
| ⭐ 学生满意度 | 4.5+/5 | 🎯 目标 |

---

## 🔮 路线图与未来增强

### 🚧 V1.0（当前版本）
- ✅ GDB、陷阱帧、页表分析
- ✅ x86 和 RISC-V 支持
- ✅ 基于 Web 的界面
- ✅ 基于规则的假设引擎
- ✅ **可选** AI 增强分析（GPT-4/Claude）

### 🎯 V2.0（计划中）
- [ ] 实时 GDB 集成（通过 MI 协议）
- [ ] 源代码分析
- [ ] ARM 架构支持
- [ ] 交互式调试教程

### 🌟 V3.0（愿景）
- [ ] 并发 Bug 检测（竞态条件、死锁）
- [ ] 性能分析洞察
- [ ] 多语言支持（英语、西班牙语）
- [ ] IDE 插件（VS Code、CLion）

---

## 🤝 贡献

我们 ❤️ 贡献！这是一个旨在帮助全世界学生的教育项目。

### 🌈 贡献方式

<table>
<tr>
<td>

**🐛 报告 Bug**
- 发现问题？提交 GitHub issue
- 包含崩溃转储和预期行为

</td>
<td>

**💡 建议功能**
- 新的假设模式
- 额外的架构支持
- UI 改进

</td>
<td>

**📝 改进文档**
- 修复错别字
- 添加示例
- 翻译成其他语言

</td>
</tr>
</table>

### 🔧 开发领域

- **架构支持：** 添加 ARM、MIPS、PowerPC
- **假设模式：** 添加更多 Bug 检测规则
- **可视化：** 更好的页表/内存可视化
- **集成：** GDB 脚本、IDE 插件、CI/CD 钩子

### 📜 贡献指南

1. Fork 仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交你的更改（`git commit -m '添加惊人功能'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 打开 Pull Request

---

## 📚 完整文档索引

<div align="center">

| 📖 文档类型 | 📝 文档名称 | 📌 说明 |
|------------|------------|---------|
| **🏠 主文档** | [README.md](README.md) | 项目总览、安装和快速开始 |
| **📚 文档中心** | [docs/README.md](docs/README.md) | 所有文档的导航中心 ⭐ |
| | | |
| **🚀 v2.0 文档** | [GDB 集成使用指南](docs/GDB_INTEGRATION_GUIDE.md) | 实时 GDB 功能详细使用教程 |
| | [GDB 集成技术设计](docs/GDB_INTEGRATION_DESIGN.md) | 系统架构、数据流、API 文档 |
| | [v2.0 发布说明](V2.0_RELEASE_NOTES.md) | 完整功能清单和更新内容 |
| | [v2.0 开发计划](V2_PLAN.md) | 路线图和后续功能计划 |
| | | |
| **📋 其他文档** | [AI 配置指南](AI_SETUP.md) | AI 增强功能设置教程 |
| | [测试报告](TESTING.md) | Bug 修复记录和测试方法 |

**💡 提示**: 如果不确定看哪个文档，先访问 [📚 文档中心](docs/README.md)

</div>

---

## 📄 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件。

```
MIT 许可证 - 可自由使用、修改和分发
非常适合教育环境 🎓
```

---

## 🙏 致谢

<div align="center">

### 用 💙 为全球学生打造

*灵感来源于在 GDB 中度过的无数小时、神秘的内核崩溃，*
*以及让 OS 调试不再痛苦的愿望*

**特别感谢：**
- 🎓 MIT xv6 开发者提供了出色的教学操作系统
- 📚 Stanford Pintos 团队提供的教育材料
- 💻 RISC-V 社区提供的开放架构
- 👥 所有在内核 Bug 中挣扎（并克服）的学生

---

### ⚡ 今天就开始更智能地调试！

```bash
git clone https://github.com/yourusername/os_debug.git
cd os_debug && ./run.sh
```

**有问题？建议？想法？**
[提交 Issue](https://github.com/yourusername/os_debug/issues) | [讨论区](https://github.com/yourusername/os_debug/discussions)

---

<sub>用 ❤️ 为 OS 社区制作 | © 2025</sub>

</div>

---

> **⚠️ 重要提示：**
> 此工具是*学习辅助*，而非替代理解 OS 概念。
> 使用它来加速学习，但要确保理解每个问题背后的*原理*！
