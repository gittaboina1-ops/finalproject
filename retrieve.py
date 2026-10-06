import os
import chromadb

from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(ROOT_DIR, "chroma_db")

COLLECTION_NAME = "os_knowledge_base"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


# ============================================================
# LOAD EMBEDDING MODEL (REUSE GLOBAL INSTANCE IF AVAILABLE)
# ============================================================

try:
    from topic_identifier import model as embedding_model
except Exception:
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

COLLECTION_CACHE = {}
VISUAL_EMBS_CACHE = {}

# ============================================================
# LOAD EXISTING COLLECTION (CACHED FOR PERFORMANCE)
# ============================================================

def get_subject_collection(subject_name=None):
    if not subject_name:
        subject_name = COLLECTION_NAME
    clean_sub = str(subject_name).lower().replace(" ", "_").replace("-", "_")
    target_name = f"{clean_sub}_knowledge_base" if not clean_sub.endswith("_knowledge_base") else clean_sub
    
    if clean_sub in COLLECTION_CACHE:
        return COLLECTION_CACHE[clean_sub]

    col = None
    # Try normalized target name (e.g. operating_systems_knowledge_base)
    try:
        col = client.get_collection(name=target_name)
    except Exception:
        pass

    # Try os_knowledge_base alias
    if not col and clean_sub in ["operating_systems", "os"]:
        try:
            col = client.get_collection(name="os_knowledge_base")
        except Exception:
            pass

    # Fallback to default or create if empty
    if not col:
        try:
            col = client.get_collection(name=COLLECTION_NAME)
        except Exception:
            col = client.get_or_create_collection(name=target_name)

    if col and col.count() > 0:
        COLLECTION_CACHE[clean_sub] = col
    return col

# Default collection reference for compatibility
try:
    collection = get_subject_collection(COLLECTION_NAME)
except Exception:
    collection = None

# ============================================================
# RETRIEVE RELEVANT CONTENT
# ============================================================

def retrieve(
    query,
    top_k=TOP_K,
    subject=None
):
    """
    Retrieve the most relevant chunks
    from the PragTutor knowledge base.

    Parameters:
        query   -> student's question
        top_k   -> number of chunks to retrieve
        subject -> target subject domain (e.g. 'operating_systems', 'dbms')
    """

    target_collection = get_subject_collection(subject) if subject else collection
    if target_collection is None:
        return []

    # --------------------------------------------------------
    # Convert query into embedding
    # --------------------------------------------------------

    if isinstance(query, dict):
        search_text = query.get("combined_text") or query.get("raw_query") or ""
    else:
        search_text = str(query or "")

    if not search_text.strip():
        return []

    query_embedding = (
        embedding_model
        .encode(search_text)
        .tolist()
    )

    # --------------------------------------------------------
    # Search ChromaDB
    # --------------------------------------------------------

    if target_collection.count() == 0:
        return []

    actual_k = min(top_k, target_collection.count())
    results = target_collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"]
    )

    # --------------------------------------------------------
    # Extract results
    # --------------------------------------------------------

    documents = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    retrieved_results = []
    for i in range(len(documents)):
        meta = metadatas[i] if i < len(metadatas) else {}
        result = {
            "content": documents[i],
            "unit": meta.get("unit", "General"),
            "page": meta.get("page", 1),
            "source": meta.get("source", "Document"),
            "distance": distances[i] if i < len(distances) else 0.0
        }
        retrieved_results.append(result)

    return retrieved_results


# ============================================================
# RETRIEVE RELEVANT VISUAL IMAGES
# ============================================================

from sklearn.metrics.pairwise import cosine_similarity
from visual_processor import load_visual_metadata

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
    "se": "software_engineering",
    "software_engineering": "software_engineering"
}

def normalize_subject_id(subject_id):
    if not subject_id:
        return "operating_systems"
    clean = str(subject_id).lower().strip().replace("-", "_")
    return SUBJECT_ID_MAP.get(clean, clean)

