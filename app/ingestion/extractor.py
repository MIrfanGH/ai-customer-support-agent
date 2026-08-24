from pathlib import Path


def doc_extractor(doc_path: str) -> list[dict]:

    """
    Load all .md files from doc_path, extract raw text + basic metadata.
    Returns one dict per file — chunking.py will split each further.
    """

    docs = [] # List of dicts where, 1 dict = i complete document

    doc_dir = Path(doc_path)
    for path in sorted(doc_dir.glob("*.md")):  # sorted() -> keep files in consistent order across re-ingests
        # glob():  A method from Path class that searches for files, matching a pattern
        raw_text = path.read_text(encoding="utf-8")


        # pulling every line (across the corpus) starting with "# Title" in meta instead of leaving buried in content
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else ""
        title = first_line.lstrip("#").strip() if first_line.startswith("#") else path.stem


        doc = {  # One dictionary per file: holds filename, full path, raw content, and metadata (title + type)
            "source": path.stem,  # filename without extension       
            "source_path": str(path), 
            "content": raw_text, # "content" so it matches the Chunk.content column name,          
            "metadata": {
                "title": title,
                "doc_type": "support_doc",
            },
        }
        docs.append(doc)

    return docs


if __name__ == "__main__":
    import json
    print(json.dumps(doc_extractor("data/documents"), indent=2))

