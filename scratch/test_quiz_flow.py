import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pragtutor_backend import parse_quiz_from_llm_response, evaluate_quiz

def test_quiz_flow():
    print("--- TEST 1: LLM explanation followed by ```json quiz block ---")
    llm_resp1 = """### Deadlock Overview
Deadlock is a state where a set of processes are blocked because each process holds a resource and waits for another resource held by some other process.

```json
{
  "quiz": [
    {
      "question": "Which of the following is a necessary condition for deadlock?",
      "options": ["Mutual Exclusion", "Paging", "Caching", "Scheduling"],
      "correct_answer": "Mutual Exclusion",
      "explanation": "Mutual Exclusion means at least one resource must be held in a non-shareable mode."
    },
    {
      "question": "What happens when circular wait occurs?",
      "options": ["High CPU usage", "Deadlock state", "Fast execution", "Memory leak"],
      "correct_answer": "Deadlock state",
      "explanation": "Circular wait is one of the four necessary conditions for deadlock."
    }
  ]
}
```"""

    cleaned1, safe_quiz1, quiz_id1, err1 = parse_quiz_from_llm_response(llm_resp1, "Deadlock")
    assert err1 is None, f"Expected no error, got {err1}"
    assert '"quiz"' not in cleaned1, f"JSON leaked in cleaned explanation: {cleaned1}"
    assert len(safe_quiz1) == 2, f"Expected 2 questions, got {len(safe_quiz1)}"
    assert "correct_answer" not in safe_quiz1[0], "Correct answer leaked in safe questions!"
    print("✓ Test 1 Passed!")
    print("Cleaned explanation sample:", cleaned1[:60])
    print("Safe questions count:", len(safe_quiz1))

    print("\n--- TEST 2: LLM output with raw JSON without ```json fences ---")
    llm_resp2 = """A process is an executing instance of a computer program.
{
  "quiz": [
    {
      "question": "What is a process?",
      "options": ["A running program", "A stored file", "A memory chip", "A CPU socket"],
      "correct_answer": "A running program",
      "explanation": "A process is a program in execution."
    }
  ]
}"""

    cleaned2, safe_quiz2, quiz_id2, err2 = parse_quiz_from_llm_response(llm_resp2, "Process Management")
    assert err2 is None, f"Expected no error, got {err2}"
    assert '"quiz"' not in cleaned2, f"JSON leaked in cleaned explanation: {cleaned2}"
    assert len(safe_quiz2) == 1
    print("✓ Test 2 Passed!")

    print("\n--- TEST 3: LLM output with ONLY JSON (no leading text) ---")
    llm_resp3 = """{
  "quiz": [
    {
      "question": "What is virtual memory?",
      "options": ["Storage abstraction", "Physical RAM", "Hard disk partition", "ROM"],
      "correct_answer": "Storage abstraction",
      "explanation": "Virtual memory provides an illusion of large main memory."
    }
  ]
}"""

    cleaned3, safe_quiz3, quiz_id3, err3 = parse_quiz_from_llm_response(llm_resp3, "Virtual Memory")
    assert err3 is None
    assert '"quiz"' not in cleaned3
    assert len(cleaned3) > 20, "Fallback concept header should be generated when explanation is empty!"
    print("✓ Test 3 Passed! Fallback header generated:", cleaned3[:80])

    print("\n--- TEST 4: Evaluate Quiz Submissions ---")
    # Evaluate 100% score
    res_100 = evaluate_quiz(quiz_id1, [0, 1])
    assert res_100["score"] == 2
    assert res_100["percentage"] == 100.0
    assert res_100["passed"] is True
    print("✓ 100% Score Evaluation Passed!")

    # Evaluate 50% score (requires > 70% to pass)
    res_50 = evaluate_quiz(quiz_id1, [0, 0])
    assert res_50["score"] == 1
    assert res_50["percentage"] == 50.0
    assert res_50["passed"] is False
    print("✓ 50% Score Fail Condition (>70% requirement) Passed!")

    print("\nALL BACKEND QUIZ TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_quiz_flow()