TOPIC_CATEGORIES = {
    "deadlock": ["deadlock", "deadlocks", "banker", "wait-for", "resource allocation graph", "deadlock detection", "deadlock prevention", "deadlock avoidance", "deadlock recovery"],
    "paging_memory": ["paging", "page table", "page replacement", "virtual memory", "segmentation", "tlb", "frame", "lru", "fifo page", "demand paging", "page fault"],
    "cpu_scheduling": ["cpu scheduling", "gantt", "fcfs", "sjf", "round robin", "priority scheduling", "dispatcher", "burst time", "turnaround time"],
    "process_concepts": ["process state", "pcb", "process control block", "task control block", "context switch", "state transition"],
    "synchronization": ["synchronization", "semaphore", "mutex", "critical section", "peterson", "dining philosophers", "monitors"],
    "file_systems": ["file system", "disk scheduling", "c-scan", "scan disk", "inode", "raid", "fcfs disk"],
    "networking": ["osi model", "tcp/ip", "routing", "subnet", "ip address", "packet", "router"],
    "dbms": ["sql", "normalization", "transaction", "acid", "relational", "schema"],
    "data_structures": ["binary tree", "bst", "graph algorithm", "linked list", "stack", "queue"]
}

def get_topic_keywords(target_topic):
    if not target_topic:
        return []
    
    t_clean = str(target_topic).lower().replace("_", " ").strip()
    
    topic_keywords_map = {
        "cpu scheduling": ["cpu scheduling", "scheduling", "gantt", "gantt chart", "fcfs", "sjf", "round robin", "priority scheduling", "dispatcher", "turnaround time", "waiting time", "burst time"],
        "process states": ["process state", "state transition", "ready queue", "running", "waiting", "terminated", "suspended", "pcb"],
        "process control block": ["process control block", "pcb", "task control block", "registers", "process table"],
        "deadlock": ["deadlock", "deadlocks", "banker", "banker's algorithm", "safe state", "wait-for", "resource allocation graph", "deadlock detection", "deadlock prevention", "deadlock avoidance", "deadlock recovery"],
        "deadlocks": ["deadlock", "deadlocks", "banker", "banker's algorithm", "safe state", "wait-for", "resource allocation graph", "deadlock detection", "deadlock prevention", "deadlock avoidance", "deadlock recovery"],
        "memory management": ["memory management", "paging", "page table", "virtual memory", "segmentation", "tlb", "frame", "allocation"],
        "paging": ["paging", "page table", "page fault", "frame", "tlb", "virtual memory", "page replacement"],
        "page replacement": ["page replacement", "fifo page", "lru page", "optimal page", "page fault", "frame", "paging"],
        "virtual memory": ["virtual memory", "paging", "demand paging", "page replacement", "lru", "fifo", "page fault"],
        "context switch": ["context switch", "context switching", "cpu switch"],
        "synchronization": ["synchronization", "semaphore", "mutex", "critical section", "peterson", "monitor"],
        "file systems": ["file system", "directory", "disk scheduling", "c-scan", "scan", "fcfs disk", "raid", "inode"],
        "osi model": ["osi", "osi model", "layers", "transport layer", "network layer", "data link", "physical layer"],
        "routing": ["routing", "ip address", "subnet", "router", "packet", "dijkstra"],
        "binary tree": ["binary tree", "bst", "traversal", "tree", "node"],
        "graph algorithms": ["graph", "bfs", "dfs", "dijkstra", "shortest path"],
        "sql queries": ["sql", "query", "select", "join", "table", "schema", "relational"],
        "normalization": ["normalization", "1nf", "2nf", "3nf", "bcnf", "dependency"],
        "transactions": ["transaction", "acid", "concurrency", "lock", "serializability"]
    }
    
    kws = set()
    if t_clean:
        kws.add(t_clean)
        if t_clean.endswith("s") and len(t_clean) > 4:
            kws.add(t_clean[:-1])
        for word in t_clean.split():
            if len(word) > 3 and word not in ["with", "from", "that", "this", "some", "type"]:
                kws.add(word)

    for top_key, kw_list in topic_keywords_map.items():
        if top_key in t_clean or t_clean in top_key:
            for kw in kw_list:
                kws.add(kw)
                
    return list(kws)

IMAGE_VALID_CACHE = {}

