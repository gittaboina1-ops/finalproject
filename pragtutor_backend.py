import os
import json

from dynamic_prompt import build_dynamic_prompt, build_multimodal_llm_payload
from llm_service import generate_response
from multimodal_processor import process_multimodal_inputs
from topic_identifier import identify_topic

from prerequisite_engine import (
    find_missing_prerequisites,
    generate_learning_path
)

from retrieve import retrieve, retrieve_relevant_images


# ============================================================
# CONFIGURATION
# ============================================================

STUDENT_ID = "STU001"

TOP_K = 5

# In-memory session tracking for generated quizzes (quiz_id -> private quiz metadata with correct answers)
QUIZ_STORE: dict = {}

def generate_fallback_quiz(target_topic: str, subject: str = "operating_systems"):
    """
    Generates a high-quality 5-question fallback quiz for the given target topic
    in case the LLM response did not include a valid quiz JSON block.
    Guarantees that an interactive quiz is ALWAYS displayed to the student.
    """
    topic_clean = (target_topic or "Operating Systems").strip()
    topic_lower = topic_clean.lower()

    if "deadlock" in topic_lower:
        return [
            {
                "question": "Which of the following is a necessary condition for deadlock to occur?",
                "options": ["Mutual exclusion", "Preemption", "Single threading", "Cache coherency"],
                "correct_answer": "Mutual exclusion",
                "explanation": "Mutual exclusion requires that at least one resource is held in a non-shareable mode."
            },
            {
                "question": "What does the 'Hold and Wait' condition mean in deadlock theory?",
                "options": [
                    "A process holds at least one resource and waits for additional resources held by others",
                    "A process releases all resources before requesting new ones",
                    "The CPU holds execution while waiting for I/O",
                    "A thread yields its time slice to main memory"
                ],
                "correct_answer": "A process holds at least one resource and waits for additional resources held by others",
                "explanation": "Hold and wait means a process holding resources is waiting for additional resources held by other processes."
            },
            {
                "question": "Which deadlock handling strategy prevents deadlocks by invalidating one of the 4 necessary conditions?",
                "options": ["Deadlock Prevention", "Deadlock Detection", "Banker's Algorithm", "Ostrich Algorithm"],
                "correct_answer": "Deadlock Prevention",
                "explanation": "Deadlock prevention eliminates deadlock by ensuring at least one of the 4 necessary conditions cannot hold."
            },
            {
                "question": "Which algorithm is commonly used for Deadlock Avoidance?",
                "options": ["Banker's Algorithm", "Round Robin", "First-Come First-Served", "LRU Page Replacement"],
                "correct_answer": "Banker's Algorithm",
                "explanation": "Banker's Algorithm tests for safety by simulating the allocation of maximum predetermined amounts of resources."
            },
            {
                "question": "What is a 'Circular Wait' condition?",
                "options": [
                    "A closed chain of processes exists such that each process holds a resource needed by the next",
                    "A process loops infinitely waiting for user input",
                    "The scheduler rotates CPU time in a circle",
                    "Disk read heads rotate in a circular track"
                ],
                "correct_answer": "A closed chain of processes exists such that each process holds a resource needed by the next",
                "explanation": "Circular wait occurs when process P0 waits for a resource held by P1, P1 waits for P2, and Pn waits for P0."
            }
        ]
    elif "process" in topic_lower or "pcb" in topic_lower:
        return [
            {
                "question": "What is a process in operating system terminology?",
                "options": ["A program in execution", "A file saved on secondary disk storage", "A physical CPU core", "A compiler directive"],
                "correct_answer": "A program in execution",
                "explanation": "A process is a dynamic entity representing an active program currently executing in main memory."
            },
            {
                "question": "Which data structure does the operating system use to store process state and metadata?",
                "options": ["Process Control Block (PCB)", "Page Table Entry (PTE)", "File Allocation Table (FAT)", "Segment Register"],
                "correct_answer": "Process Control Block (PCB)",
                "explanation": "The PCB stores essential process information including PID, program counter, registers, and memory boundaries."
            },
            {
                "question": "Which state transition occurs when a running process requests I/O operation?",
                "options": ["Running -> Waiting/Blocked", "Running -> Ready", "Waiting -> Ready", "Ready -> Running"],
                "correct_answer": "Running -> Waiting/Blocked",
                "explanation": "When a process requests I/O, it transitions to the Waiting state until the I/O operation completes."
            },
            {
                "question": "What component of the OS context switches between processes?",
                "options": ["Dispatcher / CPU Scheduler", "Linker", "Loader", "Assembler"],
                "correct_answer": "Dispatcher / CPU Scheduler",
                "explanation": "The dispatcher saves the state of the currently running process and loads the saved state of the next selected process."
            },
            {
                "question": "Which memory segment of a process stores local variables and function call frames?",
                "options": ["Stack", "Heap", "Data Segment", "Text Segment"],
                "correct_answer": "Stack",
                "explanation": "The stack dynamically grows and shrinks to manage function parameters, return addresses, and local variables."
            }
        ]
    elif "virtual memory" in topic_lower or "page" in topic_lower or "paging" in topic_lower:
        return [
            {
                "question": "What primary advantage does Virtual Memory provide to an operating system?",
                "options": [
                    "Allows execution of processes larger than physical RAM",
                    "Increases physical RAM hardware capacity",
                    "Speeds up CPU clock cycle frequency",
                    "Eliminates the need for secondary storage"
                ],
                "correct_answer": "Allows execution of processes larger than physical RAM",
                "explanation": "Virtual memory decouples logical memory from physical memory, enabling execution of programs exceeding physical RAM."
            },
            {
                "question": "What event occurs when a process accesses a page that is not currently present in physical RAM?",
                "options": ["Page Fault", "Segmentation Fault", "Bus Error", "Stack Overflow"],
                "correct_answer": "Page Fault",
                "explanation": "A Page Fault trap is triggered when the valid bit in the page table entry indicates the page is not in physical memory."
            },
            {
                "question": "Which component translates virtual logical addresses into physical RAM addresses?",
                "options": ["Memory Management Unit (MMU)", "ALU", "Control Unit", "DMA Controller"],
                "correct_answer": "Memory Management Unit (MMU)",
                "explanation": "The MMU is hardware that performs real-time address translation using page tables and TLB."
            },
            {
                "question": "What is the function of the Translation Lookaside Buffer (TLB)?",
                "options": [
                    "A high-speed hardware cache for page table translations",
                    "A secondary disk partition for swap space",
                    "A buffer for network data packets",
                    "A queue for waiting I/O requests"
                ],
                "correct_answer": "A high-speed hardware cache for page table translations",
                "explanation": "The TLB caches recent virtual-to-physical address mappings to bypass full page table memory lookups."
            },
            {
                "question": "What phenomenon occurs when the system spends more time swapping pages than executing useful work?",
                "options": ["Thrashing", "Belady's Anomaly", "Fragmentation", "Starvation"],
                "correct_answer": "Thrashing",
                "explanation": "Thrashing occurs when the total size of active working sets exceeds available physical memory, causing continuous page faults."
            }
        ]
    else:
        return [
            {
                "question": f"What is the primary core objective when studying {topic_clean}?",
                "options": [
                    f"Understanding how system resources and concepts for {topic_clean} are managed efficiently",
                    f"Replacing hardware components related to {topic_clean}",
                    f"Bypassing low-level operating system controls for {topic_clean}",
                    f"Disabling concurrent execution during {topic_clean}"
                ],
                "correct_answer": f"Understanding how system resources and concepts for {topic_clean} are managed efficiently",
                "explanation": f"Study of {topic_clean} focuses on resource allocation, correctness, efficiency, and OS abstractions."
            },
            {
                "question": f"Which of the following best describes the key mechanism involved in {topic_clean}?",
                "options": [
                    f"Structured coordination between operating system services and physical hardware for {topic_clean}",
                    f"Manual user intervention for every low-level operation in {topic_clean}",
                    f"Storing all execution data exclusively in read-only memory",
                    f"Executing instructions without allocating system registers"
                ],
                "correct_answer": f"Structured coordination between operating system services and physical hardware for {topic_clean}",
                "explanation": f"The operating system manages {topic_clean} through kernel subsystems and hardware interfaces."
            },
            {
                "question": f"What is a critical design requirement when implementing systems for {topic_clean}?",
                "options": [
                    "Ensuring safety, preventing race conditions or invalid states, and maximizing resource utilization",
                    "Increasing power consumption without bounds",
                    "Hardcoding static values for all dynamic memory allocations",
                    "Restricting memory access to a single byte"
                ],
                "correct_answer": "Ensuring safety, preventing race conditions or invalid states, and maximizing resource utilization",
                "explanation": f"Operating system abstractions for {topic_clean} must guarantee reliability, safety, and efficiency."
            },
            {
                "question": f"How does the operating system kernel interact with concepts in {topic_clean}?",
                "options": [
                    f"By providing standardized system calls, abstractions, and management algorithms for {topic_clean}",
                    f"By deleting process tables whenever {topic_clean} is referenced",
                    f"By forcing all operations in {topic_clean} to run in unprivileged user mode only",
                    f"By disabling hardware interrupts during {topic_clean} execution"
                ],
                "correct_answer": f"By providing standardized system calls, abstractions, and management algorithms for {topic_clean}",
                "explanation": f"Kernels provide clean abstractions and protected system calls for managing {topic_clean}."
            },
            {
                "question": f"What is a potential failure or performance bottleneck related to {topic_clean} if misconfigured?",
                "options": [
                    f"Resource contention, excessive overhead, or improper synchronization in {topic_clean}",
                    f"Immediate physical damage to the monitor display",
                    f"Automatic deletion of source code files on disk",
                    f"Permanent loss of static BIOS firmware"
                ],
                "correct_answer": f"Resource contention, excessive overhead, or improper synchronization in {topic_clean}",
                "explanation": f"Improper management of {topic_clean} can lead to performance degradation or resource conflicts."
            }
        ]

