"""
Improved sentence-aware chunker with paragraph boundary detection.
Splits on sentence/paragraph boundaries rather than raw character count,
preserving semantic meaning within each chunk.
"""
import re


def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    """
    Split text into chunks that respect sentence boundaries.
    - Splits on paragraph breaks first, then sentence breaks within large paragraphs.
    - Applies overlap by carrying the tail of the previous chunk into the next.
    """
    text = text.strip()
    if not text:
        return []

    # Normalise whitespace
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]

    # Within each paragraph further split on sentence endings to get finer pieces
    sentences: list[str] = []
    for para in paragraphs:
        # split on sentence-ending punctuation followed by whitespace
        parts = re.split(r'(?<=[.!?])\s+', para)
        sentences.extend([s.strip() for s in parts if s.strip()])

    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("size must be positive and overlap must be between 0 and size - 1")

    # A sentence may itself be larger than the configured limit (common in
    # extracted tables and OCR). Split those units with the same overlap
    # guarantee before sentence-aware packing.
    bounded_sentences: list[str] = []
    step = size - overlap
    for sentence in sentences:
        if len(sentence) <= size:
            bounded_sentences.append(sentence)
            continue
        for start in range(0, len(sentence), step):
            bounded_sentences.append(sentence[start:start + size])
            if start + size >= len(sentence):
                break

    # Greedily pack sentences into chunks of ≤ `size` characters
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in bounded_sentences:
        # Oversized sentence fragments are already overlapping, so emit them
        # directly instead of adding a second overlap layer.
        if len(sent) == size:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
            chunks.append(sent)
            continue
        if current_len + len(sent) + 1 > size and current:
            chunk_text_val = " ".join(current)
            chunks.append(chunk_text_val)
            # Retain only as much tail context as can fit beside the incoming
            # sentence. This keeps the hard upper bound even when individual
            # sentences are long.
            available_overlap = max(0, size - len(sent) - 1)
            retained = chunk_text_val[-min(overlap, available_overlap):].strip()
            current = [retained] if retained else []
            current_len = len(retained)

        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    # Final filter: remove whitespace-only or very short chunks
    return [c for c in chunks if len(c.strip()) > 80]