def is_valid_display_image(img_path: str, min_width: int = 60, min_height: int = 60) -> bool:
    """
    Validates if an image file exists, can be opened by PIL, meets minimum dimensions,
    and is not blank, completely white, or corrupted (cached for fast performance).
    """
    if not img_path:
        return False
    full_path = img_path if os.path.isabs(img_path) else os.path.join(ROOT_DIR, img_path.lstrip("/\\"))
    if full_path in IMAGE_VALID_CACHE:
        return IMAGE_VALID_CACHE[full_path]

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        IMAGE_VALID_CACHE[full_path] = False
        return False
    try:
        from PIL import Image, ImageStat
        with Image.open(full_path) as im:
            w, h = im.size
            if w < min_width or h < min_height:
                IMAGE_VALID_CACHE[full_path] = False
                return False
            # Check standard deviation of grayscale pixel intensity
            stat = ImageStat.Stat(im.convert("L"))
            stddev = stat.stddev[0]
            mean = stat.mean[0]
            # Solid/blank image check: stddev < 5.0 and pure white/black background
            if stddev < 5.0 and (mean > 240.0 or mean < 15.0):
                IMAGE_VALID_CACHE[full_path] = False
                return False
            IMAGE_VALID_CACHE[full_path] = True
            return True
    except Exception:
        IMAGE_VALID_CACHE[full_path] = False
        return False

def retrieve_relevant_images(
    query,
    subject=None,
    target_topic=None,
    retrieved_chunks=None,
    top_k=3
):
    """
    Retrieves the most relevant visual images/diagrams from the subject's visual metadata repository.
    Strictly filters to ensure retrieved images match the identified topic or retrieved RAG content.
    Excludes blank, white, corrupted, or invalid images.
    """
    norm_sub = normalize_subject_id(subject)
    visual_meta = load_visual_metadata(norm_sub)
    if not visual_meta:
        return []

    if isinstance(query, dict):
        search_text = query.get("combined_text") or query.get("raw_query") or ""
    else:
        search_text = str(query or "")

    topic_clean = (target_topic or "").lower().replace("_", " ").strip()
    topic_kws = get_topic_keywords(target_topic)

    # Determine target category for topic conflict checking
    target_cat = None
    if topic_clean:
        for cat_name, cat_kws in TOPIC_CATEGORIES.items():
            if any(ckw in topic_clean or topic_clean in ckw for ckw in cat_kws):
                target_cat = cat_name
                break

    # Extract pages and sources of retrieved text RAG chunks for page-level matching
    chunk_page_sources = set()
    if retrieved_chunks and isinstance(retrieved_chunks, list):
        for c in retrieved_chunks:
            if isinstance(c, dict):
                src = c.get("source") or c.get("metadata", {}).get("source")
                pg = c.get("page") or c.get("metadata", {}).get("page")
                if src and pg:
                    chunk_page_sources.add((str(src).lower(), int(pg)))

    search_prompt = f"{topic_clean} {search_text}".strip()
    q_emb = embedding_model.encode([search_prompt], convert_to_numpy=True, normalize_embeddings=True)

    if norm_sub not in VISUAL_EMBS_CACHE or VISUAL_EMBS_CACHE[norm_sub][0] != len(visual_meta):
        img_texts = [f"Caption: {item.get('caption', '')}. Context: {item.get('page_context', '')[:300]}" for item in visual_meta]
        img_embs = embedding_model.encode(img_texts, convert_to_numpy=True, normalize_embeddings=True)
        VISUAL_EMBS_CACHE[norm_sub] = (len(visual_meta), img_embs)
    else:
        img_embs = VISUAL_EMBS_CACHE[norm_sub][1]

    similarities = cosine_similarity(q_emb, img_embs)[0]

    scored_items = []
    for idx, item in enumerate(visual_meta):
        # Filter out blank, white, tiny, or corrupted images
        img_rel_p = item.get("path") or ""
        if not is_valid_display_image(img_rel_p):
            continue

        sim_score = float(similarities[idx])

        cap_lower = item.get("caption", "").lower()
        ctx_lower = item.get("page_context", "").lower()
        rel_topics = [t.lower().replace("_", " ") for t in item.get("related_topics", [])]
        item_src = str(item.get("source", "")).lower()
        item_pg = int(item.get("page", 0))
        item_path = str(item.get("path", "")).lower()

        item_full_text = f"{cap_lower} {ctx_lower} {' '.join(rel_topics)} {item_path}"

        # 1. TOPIC CONFLICT CHECK:
        # If candidate text explicitly belongs to a DIFFERENT topic category
        # and has NO keywords from the detected target topic, REJECT it.
        has_conflict = False
        if target_cat:
            target_kws = TOPIC_CATEGORIES[target_cat]
            has_target_kws = any(tkw in item_full_text for tkw in target_kws) or any(kw in item_full_text for kw in topic_kws)
            if not has_target_kws:
                for cat_name, cat_kws in TOPIC_CATEGORIES.items():
                    if cat_name != target_cat:
                        if any(ckw in item_full_text for ckw in cat_kws):
                            has_conflict = True
                            break
        if has_conflict:
            continue

        # 2. CHECK TOPIC KEYWORD MATCHES
        topic_match_found = False
        topic_match_score = 0.0
        for kw in topic_kws:
            if any(kw in r_top or r_top in kw for r_top in rel_topics):
                topic_match_score += 0.40
                topic_match_found = True
            if kw in cap_lower or kw in item_path:
                topic_match_score += 0.40
                topic_match_found = True
            elif kw in ctx_lower:
                topic_match_score += 0.25
                topic_match_found = True

        # 3. CHECK PAGE MATCH (with RAG text chunks retrieved for this topic)
        same_page_match = False
        if chunk_page_sources:
            for (c_src, c_pg) in chunk_page_sources:
                if (c_src in item_src or item_src in c_src) and abs(c_pg - item_pg) <= 1:
                    same_page_match = True
                    break

        # 4. STRICT FILTER CONDITION:
        # Require EITHER a topic keyword match OR a same-page RAG match.
        # Vector similarity alone is NEVER trusted to include an image.
        if not (topic_match_found or same_page_match):
            continue

        score = sim_score + topic_match_score + (0.30 if same_page_match else 0.0)

        if score < 0.45:
            continue

        scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen_paths = set()
    for score, item in scored_items:
        if item["path"] in seen_paths:
            continue
        seen_paths.add(item["path"])

        results.append({
            "image_id": item.get("image_id"),
            "url": item.get("url"),
            "path": item.get("path"),
            "unit": item.get("unit"),
            "page": item.get("page"),
            "source": item.get("source"),
            "caption": item.get("caption"),
            "related_topic": target_topic or (item.get("related_topics", ["general"])[0] if item.get("related_topics") else "general"),
            "relevance_score": round(score, 4)
        })

        if len(results) >= top_k:
            break

    return results

