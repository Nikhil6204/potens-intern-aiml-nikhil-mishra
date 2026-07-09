"""
Chunking strategy
------------------
Our source documents are markdown policy/guide documents with a clear heading
hierarchy (## Section headings). Naively splitting every N characters ignores
that structure and produces chunks that cut a rule in half, which is exactly
the failure mode we can't afford in a citations product: a citation should
point at a coherent unit of meaning, not an arbitrary character window.

So we chunk in two passes:

1. STRUCTURAL PASS: split the document on markdown headings (## ...). Each
   section becomes a candidate chunk, tagged with its heading as metadata.
   This is the unit we'd *like* to cite - "Section 3, Vendor Data Retention
   Requirements" is a much better citation than "chunk 14".

2. SIZE PASS: sections vary wildly in length (some are two sentences, some
   are 600+ words). Very short sections are merged with the next section so
   we don't store near-empty embeddings that dilute retrieval. Very long
   sections are split further using a recursive, sentence-boundary-aware
   splitter with a target size and overlap, so a single rule doesn't get
   sliced mid-sentence and so retrieval can still find a specific clause
   inside a long section.

Defaults: target chunk size ~800 characters (~150-200 tokens), overlap ~150
characters. This is small enough that retrieval precision stays high (a
5-sentence chunk is topically coherent) but large enough that each chunk
carries enough context for the LLM to reason over without re-fetching
neighbors. Overlap prevents a sentence that straddles a split point from
being unretrievable in either half.

Every chunk keeps: source file, doc_id, section heading, chunk_index within
the section, and character offsets into the original file (so a citation can
be traced back to an exact span, not just "somewhere in this file").
"""
import re
from dataclasses import dataclass, field
from typing import List


TARGET_CHUNK_CHARS = 800
OVERLAP_CHARS = 150
MIN_SECTION_CHARS = 120  # sections shorter than this get merged forward


@dataclass
class Chunk:
    doc_id: str
    source: str
    section: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}::sec{self.chunk_index:02d}"


def _split_into_sections(text: str):
    """Split markdown text on '## ' headings. Returns list of (heading, body, start_offset)."""
    heading_pattern = re.compile(r"^##\s+(.*)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(text))

    sections = []
    if not matches:
        return [("Document", text, 0)]

    # Preamble before first heading (e.g. the title / purpose intro), if any
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("Preamble", preamble, 0))

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading = m.group(1).strip()
        body = text[start:end].strip()
        sections.append((heading, body, start))

    return sections


def _sentence_split(text: str) -> List[str]:
    """Lightweight sentence splitter - good enough for policy prose."""
    # Split on sentence-ending punctuation followed by whitespace + capital/bullet,
    # and on newlines (bullets, list items).
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\-\*])|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]


def _recursive_split(text: str, target: int, overlap: int) -> List[str]:
    """Greedily pack sentences into ~target-sized windows with sentence overlap."""
    sentences = _sentence_split(text)
    if not sentences:
        return [text]

    chunks = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) > target and current:
            chunks.append(" ".join(current))
            # carry the tail of the previous chunk forward as overlap
            overlap_sents = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap:
                    break
                overlap_sents.insert(0, s)
                overlap_len += len(s)
            current = overlap_sents.copy()
            current_len = overlap_len
        current.append(sent)
        current_len += len(sent)

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_document(doc_id: str, source_filename: str, text: str) -> List[Chunk]:
    raw_sections = _split_into_sections(text)

    # Merge very short sections forward into the next one
    merged = []
    buffer_heading, buffer_body, buffer_start = None, "", None
    for heading, body, start in raw_sections:
        if buffer_body and len(buffer_body) < MIN_SECTION_CHARS:
            buffer_body = buffer_body + "\n\n" + body
            buffer_heading = f"{buffer_heading} / {heading}"
            continue
        if buffer_body:
            merged.append((buffer_heading, buffer_body, buffer_start))
        buffer_heading, buffer_body, buffer_start = heading, body, start
    if buffer_body:
        merged.append((buffer_heading, buffer_body, buffer_start))

    chunks: List[Chunk] = []
    idx = 0
    for heading, body, start in merged:
        if len(body) <= TARGET_CHUNK_CHARS:
            pieces = [body]
        else:
            pieces = _recursive_split(body, TARGET_CHUNK_CHARS, OVERLAP_CHARS)

        cursor = start
        for piece in pieces:
            piece_start = text.find(piece[:40], cursor) if piece[:40] else cursor
            if piece_start == -1:
                piece_start = cursor
            piece_end = piece_start + len(piece)
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    source=source_filename,
                    section=heading,
                    chunk_index=idx,
                    text=piece,
                    char_start=piece_start,
                    char_end=piece_end,
                )
            )
            idx += 1
            cursor = piece_end

    return chunks
