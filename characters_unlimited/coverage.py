"""Source census and review candidates; extraction never implies rule acceptance."""

import argparse
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4
from copy import deepcopy
from .option_audit import audited_coverage


class SourceGap(TypedDict):
    line: int
    end_line: int
    description: str


class SourceInventory:
    @staticmethod
    def with_verified_gaps(inventory, records):
        """Reconcile PDF findings with exact source fingerprints without editing books."""
        if not isinstance(records, list):
            raise ValueError('Verified source gaps must be a list')
        result = deepcopy(inventory)
        books = {book['id']: book for book in result['books']}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError('Verified source gap must be a record')
            if not isinstance(record.get('book_id'), str):
                raise ValueError('Verified source gap book identity must be text')
            book = books.get(record['book_id'])
            if (book is None or not book.get('pdf_sha256')
                    or record.get('markdown_sha256') != book['sha256']
                    or record.get('pdf_sha256') != book['pdf_sha256']):
                raise ValueError('Verified gap source changed or is unavailable; re-review its evidence')
            gap = record.get('gap')
            if (not isinstance(gap, dict) or type(gap.get('line')) is not int
                    or type(gap.get('end_line')) is not int or gap['line'] < 1
                    or gap['end_line'] < gap['line'] or not isinstance(gap.get('description'), str)
                    or not gap['description'].strip()):
                raise ValueError('Verified source gap needs a positive line range and description')
            last_line = max((candidate['end_line'] for candidate in result['candidates']
                             if candidate['book_id'] == book['id']), default=0)
            if gap['end_line'] > last_line:
                raise ValueError('Verified source gap range exceeds the scanned book')
            affected = [candidate for candidate in result['candidates']
                        if candidate['book_id'] == book['id']
                        and candidate['line'] <= gap['end_line'] and candidate['end_line'] >= gap['line']]
            if not affected:
                raise ValueError('Verified source gap range has no matching candidate')
            if gap not in book['source_gaps']:
                book['source_gaps'].append(deepcopy(gap))
            for candidate in affected:
                candidate['status'] = 'source-gap'
                if gap not in candidate['source_gaps']:
                    candidate['source_gaps'].append(deepcopy(gap))
        result['summary']['source_gaps'] = sum(len(book['source_gaps']) for book in result['books'])
        return result

    @staticmethod
    def scan(markdown_directory: str | Path, pdf_directory: str | Path | None = None) -> dict:
        directory = Path(markdown_directory)
        if not directory.is_dir():
            raise ValueError("Markdown source directory does not exist")
        originals = {}
        if pdf_directory is not None:
            originals = {path.stem.casefold(): path for path in Path(pdf_directory).iterdir() if path.suffix.casefold() == ".pdf"}
        books, candidates = [], []
        gap_count = 0
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
            text = '\n'.join(lines)
            gaps: list[SourceGap] = [{'line': text.count('\n', 0, match.start()) + 1,
                     'end_line': text.count('\n', 0, match.end()) + 1,
                     'description': ' '.join(match[1].split())}
                    for match in re.finditer(r'<!--\s*SOURCE GAP:\s*(.*?)-->', text, re.DOTALL | re.IGNORECASE)]
            gap_count += len(gaps)
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
                identifier = hashlib.sha256(f"{book_id}:{digest}:{line_number}:{title}".encode()).hexdigest()[:20]
                section_gaps = [gap for gap in gaps if gap['line'] <= end and gap['end_line'] >= line_number]
                candidates.append({
                    "id": identifier, "book_id": book_id, "title": title, "kind": kind,
                    "line": line_number, "end_line": end, "status": "source-gap" if section_gaps else "needs-review",
                    "source_gaps": section_gaps,
                    "source_sha256": digest, "dependencies": [], "evidence": [],
                })
            books.append({
                "id": book_id, "filename": source.name, "game": game, "sha256": digest,
                "bytes": len(content), "candidate_count": len(headings), "review_complete": False,
                "original_pdf": original.name if original else None,
                "pdf_sha256": hashlib.sha256(original.read_bytes()).hexdigest() if original else None,
                "source_gaps": gaps,
                "findings": ["Heading extraction is provisional. Audit prose, tables, aliases, and missing dependencies before closing coverage."],
            })
        return {
            "schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(),
            "books": books, "candidates": candidates,
            "summary": {"books": len(books), "candidates": len(candidates), "fully_automated": 0, "books_reviewed": 0,
                        "source_gaps": gap_count},
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
    def with_catalog(inventory, catalog):
        return audited_coverage(inventory, catalog)

    @staticmethod
    def load() -> dict:
        target = Path(__file__).parent / "data" / "source-inventory.json"
        if not target.exists():
            return SourceInventory.with_catalog(
                {"books": [], "candidates": [], "summary": {"books": 0, "candidates": 0, "fully_automated": 0, "books_reviewed": 0}},
                {"schema_version": 1, "entries": [], "findings": ["Source inventory is unavailable."]})
        inventory = json.loads(target.read_text(encoding="utf-8"))
        verified_gaps = json.loads((target.parent / 'verified-source-gaps.json').read_text(encoding='utf-8'))
        inventory = SourceInventory.with_verified_gaps(inventory, verified_gaps)
        catalog = json.loads((target.parent / 'canonical-options.json').read_text(encoding='utf-8'))
        return SourceInventory.with_catalog(inventory, catalog)


def main():
    parser = argparse.ArgumentParser(description="Inventory Markdown sections without accepting their mechanics")
    parser.add_argument("markdown_directory", type=Path)
    parser.add_argument("--pdf-directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "source-inventory.json")
    parser.add_argument('--verified-gaps', type=Path, help='Reconcile independently reviewed PDF gaps for this source set')
    args = parser.parse_args()
    inventory = SourceInventory.scan(args.markdown_directory, args.pdf_directory)
    if args.verified_gaps:
        inventory = SourceInventory.with_verified_gaps(inventory, json.loads(args.verified_gaps.read_text(encoding='utf-8')))
    SourceInventory.save(inventory, args.output)
    print(json.dumps(inventory["summary"]))


if __name__ == "__main__":
    main()
