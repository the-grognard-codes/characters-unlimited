"""Source census and review candidates; extraction never implies rule acceptance."""

import argparse
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class SourceInventory:
    @staticmethod
    def scan(markdown_directory: str | Path, pdf_directory: str | Path | None = None) -> dict:
        directory = Path(markdown_directory)
        if not directory.is_dir():
            raise ValueError("Markdown source directory does not exist")
        originals = {}
        if pdf_directory is not None:
            originals = {path.stem.casefold(): path for path in Path(pdf_directory).iterdir() if path.suffix.casefold() == ".pdf"}
        books, candidates = [], []
        for source in sorted(directory.glob("*.md")):
            before = source.stat()
            content = source.read_bytes()
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError(f"Source changed during scanning; retry: {source.name}")
            digest = hashlib.sha256(content).hexdigest()
            book_id = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")
            game = "rifts" if source.stem.startswith("Rifts") else "heroes-unlimited" if source.stem.startswith(("Heroes Unlimited", "Aliens Unlimited")) else "unknown"
            original = originals.get(source.stem.casefold())
            lines = content.decode("utf-8-sig").splitlines()
            headings = []
            for line_number, line in enumerate(lines, start=1):
                match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
                if match:
                    title = html.unescape(match[1]).strip()
                    headings.append((line_number, title))
            for index, (line_number, title) in enumerate(headings):
                end = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
                normalized = title.lower().replace(".", "")
                if re.search(r"\bO\.?\s*C\.?\s*C\.?\b", title, re.IGNORECASE):
                    kind = "occ"
                elif re.search(r"\bR\.?\s*C\.?\s*C\.?\b", title, re.IGNORECASE):
                    kind = "rcc"
                elif any(word in normalized for word in ("race", "species")):
                    kind = "race"
                else:
                    kind = "section"
                identifier = hashlib.sha256(f"{book_id}:{line_number}:{title}".encode()).hexdigest()[:20]
                candidates.append({
                    "id": identifier, "book_id": book_id, "title": title, "kind": kind,
                    "line": line_number, "end_line": end, "status": "needs-review",
                    "source_sha256": digest, "dependencies": [], "evidence": [],
                })
            books.append({
                "id": book_id, "filename": source.name, "game": game, "sha256": digest,
                "bytes": len(content), "candidate_count": len(headings), "review_complete": False,
                "original_pdf": original.name if original else None,
                "pdf_sha256": hashlib.sha256(original.read_bytes()).hexdigest() if original else None,
                "findings": ["Heading extraction is provisional. Audit prose, tables, aliases, and missing dependencies before closing coverage."],
            })
        return {
            "schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(),
            "books": books, "candidates": candidates,
            "summary": {"books": len(books), "candidates": len(candidates), "fully_automated": 0, "books_reviewed": 0},
        }

    @staticmethod
    def save(inventory: dict, destination: str | Path):
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def load() -> dict:
        target = Path(__file__).parent / "data" / "source-inventory.json"
        if not target.exists():
            return {"books": [], "candidates": [], "summary": {"books": 0, "candidates": 0, "fully_automated": 0, "books_reviewed": 0}}
        return json.loads(target.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Inventory Markdown sections without accepting their mechanics")
    parser.add_argument("markdown_directory", type=Path)
    parser.add_argument("--pdf-directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "source-inventory.json")
    args = parser.parse_args()
    inventory = SourceInventory.scan(args.markdown_directory, args.pdf_directory)
    SourceInventory.save(inventory, args.output)
    print(json.dumps(inventory["summary"]))


if __name__ == "__main__":
    main()
