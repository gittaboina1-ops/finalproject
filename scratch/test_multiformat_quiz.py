import sys
import os
import json
import re

def parse_quiz_robust(llm_response: str, target_topic: str):
    if not llm_response or not isinstance(llm_response, str):
        return llm_response, None, None, "Quiz could not be generated for this response."

    import time
    import random

    lower_resp = llm_response.lower()
    
    # Search for any quiz indicator keys
    key_positions = []
    for key in ['"quiz"', "'quiz'", '"questions"', "'questions'", '"question"', "'question'", '"options"', "'options'"]:
        pos = lower_resp.find(key)
        if pos != -1:
            key_positions.append(pos)

    if not key_positions:
        # Strip residual JSON or quiz headers if any
        cleaned = re.sub(r"```json[\s\S]*?```", "", llm_response, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?i)\n?\s*###?\s*Quiz[\s\S]*$", "", cleaned)
        cleaned = re.sub(r"(?i)\n?\s*To help you check your understanding[\s\S]*$", "", cleaned)
        return cleaned.strip(), None, None, "Quiz could not be generated for this response."

    key_idx = min(key_positions)

    # Find outermost container opening '{' or '[' before key_idx
    # Scan backwards from key_idx
    start_idx = -1
    pos = key_idx
    while pos >= 0:
        ch = llm_response[pos]
        if ch in ('{', '['):
            start_idx = pos
            # Check if there is an enclosing outer '[' or '{' before start_idx with only whitespace/commas
            prev_pos = pos - 1
            while prev_pos >= 0:
                prev_ch = llm_response[prev_pos]
                if prev_ch in (' ', '\t', '\n', '\r', ','):
                    prev_pos -= 1
                    continue
                elif prev_ch in ('[', '{'):
                    start_idx = prev_pos
                    pos = prev_pos
                    break
                else:
                    break
            if start_idx == pos:
                break
        pos -= 1

    json_str = None
    span_start = -1
    span_end = -1

    if start_idx != -1:
        stack = []
        in_string = False
        escape = False
        end_idx = -1

        for i in range(start_idx, len(llm_response)):
            ch = llm_response[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch in ('{', '['):
                    stack.append(ch)
                elif ch in ('}', ']'):
                    if stack:
                        top = stack[-1]
                        if (ch == '}' and top == '{') or (ch == ']' and top == '['):
                            stack.pop()
                            if not stack:
                                end_idx = i
                                break

        if end_idx != -1:
            json_str = llm_response[start_idx : end_idx + 1]
            span_start = start_idx
            span_end = end_idx + 1

    if not json_str:
        # Clean text
        cleaned = re.sub(r"```json[\s\S]*?```", "", llm_response, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?i)\n?\s*###?\s*Quiz[\s\S]*$", "", cleaned)
        cleaned = re.sub(r"(?i)\n?\s*To help you check your understanding[\s\S]*$", "", cleaned)
        return cleaned.strip(), None, None, "Quiz could not be generated for this response."

    # Check for wrapping markdown code fences around span_start / span_end
    prefix_check = llm_response[:span_start].rstrip()
    if prefix_check.endswith("```json") or prefix_check.endswith("```"):
        fence_start = prefix_check.rfind("```")
        if fence_start != -1:
            span_start = fence_start

    suffix_check = llm_response[span_end:].lstrip()
    if suffix_check.startswith("```"):
        fence_end = llm_response.find("```", span_end)
        if fence_end != -1:
            span_end = fence_end + 3

    # Remove JSON block from explanation text
    cleaned_explanation = (llm_response[:span_start] + llm_response[span_end:]).strip()

    # Clean residual quiz section headings and intro text (e.g. "### Quiz", "To help you check your understanding...")
    cleaned_explanation = re.sub(r"(?i)\n?\s*###?\s*Quiz[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*To help you check your understanding[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*Here are (some|\d+)?\s*(questions|multiple-choice questions)[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*Test your understanding[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"```json[\s\S]*?```", "", cleaned_explanation, flags=re.IGNORECASE).strip()

    # If explanation text became empty, generate fallback concept header
    if not cleaned_explanation or len(cleaned_explanation) < 15:
        topic_disp = target_topic or "the requested topic"
        cleaned_explanation = f"### Concept Overview: {topic_disp}\n\nBelow is an interactive quiz generated specifically for **{topic_disp}** to test your understanding. Complete all 5 questions below!"

    # Clean common LLM JSON syntax quirks (trailing commas)
    cleaned_json_str = re.sub(r",\s*([\]\}])", r"\1", json_str)

    try:
        data = json.loads(cleaned_json_str)
    except Exception:
        try:
            data = json.loads(json_str)
        except Exception as e:
            print(f"Notice: Quiz JSON parsing error: {e}")
            return cleaned_explanation, None, None, "Quiz could not be generated for this response."

    raw_quiz = None
    if isinstance(data, list):
        raw_quiz = data
    elif isinstance(data, dict):
        raw_quiz = data.get("quiz") or data.get("questions")
        if not raw_quiz and "question" in data:
            raw_quiz = [data]

    if not raw_quiz or not isinstance(raw_quiz, list) or len(raw_quiz) == 0:
        return cleaned_explanation, None, None, "Quiz could not be generated for this response."

    safe_questions = []
    private_questions = []

    for idx, q_item in enumerate(raw_quiz):
        if not isinstance(q_item, dict):
            continue
        q_text = q_item.get("question", f"Question {idx + 1}")
        opts = q_item.get("options", [])
        if not isinstance(opts, list) or len(opts) < 2:
            continue

        opts = [str(o) for o in opts]
        corr_ans = str(q_item.get("correct_answer", opts[0]))
        expl = str(q_item.get("explanation", ""))

        safe_questions.append({
            "id": idx,
            "question": q_text,
            "options": opts
        })
        private_questions.append({
            "id": idx,
            "question": q_text,
            "options": opts,
            "correct_answer": corr_ans,
            "explanation": expl
        })

    if len(safe_questions) == 0:
        return cleaned_explanation, None, None, "Quiz could not be generated for this response."

    quiz_id = f"quiz_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    return cleaned_explanation, safe_questions, quiz_id, None


# Test cases
def run_tests():
    print("--- Test A: Format from user screenshot (Array starting with [ { \"question\": ... }) ---")
    resp_user_screenshot = """Virtual Memory allows execution of processes that are not completely in memory.

### Quiz
To help you check your understanding, here are some questions:

[
  {
    "question": "How does the operating system choose a page to load when memory is full?",
    "options": ["Page replacement algorithm", "CPU scheduling", "Disk formatting", "Cache invalidation"],
    "correct_answer": "Page replacement algorithm",
    "explanation": "Page replacement algorithms select which page to swap out."
  },
  {
    "question": "What is page fault?",
    "options": ["Accessing page not in RAM", "Hardware failure", "Compiler error", "Syntax error"],
    "correct_answer": "Accessing page not in RAM",
    "explanation": "Page fault occurs when referenced page is not in physical memory."
  }
]"""

    cleaned, safe_quiz, quiz_id, err = parse_quiz_robust(resp_user_screenshot, "Virtual Memory")
    print("Error:", err)
    print("Cleaned explanation:\n---")
    print(cleaned)
    print("---\nSafe Quiz questions count:", len(safe_quiz) if safe_quiz else 0)
    assert err is None
    assert safe_quiz and len(safe_quiz) == 2
    assert "To help you check your understanding" not in cleaned
    assert "### Quiz" not in cleaned
    assert "question" not in cleaned
    print("✓ Test A Passed Perfectly!")

if __name__ == "__main__":
    run_tests()
