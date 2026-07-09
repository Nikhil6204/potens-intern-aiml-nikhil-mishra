"""
Run this once (and again any time data/docs/ changes) to (re)build the vector
store:

    python -m ingest.ingest

It also writes a registry.json mapping doc_id -> {source, title, num_chunks}
that the backend uses to list documents and to power the /contradict endpoint
(which needs to iterate all chunks belonging to a given doc_id).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.chunker import chunk_document
from ingest.embed_store import get_collection, add_chunks, PERSIST_DIR

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "registry.json")


def doc_id_from_filename(filename: str) -> str:
    return os.path.splitext(filename)[0]


def title_from_text(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return text[:60]


def main():
    print(f"Persisting vector store to: {PERSIST_DIR}")
    collection = get_collection(reset=True)

    registry = {}
    filenames = sorted(f for f in os.listdir(DOCS_DIR) if f.endswith(".md"))
    if len(filenames) < 5:
        print(f"WARNING: only {len(filenames)} documents found in {DOCS_DIR}; "
              f"the assignment asks for 5+.")

    total_chunks = 0
    for filename in filenames:
        path = os.path.join(DOCS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        doc_id = doc_id_from_filename(filename)
        chunks = chunk_document(doc_id, filename, text)
        add_chunks(collection, chunks)
        total_chunks += len(chunks)

        registry[doc_id] = {
            "source": filename,
            "title": title_from_text(text),
            "num_chunks": len(chunks),
            "chunk_ids": [c.chunk_id for c in chunks],
        }
        print(f"  ingested {filename}: {len(chunks)} chunks")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print(f"Done. {len(filenames)} documents, {total_chunks} chunks total.")
    print(f"Registry written to {REGISTRY_PATH}")


if __name__ == "__main__":
    main()