def parse_quiz_from_llm_response(llm_response: str, target_topic: str, student_id: str = "STU001", subject: str = "operating_systems"):
    """
    Parses the 5-question quiz JSON block generated by the LLM.
    Supports object format {"quiz": [...]}, {"questions": [...]}, and direct array format [{"question": ...}, ...].
    If no valid quiz JSON is found, automatically generates a topic-specific fallback quiz so an interactive quiz is ALWAYS provided.
    Strips the quiz JSON block and any section headings from the response text.
    Returns: (cleaned_explanation, safe_quiz_questions, quiz_id, quiz_error_message)
    """
    if not llm_response or not isinstance(llm_response, str):
        llm_response = f"### Concept Overview: {target_topic}\n\nHere is your personalized explanation for **{target_topic}**."

    import re
    import time
    import random
    import json

    lower_resp = llm_response.lower()

    # Search for any quiz indicator keys
    key_positions = []
    for key in ['"quiz"', "'quiz'", '"questions"', "'questions'", '"question"', "'question'", '"options"', "'options'"]:
        pos = lower_resp.find(key)
        if pos != -1:
            key_positions.append(pos)

    json_str = None
    span_start = -1
    span_end = -1

    if key_positions:
        key_idx = min(key_positions)

        # Find outermost container opening '{' or '[' before key_idx by scanning backwards
        start_idx = -1
        pos = key_idx
        while pos >= 0:
            ch = llm_response[pos]
            if ch in ('{', '['):
                start_idx = pos
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

    # Clean explanation text
    if json_str and span_start != -1 and span_end != -1:
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

        cleaned_explanation = (llm_response[:span_start] + llm_response[span_end:]).strip()
    else:
        cleaned_explanation = llm_response.strip()

    # Clean residual quiz section headings and intro text (e.g. "### Quiz", "To help you check your understanding...")
    cleaned_explanation = re.sub(r"(?i)\n?\s*#{1,3}\s*Quiz[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*To help you check your understanding[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*Here are (some|\d+)?\s*(questions|multiple-choice questions)[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"(?i)\n?\s*Test your understanding[\s\S]*$", "", cleaned_explanation).strip()
    cleaned_explanation = re.sub(r"```json[\s\S]*?```", "", cleaned_explanation, flags=re.IGNORECASE).strip()

    # Fallback explanation text if cleaned_explanation is empty
    if not cleaned_explanation or len(cleaned_explanation) < 15:
        topic_disp = target_topic or "the requested topic"
        cleaned_explanation = f"### Concept Overview: {topic_disp}\n\nBelow is an interactive quiz generated specifically for **{topic_disp}** to test your understanding. Complete all 5 questions below!"

    def repair_and_parse_quiz_json(raw_str: str):
        if not raw_str:
            return None
        cleaned = re.sub(r",\s*([\]\}])", r"\1", raw_str)
        cleaned = re.sub(r"\}\s*\{", "}, {", cleaned)

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        try:
            return json.loads(raw_str)
        except Exception:
            pass

        raw_questions = []
        block_splits = re.split(r"(?i)[\"']question[\"']\s*:", raw_str)

        if len(block_splits) > 1:
            for block in block_splits[1:]:
                q_text_match = re.search(r"^\s*[\"']([\s\S]*?)[\"']\s*,\s*[\"']", block)
                if not q_text_match:
                    q_text_match = re.search(r"^\s*[\"']([\s\S]*?)[\"']\s*,", block)

                q_text = q_text_match.group(1).strip() if q_text_match else ""

                opts_match = re.search(r"(?i)[\"']options[\"']\s*:\s*\[([\s\S]*?)\]", block)
                options = []
                if opts_match:
                    opts_str = opts_match.group(1)
                    options = re.findall(r"[\"']([\s\S]*?)[\"']", opts_str)
                    options = [o.strip() for o in options if o.strip()]

                corr_match = re.search(r"(?i)[\"']correct_answer[\"']\s*:\s*[\"']([\s\S]*?)[\"']", block)
                corr_ans = corr_match.group(1).strip() if corr_match else (options[0] if options else "")

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

    raw_quiz = None
    if json_str:
        data = repair_and_parse_quiz_json(json_str)
        if isinstance(data, list):
            raw_quiz = data
        elif isinstance(data, dict):
            raw_quiz = data.get("quiz") or data.get("questions")
            if not raw_quiz and "question" in data:
                raw_quiz = [data]

    # GUARANTEE: If LLM failed to produce a valid quiz, generate high-quality fallback quiz for the topic
    if not raw_quiz or not isinstance(raw_quiz, list) or len(raw_quiz) == 0:
        raw_quiz = generate_fallback_quiz(target_topic, subject)

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

    # Extra safety check: if still empty for any reason, generate fallback
    if len(safe_questions) == 0:
        fallback_raw = generate_fallback_quiz(target_topic, subject)
        for idx, q_item in enumerate(fallback_raw):
            safe_questions.append({
                "id": idx,
                "question": q_item["question"],
                "options": q_item["options"]
            })
            private_questions.append({
                "id": idx,
                "question": q_item["question"],
                "options": q_item["options"],
                "correct_answer": q_item["correct_answer"],
                "explanation": q_item["explanation"]
            })

    quiz_id = f"quiz_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    # Store private quiz data server-side
    QUIZ_STORE[quiz_id] = {
        "quiz_id": quiz_id,
        "topic": target_topic,
        "student_id": student_id,
        "subject": subject,
        "questions": private_questions,
        "created_at": time.time()
    }

    return cleaned_explanation, safe_questions, quiz_id, None

def evaluate_quiz(quiz_id: str, answers: list, student_id: str = "STU001", subject: str = "operating_systems", topic: str = None) -> dict:
    """
    Evaluates student quiz submission server-side.
    Marks target topic as COMPLETE in database ONLY when score_percentage > 70.
    """
    if not quiz_id or quiz_id not in QUIZ_STORE:
        return {
            "status": "error",
            "message": "Quiz session expired or not found. Please generate a new quiz.",
            "passed": False,
            "score": 0,
            "total": 5,
            "percentage": 0,
            "topic_completed": False
        }

    quiz_data = QUIZ_STORE[quiz_id]
    private_questions = quiz_data.get("questions", [])
    target_topic = topic or quiz_data.get("topic") or "General"
    target_subject = subject or quiz_data.get("subject") or "operating_systems"

    total = len(private_questions)
    if total == 0:
        return {
            "status": "error",
            "message": "Empty quiz questions.",
            "passed": False,
            "score": 0,
            "total": 0,
            "percentage": 0,
            "topic_completed": False
        }

    correct_count = 0
    detailed_results = []

    for idx, q_item in enumerate(private_questions):
        options = q_item.get("options", [])
        correct_ans_str = str(q_item.get("correct_answer", "")).strip()

        stu_ans_val = answers[idx] if isinstance(answers, list) and idx < len(answers) else None

        student_selected_text = ""
        if isinstance(stu_ans_val, int) and 0 <= stu_ans_val < len(options):
            student_selected_text = options[stu_ans_val]
        elif stu_ans_val is not None:
            student_selected_text = str(stu_ans_val).strip()

        # Robust answer comparison
        is_correct = False
        s_norm = student_selected_text.strip().lower()
        c_norm = correct_ans_str.strip().lower()

        if s_norm and c_norm:
            if s_norm == c_norm:
                is_correct = True
            elif c_norm in ["0", "1", "2", "3"] and str(stu_ans_val) == c_norm:
                is_correct = True
            elif c_norm in ["a", "b", "c", "d"] and isinstance(stu_ans_val, int):
                mapped_letter = chr(ord("a") + stu_ans_val)
                if mapped_letter == c_norm:
                    is_correct = True

        if is_correct:
            correct_count += 1

        detailed_results.append({
            "question_index": idx,
            "question": q_item.get("question", ""),
            "options": options,
            "student_answer": student_selected_text or "No answer selected",
            "correct_answer": correct_ans_str,
            "is_correct": is_correct,
            "explanation": q_item.get("explanation", "")
        })

    score_percentage = (correct_count / total) * 100.0

    # REQUIREMENT 9: Topic is marked completed ONLY when score_percentage > 70
    is_passed = score_percentage > 70

    topic_completed = False
    if is_passed and target_topic:
        from student_database import mark_topic_as_learned
        mark_topic_as_learned(student_id, target_topic, subject=target_subject)
        topic_completed = True

    # Determine next recommended topic using existing course graph and prerequisite relationships
    next_rec = None
    try:
        from prerequisite_engine import get_next_topic_recommendation
        next_rec = get_next_topic_recommendation(
            topic_name=target_topic,
            subject_id=target_subject,
            student_id=student_id
        )
    except Exception as e:
        print(f"Notice: Could not get next topic recommendation: {e}")

    return {
        "status": "success",
        "quiz_id": quiz_id,
        "topic": target_topic,
        "student_id": student_id,
        "subject": target_subject,
        "score": correct_count,
        "total": total,
        "percentage": round(score_percentage, 1),
        "passed": is_passed,
        "topic_completed": topic_completed,
        "results": detailed_results,
        "next_topic": next_rec.get("topic") if next_rec else None,
        "next_topic_name": next_rec.get("topic_name") if next_rec else None,
        "next_topic_description": next_rec.get("description", "") if next_rec else ""
    }



# ============================================================
# ============================================================
# CHECK KB AVAILABILITY
# ============================================================

def check_subject_kb_availability(subject):
    from topic_identifier import normalize_subject_id
    norm_sub = normalize_subject_id(subject)
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kb_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
                if norm_sub in kb_data or subject in kb_data:
                    sub_data = kb_data.get(norm_sub) or kb_data.get(subject) or {}
                    status_val = str(sub_data.get("status") or sub_data.get("kb_status") or "").lower()
                    pdf_uploaded = sub_data.get("pdf_uploaded", False)
                    if status_val == "ready" and pdf_uploaded:
                        return True
                    else:
                        return False
        except Exception:
            pass

    # Fallback check against ChromaDB collection count directly
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db"))
        col_names = [f"{norm_sub}_knowledge_base", f"{subject}_knowledge_base"]
        if norm_sub in ["operating_systems", "os"]:
            col_names.append("os_knowledge_base")
        for col_name in set(col_names):
            try:
                c = client.get_collection(col_name)
                if c and c.count() > 0:
                    return True
            except Exception:
                pass
    except Exception:
        pass

    return False


# ============================================================
# PROCESS QUERY
# ============================================================

def find_relevant_topic_images(topic=None, query=None, subject="operating_systems"):
    images_found = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    q_str = str(query or "").lower()
    t_str = str(topic or "").lower()
    
    requested_image = any(w in q_str for w in ["image", "img", "diagram", "figure", "picture", "photo", "flowchart", "show", "draw", "visualize"])

    diagram_map = [
        {
            "keys": ["process_state", "process state", "state transition", "process states"],
            "rel_path": "images/os_unit1/page_3_img_3.jpeg",
            "caption": "Process State Transition Diagram (New, Running, Waiting, Ready, Terminated)"
        },
        {
            "keys": ["pcb", "process control block", "task control block"],
            "rel_path": "images/os_unit1/page_10_img_1.jpeg",
            "caption": "Process Control Block (PCB) Structure & Registers"
        },
        {
            "keys": ["context_switch", "context switching", "cpu switch"],
            "rel_path": "images/os_unit1/page_13_img_1.jpeg",
            "caption": "Diagram of CPU Context Switch between Processes"
        },
        {
            "keys": ["process_creation", "process tree", "parent process", "fork"],
            "rel_path": "images/os_unit1/page_20_img_2.jpeg",
            "caption": "Process Hierarchy & Tree Structure Diagram"
        },
        {
            "keys": ["queue", "scheduling queue", "ready queue", "device queue"],
            "rel_path": "images/os_unit1/page_25_img_1.jpeg",
            "caption": "Process Scheduling Queues (Job Queue, Ready Queue, Device Queue)"
        },
        {
            "keys": ["cpu_scheduling", "cpu scheduler", "preemptive", "non-preemptive", "scheduling algorithm", "fcfs", "sjf"],
            "rel_path": "images/os_unit1/page_28_img_1.jpeg",
            "caption": "CPU Scheduling Architecture & Dispatcher Workflow"
        },
        {
            "keys": ["round_robin", "gantt chart", "gantt", "turnaround time", "waiting time"],
            "rel_path": "images/os_unit1/page_34_img_1.jpeg",
            "caption": "CPU Scheduling Criteria & Execution Timeline Diagram"
        }
    ]

    from retrieve import is_valid_display_image

    for item in diagram_map:
        # Strictly match candidate diagram keys against the detected topic string t_str
        matches = any(k in t_str for k in item["keys"])
        if matches:
            full_p = os.path.join(root_dir, item["rel_path"])
            # Ensure file exists and passes blank/white/tiny image validation check
            if is_valid_display_image(full_p):
                images_found.append({
                    "url": f"/images/os_unit1/{os.path.basename(full_p)}",
                    "caption": item["caption"],
                    "is_requested": requested_image
                })

    return images_found


def process_query(
    query=None,
    images=None,
    student_id=STUDENT_ID,
    subject="operating_systems",
    level="beginner"
):
    print()
    print("=" * 80)
    print(f"PRAGTUTOR MULTIMODAL BACKEND (Subject: {subject}, Level: {level})")
    print("=" * 80)

    # Step 0: Check KB Availability (DO NOT CALL RETRIEVE/LLM IF UNAVAILABLE)
    if not check_subject_kb_availability(subject):
        print(f"⚠️ Knowledge base not available for subject: {subject}")
        return {
            "status": "kb_unavailable",
            "subject": subject,
            "message": "PDFs have not been uploaded by your teachers for this subject yet."
        }

    # Step 0.5: Multimodal Processing
    mm_context = process_multimodal_inputs(query=query, images=images)

    print()
    print("User Text Query:", mm_context["raw_query"] if mm_context["raw_query"] else "[None provided]")
    if mm_context["has_images"]:
        print(f"Attached Images: {mm_context['num_images']} image(s)")
        if mm_context["ocr_text"]:
            print("Extracted OCR Text Preview:", mm_context["ocr_text"][:200] + "...")

    # ========================================================
    # STEP 1: TOPIC IDENTIFICATION
    # ========================================================

    print()
    print("STEP 1: Topic Identification")

    topic_result = identify_topic(
        mm_context,
        subject=subject
    )

    target_topic = topic_result.get("topic")
    confidence = topic_result.get("confidence", 0.0)

    # Check for unlabelled image with low classification confidence
    is_unlabelled = mm_context.get("has_images") and not mm_context.get("raw_query")
    if is_unlabelled and (not target_topic or confidence < 0.35):
        print("⚠️ Low-confidence image topic classification fallback triggered.")
        return {
            "status": "low_confidence",
            "topic": "Topic Unclear",
            "topic_id": "unidentified",
            "topic_name": "Topic Unclear",
            "topic_confidence": 0,
            "level": level,
            "completedPrereqs": [],
            "missingPrereqs": [],
            "learningPath": [],
            "sources": [],
            "images": [],
            "answer": "I couldn't confidently identify the topic from this image. Please provide the topic or a short question about the image."
        }

    if not target_topic:
        target_topic = "General Concept"

    print(
        "Identified Topic:",
        target_topic
    )

    print(
        "Confidence:",
        f"{confidence:.4f}"
    )

    # ========================================================
    # STEP 2: PREREQUISITE ANALYSIS
    # ========================================================

    print()
    print("STEP 2: Prerequisite Analysis")

    prerequisite_result = (
        find_missing_prerequisites(

            student_id,

            target_topic,

            subject_id=subject

        )
    )

    missing_prerequisites = (
        prerequisite_result[
            "missing_prerequisites"
        ]
    )

    graph = (
        prerequisite_result[
            "graph"
        ]
    )

    # ========================================================
    # STEP 3: PERSONALIZED LEARNING PATH
    # ========================================================

    print()
    print(
        "STEP 3: Personalized Learning Path"
    )

    learning_path = generate_learning_path(

        target_topic,

        missing_prerequisites,

        graph

    )

    for index, topic in enumerate(

        learning_path,

        start=1

    ):

        print(
            f"{index}. {topic}"
        )

    # ========================================================
    # STEP 4: RAG RETRIEVAL & DIAGRAM MATCHING
    # ========================================================

    print()
    print("STEP 4: RAG Retrieval")

    retrieved_content = retrieve(
        mm_context,
        top_k=TOP_K,
        subject=subject
    )

    print(
        "Retrieved chunks:",
        len(retrieved_content)
    )

    retrieved_images = retrieve_relevant_images(
        query=mm_context,
        subject=subject,
        target_topic=target_topic,
        retrieved_chunks=retrieved_content,
        top_k=3
    )

    if not retrieved_images:
        retrieved_images = find_relevant_topic_images(
            topic=target_topic,
            query=mm_context.get("raw_query") or query,
            subject=subject
        )

    # ========================================================
    # STEP 5: BUILD TUTOR CONTEXT
    # ========================================================

    print()
    print("STEP 5: Building Tutor Context")

    student_completed = list(
        prerequisite_result.get(
            "completed_topics",
            prerequisite_result.get("student_completed", [])
        )
    )

    all_prerequisites = list(
        prerequisite_result.get(
            "all_prerequisites",
            []
        )
    )

    # ========================================================
    # STEP 6: BUILD DYNAMIC PROMPT & LLM PAYLOAD
    # ========================================================

    print()
    print("STEP 6: Building Dynamic Prompt & Multimodal Payload")

    dynamic_prompt = build_dynamic_prompt(

        query=mm_context,

        topic=target_topic,

        topic_confidence=topic_result[
            "confidence"
        ],

        student_completed=
            student_completed,

        missing_prerequisites=
            missing_prerequisites,

        learning_path=
            learning_path,

        retrieved_content=
            retrieved_content,

        multimodal_context=
            mm_context,

        subject=
            subject,

        level=
            level
    )

    multimodal_llm_payload = build_multimodal_llm_payload(
        dynamic_prompt,
        mm_context
    )

    # Generate response via LLM service
    llm_response = generate_response(
        dynamic_prompt,
        multimodal_payload=multimodal_llm_payload,
        multimodal_context=mm_context
    )

    # Parse 5-question personalized quiz from LLM response (strips quiz JSON codeblock from llm_response)
    cleaned_explanation, safe_quiz, quiz_id, quiz_msg = parse_quiz_from_llm_response(
        llm_response=llm_response,
        target_topic=target_topic,
        student_id=student_id,
        subject=subject
    )
    llm_response = cleaned_explanation

    # Extract Mermaid diagram if generated by LLM
    import re
    generated_visual = None
    if llm_response and "```mermaid" in llm_response.lower():
        mermaid_match = re.search(r"```mermaid\s*([\s\S]*?)\s*```", llm_response, re.IGNORECASE)
        if mermaid_match:
            mermaid_code = mermaid_match.group(1).strip()
            generated_visual = {
                "enabled": True,
                "type": "flowchart",
                "format": "mermaid",
                "content": mermaid_code
            }

    # Determine next recommended topic using existing course graph and prerequisite relationships
    next_rec = None
    try:
        from prerequisite_engine import get_next_topic_recommendation
        next_rec = get_next_topic_recommendation(
            topic_name=target_topic,
            subject_id=subject,
            student_id=student_id
        )
    except Exception as e:
        print(f"Notice: Could not determine next topic recommendation: {e}")

    # ========================================================
    # BUILD FINAL CONTEXT
    # ========================================================

    context = {

        "status":
            "success",

        "query":
            query,

        "level":
            level,

        "multimodal_context":
            mm_context,

        "topic":
            target_topic,

        "topic_confidence":
            topic_result[
                "confidence"
            ],

        "all_prerequisites":
            all_prerequisites,

        "student_completed":
            student_completed,

        "missing_prerequisites":
            missing_prerequisites,

        "learning_path":
            learning_path,

        "retrieved_content":
            retrieved_content,

        "retrieved_images":
            retrieved_images,

        "generated_visual":
            generated_visual,

        "dynamic_prompt":
            dynamic_prompt,

        "multimodal_llm_payload":
            multimodal_llm_payload,

        "llm_response":
            llm_response,

        "quiz":
            safe_quiz,

        "quiz_id":
            quiz_id,

        "quiz_message":
            quiz_msg,

        "next_topic":
            next_rec.get("topic") if next_rec else None,

        "next_topic_name":
            next_rec.get("topic_name") if next_rec else None,

        "next_topic_description":
            next_rec.get("description", "") if next_rec else ""
    }

    # Record query history in MongoDB student_progress
    try:
        from student_database import update_student_progress_query
        update_student_progress_query(
            student_id=student_id,
            subject=subject,
            query_text=query or "Image query",
            topic=target_topic
        )
    except Exception as e:
        print(f"Notice: Could not log query to student_progress: {e}")

    # ========================================================
    # RETURN
    # ========================================================

    return context


# ============================================================
# DISPLAY CONTEXT
# ============================================================

def display_context(
    context
):

    print()
    print("=" * 80)
    print("PRAGTUTOR BACKEND SUMMARY")
    print("=" * 80)

    print()
    print("Query:", context["query"])

    mm_ctx = context.get("multimodal_context", {})
    if mm_ctx.get("has_images"):
        print(f"Attached Images: {mm_ctx['num_images']} image(s)")

    print("Identified Topic:", context["topic"])
    print(f"Topic Confidence: {context['topic_confidence']:.4f}")

    if context.get("missing_prerequisites"):
        print("Missing Prerequisites:", context["missing_prerequisites"])
    if context.get("learning_path"):
        print("Personalized Learning Path:", context["learning_path"])

    print()
    print("=" * 80)
    print("🎓 TUTOR ANSWER (LLM GENERATED RESPONSE)")
    print("=" * 80)
    print()
    print(context.get("llm_response"))
    print()
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("PRAGTUTOR MULTIMODAL BACKEND INTERACTIVE TERMINAL")
    print("=" * 80)
    print("Instructions:")
    print("  - Type your question directly (e.g. 'What is a process control block?')")
    print("  - To attach an image, add '+ <image_path>' (e.g. 'Explain this + images/sample.jpg')")
    print("  - Or type an image path directly to ask a visual question")
    print("  - Type 'exit' to quit")
    print("=" * 80)

    while True:

        user_input = input(
            "\nEnter question (or 'exit'): "
        ).strip()

        if user_input.lower() == "exit":

            print(
                "\nPragTutor backend stopped."
            )

            break

        if not user_input:

            print(
                "Please enter a question or image path."
            )

            continue

        query = user_input
        images = None

        # Check if user passed '+' for image path (e.g. "What is this? + image.jpg")
        if "+" in user_input:
            parts = user_input.split("+", 1)
            query = parts[0].strip()
            img_candidate = parts[1].strip()
            if img_candidate:
                images = [img_candidate]
        # Check if user input is an image file path directly
        elif os.path.exists(user_input):
            query = "Explain the concepts shown in this attached image."
            images = [user_input]

        try:

            context = process_query(
                query=query,
                images=images
            )

            if context["topic"] is None:

                print()
                print(
                    "Could not identify "
                    "the topic confidently."
                )

                continue

            display_context(
                context
            )

        except Exception as error:

            print()
            print(
                "ERROR:",
                error
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()