import os
import sys
import json

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pragtutor_backend import process_query

def run_tests():
    print("=" * 80)
    print("RUNNING PRAGTUTOR SYSTEM VERIFICATION TESTS WITH OPENROUTER HTTP API")
    print("=" * 80)

    # Test 1: General Query (What is a process in operating systems?)
    print("\n--- TEST 1: What is a process in operating systems? ---")
    res1 = process_query(query="What is a process in operating systems?", level="beginner")
    print(f"Status: {res1.get('status')}")
    print(f"Identified Topic: {res1.get('topic')}")
    print(f"Missing Prerequisites: {res1.get('missing_prerequisites')}")
    print(f"Learning Path: {res1.get('learning_path')}")
    print(f"Retrieved Chunks: {len(res1.get('retrieved_content', []))}")
    print(f"LLM Answer Preview:\n{str(res1.get('llm_response'))[:300]}...\n")

    # Test 2: Beginner Level
    print("\n--- TEST 2: Beginner Level Test ---")
    res2 = process_query(query="Explain process states", level="beginner")
    print(f"Identified Topic: {res2.get('topic')}")
    print(f"LLM Answer Preview:\n{str(res2.get('llm_response'))[:300]}...\n")

    # Test 3: Intermediate Level
    print("\n--- TEST 3: Intermediate Level Test ---")
    res3 = process_query(query="Explain Process Control Block PCB structure", level="intermediate")
    print(f"Identified Topic: {res3.get('topic')}")
    print(f"LLM Answer Preview:\n{str(res3.get('llm_response'))[:300]}...\n")

    # Test 4: Advanced Level
    print("\n--- TEST 4: Advanced Level Test ---")
    res4 = process_query(query="How does CPU context switching work in operating systems?", level="advanced")
    print(f"Identified Topic: {res4.get('topic')}")
    print(f"LLM Answer Preview:\n{str(res4.get('llm_response'))[:300]}...\n")

    # Test 5: Image Functionality Test
    print("\n--- TEST 5: Image Functionality Test ---")
    img_path = os.path.join(root_dir, "images", "os_unit1", "page_10_img_1.jpeg")
    if os.path.exists(img_path):
        res5 = process_query(query="Explain this diagram", images=[img_path], level="intermediate")
        print(f"Identified Topic: {res5.get('topic')}")
        print(f"LLM Answer Preview:\n{str(res5.get('llm_response'))[:300]}...\n")
    else:
        print("Image file not found for Test 5")

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
