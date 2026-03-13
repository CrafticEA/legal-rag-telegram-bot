import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

_MODEL = None
_TOKENIZER = None
_MODEL_NAME = "BAAI/bge-reranker-base"


def get_reranker():
    global _MODEL, _TOKENIZER

    if _MODEL is None or _TOKENIZER is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if device == "cuda" else torch.float32

        _TOKENIZER = AutoTokenizer.from_pretrained(_MODEL_NAME)

        _MODEL = AutoModelForSequenceClassification.from_pretrained(
            _MODEL_NAME,
            torch_dtype=torch_dtype
        ).to(device)

        _MODEL.eval()

    return _TOKENIZER, _MODEL


def rerank(query, chunks, top_k=6):
    if not chunks:
        return []

    try:
        tokenizer, model = get_reranker()
        device = next(model.parameters()).device

        pairs = [[query, c["text"]] for c in chunks]
        scores = []

        with torch.no_grad():
            for i in range(0, len(pairs), 4):
                batch = pairs[i:i + 4]

                inputs = tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(device)

                logits = model(**inputs).logits.squeeze(-1)
                scores.extend(logits.detach().cpu().numpy().tolist())

        for i, s in enumerate(scores):
            chunks[i]["rerank_score"] = float(s)

        return sorted(
            chunks,
            key=lambda x: x["rerank_score"],
            reverse=True
        )[:top_k]

    except Exception:
        return chunks[:top_k]