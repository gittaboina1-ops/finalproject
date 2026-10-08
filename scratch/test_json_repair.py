import sys
import os
import json
import re

def repair_and_parse_quiz_json(json_str: str):
    if not json_str or not isinstance(json_str, str):
        return None

    # Step 1: Clean trailing commas
    cleaned = re.sub(r",\s*([\]\}])", r"\1", json_str)
    # Step 2: Fix missing commas between objects: } { -> }, {
    cleaned = re.sub(r"\}\s*\{", "}, {", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    try:
        return json.loads(json_str)
    except Exception:
        pass

    # Step 3: Direct Regex Fallback Parser for LLM Quiz JSON
    # Extracts all question blocks even if JSON syntax has missing commas or unescaped quotes!
    raw_questions = []

    block_splits = re.split(r"(?i)[\"']question[\"']\s*:", json_str)

    if len(block_splits) > 1:
        for block in block_splits[1:]:
            # Extract question text (up to the next key or quote end)
            q_text_match = re.search(r"^\s*[\"']([\s\S]*?)[\"']\s*,\s*[\"']", block)
            if not q_text_match:
                q_text_match = re.search(r"^\s*[\"']([\s\S]*?)[\"']\s*,", block)
            
            q_text = q_text_match.group(1).strip() if q_text_match else ""

            # Extract options array
            opts_match = re.search(r"(?i)[\"']options[\"']\s*:\s*\[([\s\S]*?)\]", block)
            options = []
            if opts_match:
                opts_str = opts_match.group(1)
                options = re.findall(r"[\"']([\s\S]*?)[\"']", opts_str)
                options = [o.strip() for o in options if o.strip()]

            # Extract correct answer
            corr_match = re.search(r"(?i)[\"']correct_answer[\"']\s*:\s*[\"']([\s\S]*?)[\"']", block)
            corr_ans = corr_match.group(1).strip() if corr_match else (options[0] if options else "")

            # Extract explanation
            expl_match = re.search(r"(?i)[\"']explanation[\"']\s*:\s*[\"']([\s\S]*?)[\"']", block)
            expl = expl_match.group(1).strip() if expl_match else ""

            if q_text and options and len(options) >= 2:
                raw_questions.append({
                    "question": q_text,
                    "options": options,
                    "correct_answer": corr_ans,
                    "explanation": expl
                })

    if raw_questions:
        return {"quiz": raw_questions}

    return None

# Test with the exact error scenario from user: broken JSON missing comma
def test_repair():
    print("--- Test: Broken JSON with missing comma (line 26 column 6 error) ---")
    broken_llm_json = """{
  "quiz": [
    {
      "question": "Which condition is necessary for deadlock?",
      "options": ["Mutual exclusion", "Caching", "Paging", "Spooling"],
      "correct_answer": "Mutual exclusion",
      "explanation": "Mutual exclusion requires non-shareable resources."
    }
    {
      "question": "What is hold and wait?",
      "options": ["Process holding resources while requesting more", "CPU idle state", "Memory allocation", "Thread context switch"]
      "correct_answer": "Process holding resources while requesting more",
      "explanation": "Hold and wait means a process holds at least one resource and requests others."
    }
  ]
}"""

    data = repair_and_parse_quiz_json(broken_llm_json)
    assert data is not None, "Repair failed to parse broken JSON!"
    quiz_items = data.get("quiz", [])
    print(f"Successfully recovered {len(quiz_items)} questions from malformed JSON!")
    for q in quiz_items:
        print("Question:", q["question"])
        print("Options:", q["options"])
    assert len(quiz_items) == 2
    print("✓ JSON Repair Test Passed Successfully!")

if __name__ == "__main__":
    test_repair()
