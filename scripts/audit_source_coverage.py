"""Compare every PDF page with Markdown; low correspondence is a review flag.

This is a phrase correspondence check, not proof of completeness or correctness.
Independent OCR and embedded PDF text both have errors. Illustrations and maps
are not checked by text matching.
"""
import collections
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def words(text):
    text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return re.findall(r"[a-z0-9]+", html.unescape(text).casefold())


def grams(tokens, size):
    return [tuple(tokens[i:i+size]) for i in range(len(tokens)-size+1)]


def main():
    inventory = json.loads((ROOT / "reports/ocr-review/pdf-inventory.json").read_text(encoding="utf-8"))
    results = []
    for book in inventory:
        path = ROOT / "sources-markdown" / book["markdown"]
        md_tokens = words(path.read_text(encoding="utf-8"))
        md_grams = set(grams(md_tokens, 5))
        native = json.loads((ROOT / "tmp/pdfs/text" / (path.stem + ".json")).read_text(encoding="utf-8"))
        scan_path = ROOT / "tmp/pdfs/scans" / path.stem / "ocr.json"
        scans = json.loads(scan_path.read_text(encoding="utf-8")) if scan_path.exists() else []
        scanned = {int(Path(p["image"]).stem): p["text"] for p in scans}
        pages = []
        for p in native:
            n = p["pdf_page"]
            text = scanned.get(n, p["text"])
            tokens = words(text)
            phrases = set(grams(tokens, 5))
            matched = phrases & md_grams
            fraction = len(matched) / len(phrases) if phrases else None
            flag = len(tokens) >= 150 and fraction < 0.35
            pages.append(dict(pdf_page=n, text_method="independent Windows OCR" if n in scanned else "embedded PDF text",
                              source_words=len(tokens), unique_five_word_phrases=len(phrases),
                              matched_phrases=len(matched), phrase_correspondence=round(fraction,4) if fraction is not None else None,
                              needs_completeness_review=flag,
                              first_source_words=" ".join(tokens[:45]) if flag else None))
        results.append(dict(file=path.name, pdf_pages=len(native), independently_ocr_checked_pages=len(scanned),
                            pages_flagged=sum(p["needs_completeness_review"] for p in pages), pages=pages))
        print(f"{path.name}: {results[-1]['pages_flagged']}/{len(pages)} pages have low phrase correspondence", flush=True)
    (ROOT / "reports/ocr-review/source-coverage.json").write_text(json.dumps(dict(
        method="Unique five-word phrases per source page matched anywhere in the Markdown; flag pages with >=150 words and <35% matches",
        limitation="A match does not verify numerical values, reading order, page completeness, or image content. A flag is not proof of missing text.",
        files=results), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
