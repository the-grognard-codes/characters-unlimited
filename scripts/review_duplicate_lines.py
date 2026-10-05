"""Remove doubled OCR lines only when independently extracted PDF text supports them.

The evidence is a single occurrence of the entire retained phrase on a source
page, and no doubled occurrence on any page. Short dotted leaders are excluded.
The full changes, page locators and hashes are retained for review.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def source_pages(stem):
    native = json.loads((ROOT / "tmp/pdfs/text" / (stem + ".json")).read_text(encoding="utf-8"))
    scan_path = ROOT / "tmp/pdfs/scans" / stem / "ocr.json"
    scans = json.loads(scan_path.read_text(encoding="utf-8")) if scan_path.exists() else []
    scanned = {int(Path(p["image"]).stem): p["text"] for p in scans}
    return [(p["pdf_page"], normalized(scanned.get(p["pdf_page"], p["text"])),
             "independent Windows OCR" if p["pdf_page"] in scanned else "PDF embedded text") for p in native]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    report = ROOT / "reports/ocr-review" / ("duplicate-repairs.json" if args.apply else "duplicate-candidates.json")
    if args.apply and report.exists():
        raise ValueError("Applied repair log already exists")
    records, files, pending = [], [], []
    for path in sorted((ROOT / "sources-markdown").glob("*.md")):
        raw = path.read_bytes()
        lines = raw.decode("utf-8").splitlines(keepends=True)
        pages = source_pages(path.stem)
        count = 0
        for i, line in enumerate(lines):
            match = re.fullmatch(r"(#{1,6} |[-*] )?(.{12,}?)\s+\2", line.strip())
            if not match:
                continue
            retained = match[2]
            needle = normalized(retained)
            if len(needle) < 12 or len(re.findall(r"[A-Za-z]{2,}", retained)) < 2:
                continue
            matches = [(n, text.count(needle), method) for n, text, method in pages if needle in text]
            confirmed = bool(matches) and all(n == 1 for _, n, _ in matches)
            after = (match[1] or "") + retained
            rec = dict(file=path.name, line=i + 1, before=line.rstrip("\r\n"), after=after,
                       confirmed=confirmed,
                       source_pages=[dict(pdf_page=n, occurrences=c, method=m) for n,c,m in matches])
            records.append(rec)
            if confirmed:
                count += 1
                lines[i] = after + ("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
        new = "".join(lines).encode("utf-8")
        files.append(dict(file=path.name, repairs=count, before_sha256=hashlib.sha256(raw).hexdigest(),
                          after_sha256=hashlib.sha256(new).hexdigest()))
        pending.append((path, raw, new))
        print(f"{path.name}: {count} confirmed doubled lines", flush=True)
    assert all(p.read_bytes() == raw for p, raw, _ in pending)
    report.write_text(json.dumps(dict(applied=args.apply, files=files, candidates=records),
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.apply:
        for path, raw, new in pending:
            assert path.read_bytes() == raw
            if raw != new:
                path.write_bytes(new)


if __name__ == "__main__":
    main()