def retrieve_multimodal(
    query,
    top_k=TOP_K,
    subject=None,
    target_topic=None
):
    """
    Returns both relevant text RAG chunks and extracted PDF images.
    """
    text_results = retrieve(query=query, top_k=top_k, subject=subject)
    image_results = retrieve_relevant_images(query=query, subject=subject, target_topic=target_topic, retrieved_chunks=text_results, top_k=3)
    return {
        "text_results": text_results,
        "image_results": image_results
    }



# ============================================================
# DISPLAY RETRIEVED RESULTS
# ============================================================

def display_results(
    query,
    results
):

    print()
    print("=" * 80)

    print(
        f"QUERY: {query}"
    )

    print("=" * 80)

    for i, result in enumerate(
        results,
        start=1
    ):

        print()

        print(
            f"RESULT {i}"
        )

        print("-" * 80)

        print(
            f"Unit: "
            f"{result['unit']}"
        )

        print(
            f"Page: "
            f"{result['page']}"
        )

        print(
            f"Source: "
            f"{result['source']}"
        )

        print(
            f"Distance: "
            f"{result['distance']:.4f}"
        )

        print()

        print(
            result["content"]
        )

        print("-" * 80)


# ============================================================
# MAIN - TEST RETRIEVER
# ============================================================

def main():

    print()
    print("=" * 80)
    print("PRAGTUTOR RAG RETRIEVER")
    print("=" * 80)

    while True:

        query = input(
            "\nEnter your question "
            "(type 'exit' to stop): "
        )

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if query.lower().strip() == "exit":

            print(
                "\nRetriever stopped."
            )

            break

        # ----------------------------------------------------
        # Empty query
        # ----------------------------------------------------

        if not query.strip():

            print(
                "Please enter a question."
            )

            continue

        # ----------------------------------------------------
        # Retrieve
        # ----------------------------------------------------

        results = retrieve(
            query
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        display_results(
            query,
            results
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()