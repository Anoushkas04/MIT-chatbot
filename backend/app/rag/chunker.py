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

    # Greedily pack sentences into chunks of ≤ `size` characters
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) + 1 > size and current:
            chunk_text_val = " ".join(current)
            chunks.append(chunk_text_val)
            # Overlap: keep the last few sentences for context
            overlap_chars = 0
            overlap_sents: list[str] = []
            for s in reversed(current):
                overlap_chars += len(s)
                overlap_sents.insert(0, s)
                if overlap_chars >= overlap:
                    break
            current = overlap_sents
            current_len = sum(len(s) for s in current) + len(current)

        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    # Final filter: remove whitespace-only or very short chunks
    return [c for c in chunks if len(c.strip()) > 80]
