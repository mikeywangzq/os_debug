#!/usr/bin/env python3
"""
OS 调试助手后端的简单测试脚本
使用示例输入测试各个分析器
"""

import sys
import os

# 将 backend 目录添加到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from analyzers.hypothesis_engine import HypothesisEngine


def test_null_pointer_example():
    """测试空指针解引用示例（RISC-V 架构）"""
    print("=" * 80)
    print("测试 1: 空指针解引用 (RISC-V)")
    print("=" * 80)

    # RISC-V 内核崩溃的示例输入
    # 特征: stval=0x0 表示访问了空指针
    test_input = """
#0  0x0000000080002a9e in panic () at kernel/printf.c:127
#1  0x0000000080002630 in kerneltrap () at kernel/trap.c:141
#2  0x0000000080003456 in mycpu () at kernel/proc.c:67

scause 0x000000000000000d
stval 0x0000000000000000
sepc=0x0000000080003456

ra             0x80002630
sp             0x80009ac0
a0             0x0
s1             0x0
"""

    # 创建分析引擎并运行分析
    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    # 打印分析摘要
    print(f"\n摘要: {result['summary']}")
    print(f"\n假设数量: {len(result['hypotheses'])}")

    # 显示首要假设
    if result['hypotheses']:
        print("\n首要假设:")
        hyp = result['hypotheses'][0]
        print(f"  场景: {hyp['scenario']}")
        print(f"  优先级: {hyp['priority']}")
        print(f"  解释: {hyp['explanation']}")

    # 显示发现的问题
    print(f"\n发现问题总数: {len(result['all_findings'])}")
    for finding in result['all_findings'][:3]:  # 显示前3个
        print(f"  [{finding['severity']}] {finding['category']}")

    return result


def test_page_table_example():
    """测试页表配置错误示例"""
    print("\n" + "=" * 80)
    print("测试 2: 页表配置错误")
    print("=" * 80)

    # 页表转储示例输入
    # 问题: 内核地址 (0x80000000) 被标记为用户可访问 (U 位)
    test_input = """
VA 0x0000000000000000 -> PA 0x0000000087f6e000 | Flags: P W U
VA 0x0000000000001000 -> PA 0x0000000087f6d000 | Flags: P W U
VA 0x0000000080000000 -> PA 0x0000000080000000 | Flags: P W U
VA 0x0000000080001000 -> PA 0x0000000080001000 | Flags: P W U
"""

    # 运行分析
    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    print(f"\n摘要: {result['summary']}")

    # 显示页表分析结果
    if result['pagetable_analysis']:
        pt = result['pagetable_analysis']
        print(f"\n发现页表映射: {len(pt['mappings'])} 条")
        print(f"页表问题: {len(pt['findings'])} 个")

        if pt['findings']:
            print("\n严重的页表问题:")
            for finding in pt['findings'][:2]:
                print(f"  [{finding['severity']}] {finding['message'][:100]}...")

    return result


def test_x86_page_fault():
    """测试 x86 页面错误示例"""
    print("\n" + "=" * 80)
    print("测试 3: x86 页面错误")
    print("=" * 80)

    # x86 页面错误示例输入
    # 特征: trap 14 (Page Fault), err 6, cr2=0x8 (接近空指针)
    test_input = """
#0  0x80103a2e in trap (tf=0x8dfffe8c) at trap.c:37
#1  0x8010392c in alltraps () at trapasm.S:20

trap 14 err 6
eip 80104f3a esp 8dfffeb8
eax 0 ebx 80112fd0
cr2 0x8
"""

    # 运行分析
    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    print(f"\n摘要: {result['summary']}")

    # 显示陷阱帧分析结果
    if result['trapframe_analysis']:
        tf = result['trapframe_analysis']
        if tf.get('exception_info'):
            print(f"\n异常类型: {tf['exception_info']['trap_name']}")

        # 显示错误代码分析
        if tf.get('error_code_analysis'):
            err = tf['error_code_analysis']
            print(f"\n错误代码分析:")
            print(f"  页面存在: {err['present']}")
            print(f"  写操作: {err['write']}")
            print(f"  用户模式: {err['user_mode']}")

    # 显示生成的假设
    print(f"\n生成假设数量: {len(result['hypotheses'])}")
    for i, hyp in enumerate(result['hypotheses'][:2], 1):
        print(f"\n  {i}. {hyp['scenario']} (优先级: {hyp['priority']})")

    return result


def main():
    """运行所有测试"""
    print("OS 调试助手 - 后端测试套件")
    print()

    try:
        # 执行所有测试
        test_null_pointer_example()
        test_page_table_example()
        test_x86_page_fault()

        # 显示成功信息
        print("\n" + "=" * 80)
        print("✓ 所有测试成功完成！")
        print("=" * 80)
        print("\n后端工作正常。现在你可以:")
        print("1. 启动 Web 服务器: cd backend && python app.py")
        print("2. 在浏览器中打开 http://localhost:5000")
        print("3. 尝试示例输入!")

    except Exception as e:
        # 显示错误信息
        print(f"\n✗ 测试失败，错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
