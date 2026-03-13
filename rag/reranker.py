import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "Qwen/Qwen3-Reranker-0.6B"

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    torch_dtype=torch.float16
).to(device)


def rerank(query, chunks, top_k=6):

    pairs = [[query, c["text"]] for c in chunks]

    scores = []

    with torch.no_grad():

        for i in range(0, len(pairs), 4):

            batch = pairs[i:i+4]

            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(device)

            logits = model(**inputs).logits.squeeze()

            scores.extend(logits.cpu().numpy())

    for i, s in enumerate(scores):
        chunks[i]["rerank_score"] = float(s)

    return sorted(
        chunks,
        key=lambda x: x["rerank_score"],
        reverse=True
    )[:top_k]