
from transformers.models.auto.tokenization_auto import AutoTokenizer

from app.core.config import settings


def chunk_text(
    text: str,
    model_name: str = settings.EMBEDDING_MODEL_NAME,
    chunk_size: int = 512,
    overlap: int = 102
) -> list[str]:
    """Split text into overlapping chunks using a HuggingFace tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(text, padding=True, truncation=True, add_special_tokens=False)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i : i + chunk_size]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        i += chunk_size - overlap
    return chunks
