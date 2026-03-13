import json
import os
import threading

import faiss

BASE_STORAGE = "data/cases"

_INDEX_CACHE = {}
_CHUNKS_CACHE = {}
_CACHE_LOCK = threading.Lock()


def get_case_path(chat_id, case_id):
    path = os.path.join(
        BASE_STORAGE,
        str(chat_id),
        str(case_id)
    )
    os.makedirs(path, exist_ok=True)
    return path


def get_index_path(chat_id, case_id):
    return os.path.join(
        get_case_path(chat_id, case_id),
        "faiss.index"
    )


def get_chunks_path(chat_id, case_id):
    return os.path.join(
        get_case_path(chat_id, case_id),
        "chunks.jsonl"
    )


def load_chunks_file(path):
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def get_case_resources(chat_id, case_id, force_reload=False):
    key = (str(chat_id), str(case_id))

    with _CACHE_LOCK:
        if force_reload or key not in _INDEX_CACHE or key not in _CHUNKS_CACHE:
            index_path = get_index_path(chat_id, case_id)
            chunks_path = get_chunks_path(chat_id, case_id)

            _INDEX_CACHE[key] = faiss.read_index(index_path)
            _CHUNKS_CACHE[key] = load_chunks_file(chunks_path)

        return _INDEX_CACHE[key], _CHUNKS_CACHE[key]


def invalidate_case_cache(chat_id, case_id):
    key = (str(chat_id), str(case_id))

    with _CACHE_LOCK:
        _INDEX_CACHE.pop(key, None)
        _CHUNKS_CACHE.pop(key, None)