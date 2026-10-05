"""Read source PDFs without modifying them; cache text and page inventory."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tmp" / "ocr-deps"))
import pymupdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_dir", type=Path)
    args = parser.parse_args()
    cache = ROOT / "tmp" / "pdfs" / "text"
    cache.mkdir(parents=True, exist_ok=True)
    inventory = []
    for md in sorted((ROOT / "sources-markdown").glob("*.md")):
        matches = [p for p in args.pdf_dir.iterdir()
                   if p.stem.casefold() == md.stem.casefold() and p.suffix.lower() == ".pdf"]
        if not matches:
            inventory.append(dict(markdown=md.name, pdf=None, status="missing source PDF"))
            continue
        assert len(matches) == 1
        pdf = matches[0]
        doc = pymupdf.open(pdf)
        pages = []
        for i, page in enumerate(doc, 1):
            text = page.get_text(sort=True)
            pages.append(dict(pdf_page=i, text=text))
        (cache / (md.stem + ".json")).write_text(
            json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        text_pages = sum(len(p["text"].strip()) >= 100 for p in pages)
        rec = dict(markdown=md.name, pdf=str(pdf),
                   pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                   pdf_pages=len(pages), pages_with_embedded_text=text_pages,
                   pages_needing_visual_or_ocr_review=[p["pdf_page"] for p in pages
                                                      if len(p["text"].strip()) < 100])
        inventory.append(rec)
        print(f"{md.name}: {len(pages)} pages; {text_pages} with embedded text", flush=True)
    output = ROOT / "reports" / "ocr-review" / "pdf-inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
