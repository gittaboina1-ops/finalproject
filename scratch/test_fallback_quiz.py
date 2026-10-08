import sys
import os
import json

def generate_fallback_quiz(target_topic: str, subject: str = "operating_systems"):
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

def test_fallback():
    deadlock_quiz = generate_fallback_quiz("Deadlock")
    assert len(deadlock_quiz) == 5
    assert deadlock_quiz[0]["question"].startswith("Which")
    
    general_quiz = generate_fallback_quiz("CPU Scheduling")
    assert len(general_quiz) == 5
    assert "CPU Scheduling" in general_quiz[0]["question"]
    print("Fallback quiz generator test passed!")

if __name__ == "__main__":
    test_fallback()
