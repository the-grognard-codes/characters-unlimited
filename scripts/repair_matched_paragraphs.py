"""Apply manually reviewed paragraph recoveries bounded by matching source phrases.

The independent OCR supplies missing words. Every existing numeric token is
preserved. Native text with interleaved columns was rejected during review.
"""
import json
import re
from repair_source_passages import ROOT, replace, save_repairs


def main():
    approved = {
        ("Heroes Unlimited - Powers Unlimited 2.md",79): {},
        ("Rifts - Ultimate Edition.md",23): {"spe- Cies": "species"},
        ("Rifts - Ultimate Edition.md",34): {},
        ("Rifts - Ultimate Edition.md",52): {},
        ("Rifts - Ultimate Edition.md",82): {},
        ("Rifts - Ultimate Edition.md",148): {"bit Of": "bit of"},
        ("Rifts - Ultimate Edition.md",193): {},
        ("Rifts - Ultimate Edition.md",195): {"Ilit Points": "Hit Points"},
        ("Rifts - Ultimate Edition.md",218): {"'Phis": "This", "tour times": "four times", "för each": "for each"},
        ("Rifts - Ultimate Edition.md",226): {},
        ("Rifts - World Book 07 - Underseas.md",76): {"irnpressions": "impressions"},
    }
    proposals = json.loads((ROOT / "reports/ocr-review/paragraph-candidates.json").read_text(encoding="utf-8"))
    for rec in proposals:
        if len(rec['matches']) != 1:
            continue
        match = rec['matches'][0]
        key = (rec['file'],match['pdf_page'])
        if key not in approved:
            continue
        assert match['numbers_unchanged']
        after = match['after']
        for before, corrected in approved[key].items():
            assert before in after
            after = after.replace(before,corrected)
        assert re.findall(r'\d+',rec['before']) == re.findall(r'\d+',after)
        replace(rec['file'],rec['before'],after,match['pdf_page'],None,
                "Recovered unreadable words from independent source-page OCR between matching eight-word endpoints; manually reviewed continuous paragraph and preserved all numerical tokens. Fixed OCR errors in otherwise unchanged words using the original clear text. Printed page not independently recorded.")
    assert len(approved) == 11
    save_repairs(ROOT / "reports/ocr-review/source-repairs-08.json")


if __name__=='__main__':main()
