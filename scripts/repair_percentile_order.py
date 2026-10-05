"""Sort intact percentile tables scrambled by OCR column order.

Only a run whose ranges cover 01-100 exactly once is changed. No words, ranges
or assignments are added/deleted. This does not repair missing table entries.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = re.compile(r"^(?:[-*] )?(\d{1,2})[-–](\d{1,2})(?:%|\s)")


def main():
    report = ROOT / "reports/ocr-review/percentile-order-repairs.json"
    if report.exists():
        raise ValueError("Applied log already exists")
    records, files, pending = [], [], []
    for path in sorted((ROOT / "sources-markdown").glob("*.md")):
        raw = path.read_bytes()
        # Split with separators retained so the exact original line layout is kept.
        parts = re.split(r"((?:\r?\n){2,})", raw.decode("utf-8"))
        i = 0
        while i < len(parts):
            items = []
            j = i
            while j < len(parts):
                m = ENTRY.match(parts[j])
                if not m:
                    break
                low, high = map(int, m.groups())
                high = high or 100
                if low < 1 or low > high:
                    break
                items.append((low, high, parts[j]))
                j += 2
            coverage = [n for low, high, _ in items for n in range(low, high+1)]
            if len(items) >= 4 and sorted(coverage) == list(range(1,101)) and items != sorted(items):
                before = "".join(parts[i:j-1])
                ordered = sorted(items)
                for offset, (_,_,body) in enumerate(ordered):
                    parts[i+2*offset] = body
                after = "".join(parts[i:j-1])
                assert sorted(re.findall(r"\d+", before)) == sorted(re.findall(r"\d+", after))
                assert sorted(x[2] for x in items) == sorted(x[2] for x in ordered)
                records.append(dict(file=path.name, line_before_patch="".join(parts[:i]).count("\n")+1,
                                    reason="Intact percentile run covers 01-100 exactly once; sorted existing entries without changing any assignment", before=before, after=after))
            i = max(i+2,j)
        new = "".join(parts).encode("utf-8")
        files.append(dict(file=path.name, before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest()))
        pending.append((path,raw,new))
    report.write_text(json.dumps(dict(files=files,repairs=records),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for path,raw,new in pending:
        assert path.read_bytes() == raw
        if raw != new:
            path.write_bytes(new)
    print(f"Reordered {len(records)} intact percentile runs")


if __name__ == "__main__":
    main()
