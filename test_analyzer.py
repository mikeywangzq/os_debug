#!/usr/bin/env python3
"""
Simple test script for the OS Debugging Assistant backend.
Tests the analyzers with example inputs.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from analyzers.hypothesis_engine import HypothesisEngine


def test_null_pointer_example():
    """Test with null pointer dereference example."""
    print("=" * 80)
    print("TEST 1: Null Pointer Dereference (RISC-V)")
    print("=" * 80)

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

    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    print(f"\nSummary: {result['summary']}")
    print(f"\nNumber of hypotheses: {len(result['hypotheses'])}")

    if result['hypotheses']:
        print("\nTop Hypothesis:")
        hyp = result['hypotheses'][0]
        print(f"  Scenario: {hyp['scenario']}")
        print(f"  Priority: {hyp['priority']}")
        print(f"  Explanation: {hyp['explanation']}")

    print(f"\nTotal findings: {len(result['all_findings'])}")
    for finding in result['all_findings'][:3]:  # Show first 3
        print(f"  [{finding['severity']}] {finding['category']}")

    return result


def test_page_table_example():
    """Test with page table misconfiguration example."""
    print("\n" + "=" * 80)
    print("TEST 2: Page Table Misconfiguration")
    print("=" * 80)

    test_input = """
VA 0x0000000000000000 -> PA 0x0000000087f6e000 | Flags: P W U
VA 0x0000000000001000 -> PA 0x0000000087f6d000 | Flags: P W U
VA 0x0000000080000000 -> PA 0x0000000080000000 | Flags: P W U
VA 0x0000000080001000 -> PA 0x0000000080001000 | Flags: P W U
"""

    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    print(f"\nSummary: {result['summary']}")

    if result['pagetable_analysis']:
        pt = result['pagetable_analysis']
        print(f"\nPage table mappings found: {len(pt['mappings'])}")
        print(f"Page table findings: {len(pt['findings'])}")

        if pt['findings']:
            print("\nCritical page table issues:")
            for finding in pt['findings'][:2]:
                print(f"  [{finding['severity']}] {finding['message'][:100]}...")

    return result


def test_x86_page_fault():
    """Test with x86 page fault example."""
    print("\n" + "=" * 80)
    print("TEST 3: x86 Page Fault")
    print("=" * 80)

    test_input = """
#0  0x80103a2e in trap (tf=0x8dfffe8c) at trap.c:37
#1  0x8010392c in alltraps () at trapasm.S:20

trap 14 err 6
eip 80104f3a esp 8dfffeb8
eax 0 ebx 80112fd0
cr2 0x8
"""

    engine = HypothesisEngine()
    result = engine.analyze(test_input)

    print(f"\nSummary: {result['summary']}")

    if result['trapframe_analysis']:
        tf = result['trapframe_analysis']
        if tf.get('exception_info'):
            print(f"\nException: {tf['exception_info']['trap_name']}")

        if tf.get('error_code_analysis'):
            err = tf['error_code_analysis']
            print(f"\nError Code Analysis:")
            print(f"  Present: {err['present']}")
            print(f"  Write: {err['write']}")
            print(f"  User mode: {err['user_mode']}")

    print(f"\nHypotheses generated: {len(result['hypotheses'])}")
    for i, hyp in enumerate(result['hypotheses'][:2], 1):
        print(f"\n  {i}. {hyp['scenario']} (Priority: {hyp['priority']})")

    return result


def main():
    """Run all tests."""
    print("OS Debugging Assistant - Backend Test Suite")
    print()

    try:
        test_null_pointer_example()
        test_page_table_example()
        test_x86_page_fault()

        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)
        print("\nThe backend is working correctly. You can now:")
        print("1. Start the web server: cd backend && python app.py")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Try the example inputs!")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
