"""Cache independent Windows OCR for scanned source PDF pages.

This does not replace the Markdown. Cached OCR is a locator and comparison
aid; repairs still require review against the PDF rendering.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tmp" / "ocr-deps"))
import pymupdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", help="A PDF filename stem; default: all scanned books")
    parser.add_argument("--pages", help="Comma-separated 1-based PDF page numbers")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "reports/ocr-review/pdf-inventory.json").read_text(encoding="utf-8"))
    for rec in inventory:
        if args.book and Path(rec["markdown"]).stem != args.book:
            continue
        if not args.book and rec["pages_with_embedded_text"]:
            continue
        doc = pymupdf.open(rec["pdf"])
        stem = Path(rec["markdown"]).stem
        folder = ROOT / "tmp/pdfs/scans" / stem
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "ocr.json"
        cached = json.loads(output.read_text(encoding="utf-8-sig")) if output.exists() else []
        if isinstance(cached, dict):
            cached = [cached]
        existing = {item["image"] for item in cached}
        page_numbers = [int(n) for n in args.pages.split(",")] if args.pages else range(1, len(doc) + 1)
        page_numbers = [n for n in page_numbers if f"{n:04d}.png" not in existing]
        for start in range(0, len(page_numbers), 20):
            numbers = page_numbers[start:start + 20]
            batch = folder / "batch"
            batch.mkdir(exist_ok=True)
            for number in numbers:
                doc[number - 1].get_pixmap(dpi=160).save(batch / f"{number:04d}.png")
            batch_output = batch / "ocr.json"
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(ROOT / "scripts/ocr_windows.ps1"), "-ImageDirectory", str(batch),
                            "-OutputPath", str(batch_output)], check=True, capture_output=True)
            items = json.loads(batch_output.read_text(encoding="utf-8-sig"))
            if isinstance(items, dict):
                items = [items]
            cached.extend(items)
            cached.sort(key=lambda item: item["image"])
            output.write_text(json.dumps(cached, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            # Each exact file was just generated in the validated scratch folder.
            for number in numbers:
                target = (batch / f"{number:04d}.png").resolve()
                assert target.parent == batch.resolve() and target.suffix == ".png"
                target.unlink()
            batch_output.unlink()
            print(f"{stem}: independent OCR cached for {len(cached)}/{len(doc)} pages", flush=True)


if __name__ == "__main__":
    main()
