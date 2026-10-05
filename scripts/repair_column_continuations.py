"""Restore HU2 paragraphs that continue across columns or pages."""
import json
from repair_source_passages import ROOT, replace, save_repairs


def main():
    records=json.loads((ROOT/'reports/ocr-review/column-paragraph-candidates.json').read_text(encoding='utf-8'))
    assert len(records)==6
    for rec in records:
        after=rec['after']
        for before,corrected in {
            '1 5%':'15%', 'concen- trating':'concentrating', 'pow- ers':'powers',
            'Un\u00ad Iimited':'Unlimited','aI/ of':'all of','WizardS/Sorcer\u00ad ers':'Wizards/Sorcerers',
            '+1 .':'+1.',
        }.items():after=after.replace(before,corrected)
        replace(rec['file'],rec['before'],after,rec['pdf_pages'],None,
                "Recovered continuous paragraph by reading left/right native PDF text blocks in column order, bounded by matching 50-character endpoints. Manually reviewed prose; numbers on PDF 41 and 318 visually verified, including the omitted +1 spell-strength and 20 P.P.E. per melee rules. Removed extraction-only word breaks and glyph errors.")
    save_repairs(ROOT/'reports/ocr-review/source-repairs-10.json')


if __name__=='__main__':main()
