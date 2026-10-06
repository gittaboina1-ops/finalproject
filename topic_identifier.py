import os
import json
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSE_TOPICS_FILE = os.path.join(BASE_DIR, "data", "course_topics.json")

TOPIC_CACHE = {}

SUBJECT_ID_MAP = {
    "os": "operating_systems",
    "operating systems": "operating_systems",
    "operating_systems": "operating_systems",
    "cn": "computer_networks",
    "computer networks": "computer_networks",
    "computer_networks": "computer_networks",
    "ds": "data_structures",
    "data structures": "data_structures",
    "data_structures": "data_structures",
    "dbms": "dbms",
    "database management systems": "dbms",
    "se": "software_engineering",
    "software engineering": "software_engineering",
    "software_engineering": "software_engineering"
}

def normalize_subject_id(subject_id):
    if not subject_id:
        return "operating_systems"
    clean = str(subject_id).lower().strip().replace("-", "_")
    clean_space = clean.replace("_", " ")
    if clean in SUBJECT_ID_MAP:
        return SUBJECT_ID_MAP[clean]
    if clean_space in SUBJECT_ID_MAP:
        return SUBJECT_ID_MAP[clean_space]
    return clean.replace(" ", "_")

def load_topics(subject_id=None):
    if not subject_id:
        subject_id = "operating_systems"
    norm_sub = normalize_subject_id(subject_id)
    if norm_sub in TOPIC_CACHE:
        return TOPIC_CACHE[norm_sub]

    topics = []
    raw_data = None
    
    # 1. Try subject specific prerequisites file
    prereq_file = os.path.join(BASE_DIR, "data", f"prerequisites_{norm_sub}.json")
    if os.path.exists(prereq_file):
        try:
            with open(prereq_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"Error loading {prereq_file}: {e}")

    # 2. Try subject specific course topics file
    if not raw_data:
        topic_file = os.path.join(BASE_DIR, "data", f"course_topics_{norm_sub}.json")
        if os.path.exists(topic_file):
            try:
                with open(topic_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                print(f"Error loading {topic_file}: {e}")

    # 3. Fallback to default COURSE_TOPICS_FILE or global prerequisites.json
    if not raw_data and os.path.exists(COURSE_TOPICS_FILE):
        try:
            with open(COURSE_TOPICS_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            pass

    if not raw_data:
        global_prereqs = os.path.join(BASE_DIR, "prerequisites.json")
        if os.path.exists(global_prereqs):
            try:
                with open(global_prereqs, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception:
                pass

    if isinstance(raw_data, dict):
        if "units" in raw_data:
            for unit_id, unit_data in raw_data["units"].items():
                for topic, information in unit_data.get("topics", {}).items():
                    topics.append({
                        "topic": topic,
                        "unit": unit_id,
                        "description": information.get("description", "") if isinstance(information, dict) else "",
                        "parent_topic": information.get("parent_topic", None) if isinstance(information, dict) else None
                    })
        else:
            seen_topics = set()
            def add_t(t_name, desc="", parent=None):
                if t_name and t_name not in seen_topics:
                    seen_topics.add(t_name)
                    topics.append({
                        "topic": t_name,
                        "unit": "1",
                        "description": desc or "",
                        "parent_topic": parent
                    })

            if "topic_prerequisites" in raw_data and isinstance(raw_data["topic_prerequisites"], dict):
                for t_name, t_val in raw_data["topic_prerequisites"].items():
                    desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                    add_t(t_name, desc)

            if "prerequisites" in raw_data:
                p_data = raw_data["prerequisites"]
                if isinstance(p_data, dict):
                    for t_name, t_val in p_data.items():
                        desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                        add_t(t_name, desc)
                elif isinstance(p_data, list):
                    for item in p_data:
                        if isinstance(item, dict):
                            t_name = item.get("topic") or item.get("name")
                            if t_name:
                                add_t(t_name, item.get("description", ""))
                        elif isinstance(item, str):
                            add_t(item)

            if "topics" in raw_data and isinstance(raw_data["topics"], dict):
                for t_name, t_val in raw_data["topics"].items():
                    desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                    add_t(t_name, desc)

            for k, v in raw_data.items():
                if k not in ["subject", "course", "source_basis", "topic_prerequisites", "prerequisites", "topics", "units", "version"]:
                    desc = v.get("description", "") if isinstance(v, dict) else ""
                    add_t(k, desc)

    # Compute topic texts and embeddings
    if topics and 'model' in globals():
        t_texts = [create_topic_text(t) for t in topics]
        t_embeddings = model.encode(t_texts, convert_to_numpy=True, normalize_embeddings=True)
    else:
        t_texts = []
        t_embeddings = []

    res = {
        "topics": topics,
        "texts": t_texts,
        "embeddings": t_embeddings
    }
    TOPIC_CACHE[norm_sub] = res
    return res

MODEL_NAME = "all-MiniLM-L6-v2"

TOP_K = 5

CONFIDENCE_THRESHOLD = 0.35


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    text = text.lower()

    text = text.replace("'", "")
    text = text.replace("’", "")

    text = text.replace("_", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CREATE SEMANTIC REPRESENTATION
# ============================================================

def create_topic_text(topic_data):

    topic = normalize_text(
        topic_data["topic"]
    )

    description = normalize_text(
        topic_data["description"]
    )

    parent = topic_data[
        "parent_topic"
    ]

    if parent:

        parent = normalize_text(
            parent
        )

        return (
            f"Topic: {topic}. "
            f"Parent topic: {parent}. "
            f"Description: {description}"
        )

    return (
        f"Topic: {topic}. "
        f"Description: {description}"
    )


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print()
print("=" * 70)
print("PRAGTUTOR - TOPIC IDENTIFIER")
print("=" * 70)

print()
print("Loading embedding model...")

try:
    model = SentenceTransformer(MODEL_NAME, local_files_only=True)
except Exception:
    model = SentenceTransformer(MODEL_NAME)

print(
    "Embedding model loaded."
)


# ============================================================
# LOAD TOPICS
# ============================================================

print()
print("Loading default course topics...")

default_topic_data = load_topics()
topics = default_topic_data["topics"]
topic_embeddings = default_topic_data["embeddings"]

print(
    "Topics loaded:",
    len(topics)
)


# ============================================================
# IDENTIFY TOPIC
# ============================================================

def is_generic_or_empty_query(raw_q: str) -> bool:
    if not raw_q:
        return True
    clean_q = str(raw_q).lower().strip().rstrip("?.!")
    generic_phrases = {
        "explain this", "what is this", "explain image", "explain the image",
        "explain attached image", "explain the attached image", "analyze this",
        "analyze this image", "explain", "describe this", "what is shown here",
        "explain diagram", "explain this diagram", "tell me about this",
        "what does this mean", "explain the diagram", "explain attached diagram"
    }
    return clean_q in generic_phrases or len(clean_q) < 3

def identify_topic(
    query,
    top_k=TOP_K,
    subject=None
):
    query_text = ""
    mm_context = None

    if isinstance(query, dict):
        mm_context = query
        query_text = query.get("combined_text") or query.get("raw_query") or ""
    else:
        query_text = str(query or "")

    subj_data = load_topics(subject)
    cur_topics = subj_data["topics"]
    cur_embeddings = subj_data["embeddings"]

    if not cur_topics or len(cur_embeddings) == 0:
        return {
            "query": query_text,
            "topic": None,
            "unit": None,
            "confidence": 0.0,
            "status": "no_topics_available",
            "top_matches": []
        }

    raw_q = mm_context.get("raw_query") if mm_context else (query_text if not isinstance(query, dict) else "")
    has_attached_image = bool(mm_context and mm_context.get("has_images"))
    is_generic_query = is_generic_or_empty_query(raw_q)
    
    # Task 1 & Part 1 Decision Tree:
    # 1. Text only -> Normal topic identification (No Vision)
    # 2. Text + Image -> Normal topic identification if text query is specific (No Vision for topic ID)
    # 3. Image + Useful OCR text -> Normal topic identification using OCR text (No Vision)
    # 4. Image only + OCR failed/insufficient -> OpenAI Vision topic identification
    ocr_text_clean = (mm_context.get("ocr_text") if mm_context else "").strip()
    has_useful_ocr = len(ocr_text_clean) > 15 and not is_generic_or_empty_query(ocr_text_clean)
    
    # Use OpenAI Vision for topic identification ONLY when image exists, text query is empty/generic, and OCR text is insufficient
    use_vision_for_topic = has_attached_image and is_generic_query and not has_useful_ocr

    if use_vision_for_topic:
        try:
            # Use OpenRouter vision to identify course topic from visual content
            from llm_service import generate_response
            topic_names = [t["topic"] for t in cur_topics]
            subj_display = (subject or "Operating Systems").replace("_", " ").title()
            vision_prompt = (
                f"The image is from an {subj_display} educational course.\n"
                f"Identify the most likely topic represented by this image.\n"
                f"Prefer an existing topic from the course topic list:\n"
                f"{', '.join(topic_names)}\n\n"
                f"Instructions:\n"
                f"1. Select the single course topic from the list that best matches the diagram/image.\n"
                f"2. Return ONLY the exact topic name from the allowed topics list above."
            )
            
            payloads = mm_context.get("llm_image_payloads") or []
            messages = [{"role": "user", "content": [{"type": "text", "text": vision_prompt}] + payloads}]
            llm_topic_raw = generate_response(prompt=vision_prompt, multimodal_payload=messages, multimodal_context=mm_context).strip()
                
            # Match OpenRouter Vision response directly to allowed course topic list (avoid duplicate LLM calls)
            if llm_topic_raw and "UNKNOWN" not in llm_topic_raw.upper() and not llm_topic_raw.startswith("[OpenRouter LLM Error"):
                for t_obj in cur_topics:
                    t_clean = normalize_text(t_obj["topic"])
                    raw_clean = normalize_text(llm_topic_raw)
                    if t_obj["topic"].lower() == llm_topic_raw.lower() or t_clean == raw_clean or t_clean in raw_clean or raw_clean in t_clean:
                        return {
                            "query": raw_q or "[Unlabelled Image Classification]",
                            "topic": t_obj["topic"],
                            "unit": t_obj["unit"],
                            "confidence": 0.90,
                            "reason": f"Identified via OpenRouter Vision visual content analysis: {t_obj['topic']}",
                            "status": "identified_via_vision",
                            "top_matches": [{"topic": t_obj["topic"], "unit": t_obj["unit"], "score": 0.90}]
                        }
            
            # If vision model cannot identify topic, return unlabelled fallback status
            return {
                "query": raw_q or "[Unlabelled Image Classification]",
                "topic": "Topic Unclear",
                "unit": None,
                "confidence": 0.0,
                "reason": "Could not confidently identify topic from image visual content.",
                "status": "unidentified_image",
                "top_matches": []
            }
        except Exception as v_err:
            print(f"Vision topic classification note: {v_err}")

    norm_q = normalize_text(query_text)

    query_embedding = model.encode(
        [norm_q],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    similarities = cosine_similarity(
        query_embedding,
        cur_embeddings
    )[0]

    scores = list(similarities)
    for idx, t_obj in enumerate(cur_topics):
        t_norm = normalize_text(t_obj["topic"])
        if len(t_norm) >= 3:
            pattern = r'\b' + re.escape(t_norm) + r'\b'
            if re.search(pattern, norm_q):
                scores[idx] = max(scores[idx], 0.95)
            elif t_norm in norm_q:
                scores[idx] = max(scores[idx], 0.88)

    import numpy as np
    ranked_indices = np.array(scores).argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        results.append({
            "topic": cur_topics[index]["topic"],
            "unit": cur_topics[index]["unit"],
            "description": cur_topics[index]["description"],
            "parent_topic": cur_topics[index]["parent_topic"],
            "score": float(scores[index])
        })

    best = results[0]

    return {
        "query": norm_q,
        "topic": best["topic"],
        "unit": best["unit"],
        "confidence": best["score"],
        "status": "identified",
        "top_matches": results
    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(result):

    print()
    print("=" * 70)
    print("TOPIC IDENTIFICATION RESULT")
    print("=" * 70)

    print()
    print("Query:")
    print(
        " ",
        result["query"]
    )

    print()

    if result["topic"]:

        print(
            "Identified Topic:"
        )

        print(
            " ",
            result["topic"]
        )

        print()

        print("Unit:")

        print(
            " ",
            result["unit"]
        )

        print()

        print("Confidence:")

        print(
            f"  {result['confidence']:.4f}"
        )

    else:

        print(
            "Could not confidently identify a topic."
        )

    print()
    print("Top Matches:")

    for index, match in enumerate(

        result["top_matches"],

        start=1

    ):

        print(

            f"  {index}. "
            f"{match['topic']} "
            f"({match['score']:.4f})"

        )

        if match["description"]:

            print(

                f"     {match['description']}"

            )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    while True:

        query = input(

            "\nEnter your question "
            "(type 'exit' to stop): "

        )

        if query.strip().lower() == "exit":

            print(
                "\nTopic identifier stopped."
            )

            break

        result = identify_topic(
            query
        )

        display_result(
            result
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()