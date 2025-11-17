# 🔍 OS Debugging Assistant

An intelligent debugging companion for operating systems courses (xv6, Pintos, JOS). This tool analyzes debugging output and provides expert insights to help students identify and fix kernel bugs faster.

## 📋 Overview

Operating system debugging is notoriously difficult. Students face:
- Raw GDB output with cryptic register dumps
- Complex trapframe structures from kernel crashes
- Massive page table dumps that are hard to parse
- No clear path from symptoms to root cause

The OS Debugging Assistant solves this by acting as an expert system that:
- **Reads** and **understands** debugging output (GDB, trapframes, page tables)
- **Analyzes** the data to identify patterns and anomalies
- **Generates** prioritized hypotheses about the root cause
- **Provides** actionable debugging suggestions

## ✨ Features

### 1. GDB Output Analysis
- Parse and humanize stack backtraces
- Analyze register values for suspicious patterns
- Detect null pointers, invalid addresses, and corrupted state
- Identify common error patterns (panic, assertion failures)

### 2. Trapframe/Exception Analysis
- Decode trap numbers and exception types
- Parse x86 and RISC-V exception frames
- Decode page fault error codes (P/W/U/R/I bits)
- Identify faulting addresses (CR2/STVAL)
- Distinguish kernel vs user mode faults

### 3. Page Table Analysis
- Visualize virtual-to-physical memory mappings
- Check for common configuration errors:
  - Kernel pages marked as user-accessible (security violation)
  - Code pages marked as writable
  - Missing present bits
  - Permission mismatches

### 4. Intelligent Hypothesis Engine
Correlates findings from all analyzers to generate prioritized hypotheses:
- **Kernel null pointer dereference**
- **User stack overflow**
- **Invalid syscall arguments**
- **Page table misconfiguration**
- **Copy-on-write handling**
- **General protection faults**

## 🏗️ Architecture

```
os_debug/
├── backend/
│   ├── analyzers/          # Analysis engines
│   │   ├── gdb_analyzer.py
│   │   ├── trapframe_analyzer.py
│   │   ├── pagetable_analyzer.py
│   │   └── hypothesis_engine.py
│   ├── parsers/            # Text parsers
│   │   ├── gdb_parser.py
│   │   ├── trapframe_parser.py
│   │   └── pagetable_parser.py
│   ├── app.py              # Flask web server
│   └── requirements.txt
├── frontend/               # Web UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── examples/               # Example debugging scenarios
│   ├── example1_null_pointer.txt
│   ├── example2_page_table.txt
│   └── example3_x86_pagefault.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd os_debug
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Run the server:
```bash
python app.py
```

4. Open your browser:
```
http://localhost:5000
```

## 📖 Usage

### Basic Workflow

1. **Copy debugging output** from GDB, QEMU, or your kernel's crash dump
2. **Paste it** into the left text area
3. **Click "Analyze"**
4. **Review** the generated hypotheses and suggestions

### Example Inputs

The tool accepts various types of debugging information:

#### GDB Backtrace
```
(gdb) bt
#0  0x80100abc in panic () at kernel.c:42
#1  0x80101234 in trap (tf=0x...) at trap.c:123
```

#### GDB Registers
```
(gdb) info registers
rax            0x0      0
rip            0x80100abc
rsp            0x87fff000
```

#### Trapframe Dump
```
scause 0x000000000000000d
stval 0x0000000000000010
sepc=0x80003456
```

#### Page Table Dump
```
VA 0x80000000 -> PA 0x80000000 | Flags: P W U
VA 0x80001000 -> PA 0x80001000 | Flags: P W
```

### Supported Architectures

- ✅ x86-32 (xv6-x86, Pintos)
- ✅ x86-64
- ✅ RISC-V (xv6-riscv)

## 💡 Example Scenarios

### Scenario 1: Null Pointer Dereference

**Input:**
```
scause 0x000000000000000d
stval 0x0000000000000000
```

**Output:**
- **Hypothesis:** Kernel Null Pointer Dereference
- **Evidence:** STVAL is 0x0 (NULL)
- **Suggestions:**
  - Check for uninitialized pointers
  - Look for `ptr->field` where ptr is NULL
  - Add assertions before dereferencing

### Scenario 2: Page Table Security Issue

**Input:**
```
VA 0x80000000 -> PA 0x80000000 | Flags: P W U
```

**Output:**
- **Hypothesis:** Page Table Misconfiguration
- **Severity:** CRITICAL
- **Issue:** Kernel memory marked as user-accessible
- **Impact:** Security vulnerability - user can read/write kernel memory

## 🧪 Testing

Try the built-in examples:
1. Click "Load Example" in the UI
2. Or manually test with files in the `examples/` directory

## 🎯 Target Users

- **Primary:** OS course students (undergraduate/graduate)
- **Secondary:** OS enthusiasts, junior kernel developers
- **Courses:** xv6, Pintos, JOS, OS161

## 📊 Success Metrics

- Students report "Aha!" moments and time saved
- Teaching assistants recommend the tool
- 90%+ accuracy in categorizing crashes to known scenarios

## 🔮 Future Enhancements (Not in V1)

- Real-time GDB integration
- Source code analysis
- Concurrency bug detection (race conditions, deadlocks)
- Multi-language support

## 🤝 Contributing

This is an educational tool. Contributions are welcome!

Areas for improvement:
- Additional architecture support (ARM, MIPS)
- More hypothesis patterns
- Better visualization
- Integration with popular OS course projects

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built for students struggling with OS debugging. Inspired by countless hours spent in GDB trying to understand kernel panics.

---

**Note:** This tool provides debugging assistance but cannot replace understanding of OS concepts. Use it as a learning aid, not a replacement for learning!
