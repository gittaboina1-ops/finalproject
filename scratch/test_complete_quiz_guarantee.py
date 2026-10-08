import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pragtutor_backend import parse_quiz_from_llm_response

def run_all_guarantee_tests():
    print("======================================================")
    print("RUNNING COMPLETE QUIZ GUARANTEE TEST SUITE")
    print("======================================================")

    # Scenario 1: Standard valid JSON quiz block
    resp1 = """### CPU Scheduling
CPU Scheduling is the process of deciding which process gets CPU time.

```json
{
  "quiz": [
    {"question": "What is FCFS?", "options": ["First Come First Served", "Fastest CPU", "Full Cache", "Fixed Count"], "correct_answer": "First Come First Served", "explanation": "FCFS schedules processes in arrival order."},
    {"question": "What is Round Robin?", "options": ["Time slice scheduling", "Priority queue", "LIFO", "Static allocation"], "correct_answer": "Time slice scheduling", "explanation": "Round Robin uses fixed time quantums."}
  ]
}
```"""
    c1, q1, id1, err1 = parse_quiz_from_llm_response(resp1, "CPU Scheduling")
    assert q1 is not None and len(q1) == 2
    assert id1 is not None
    assert err1 is None
    print("Scenario 1 (Valid JSON): PASSED! Questions count:", len(q1))

    # Scenario 2: Broken JSON (missing commas)
    resp2 = """### Deadlock
Deadlock occurs when processes wait indefinitely.

{
  "quiz": [
    {"question": "What is mutual exclusion?", "options": ["Exclusive access", "Shared access", "No access", "Disk access"], "correct_answer": "Exclusive access", "explanation": "Mutual exclusion grants exclusive access."}
    {"question": "What is hold and wait?", "options": ["Holding resource while waiting", "Holding CPU", "Waiting for input", "Yielding CPU"], "correct_answer": "Holding resource while waiting", "explanation": "Process holds resources while requesting more."}
  ]
}"""
    c2, q2, id2, err2 = parse_quiz_from_llm_response(resp2, "Deadlock")
    assert q2 is not None and len(q2) == 2
    assert id2 is not None
    print("Scenario 2 (Malformed JSON): PASSED! Questions count:", len(q2))

    # Scenario 3: Direct Array without "quiz" object
    resp3 = """### Virtual Memory
Virtual Memory abstracts RAM.

[
  {"question": "What is a page fault?", "options": ["Missing page trap", "Disk crash", "RAM error", "Kernel panic"], "correct_answer": "Missing page trap", "explanation": "Page fault occurs when page is not in RAM."}
]"""
    c3, q3, id3, err3 = parse_quiz_from_llm_response(resp3, "Virtual Memory")
    assert q3 is not None and len(q3) == 1
    assert id3 is not None
    print("Scenario 3 (Direct Array): PASSED! Questions count:", len(q3))

    # Scenario 4: Truncated LLM response WITH ZERO JSON AT ALL
    resp4 = """### Process Synchronization
Process Synchronization coordinates concurrent processes so they do not access shared data at the same time and cause race conditions.

Semaphores and Mutexes are common synchronization primitives."""
    c4, q4, id4, err4 = parse_quiz_from_llm_response(resp4, "Process Synchronization")
    assert q4 is not None and len(q4) == 5
    assert id4 is not None
    print("Scenario 4 (Zero JSON / Truncated LLM Output): PASSED! Fallback Quiz Generated. Questions count:", len(q4))

    # Scenario 5: Empty/Null response
    c5, q5, id5, err5 = parse_quiz_from_llm_response("", "Deadlock")
    assert q5 is not None and len(q5) == 5
    assert id5 is not None
    print("Scenario 5 (Empty LLM Output): PASSED! Fallback Quiz Generated. Questions count:", len(q5))

    print("\n======================================================")
    print("ALL 5 QUIZ GUARANTEE SCENARIOS PASSED 100% PERFECTLY!")
    print("======================================================")

if __name__ == "__main__":
    run_all_guarantee_tests()
