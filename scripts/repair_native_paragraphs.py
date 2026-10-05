"""Apply eight HU2 paragraphs visually checked in isolated source text blocks."""
import json
from repair_source_passages import ROOT, replace, save_repairs


def main():
    corrections={
        30:{"01 -10":"01-10","Le. animal-like":"i.e. animal-like"},
        35:{},73:{"kmlh":"km/h"},89:{},
        226:{"1 0-1 5":"10-15"},
        249:{"1 35":"135","P .S.":"P.S."},
        258:{"1 1 2-1 44":"112-144","Ibs":"lbs"},
    }
    records=json.loads((ROOT/'reports/ocr-review/native-paragraph-candidates.json').read_text(encoding='utf-8'))
    count=0
    for rec in records:
        assert rec['file']=="Heroes Unlimited - RPG - 2E.md" and len(rec['matches'])==1
        m=rec['matches'][0];after=m['after']
        for before,new in corrections[m['pdf_page']].items():after=after.replace(before,new)
        replace(rec['file'],rec['before'],after,m['pdf_page'],None,
                "Restored garbled paragraph from a single-column embedded PDF text block; visually checked the rendered block, including superspeed +4 damage per 20 mph, Hurl Earth limits, and glue strength. Corrected extraction glyphs/spacing using the image.")
        count+=1
    assert count==8
    save_repairs(ROOT/'reports/ocr-review/source-repairs-09.json')


if __name__=='__main__':main()
