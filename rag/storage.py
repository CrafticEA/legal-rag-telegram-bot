import os

BASE_STORAGE = "data/cases"


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