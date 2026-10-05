"""Generate a per-book review summary without claiming full source certification."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/ocr-review'


def read(name):return json.loads((REPORT/name).read_text(encoding='utf8'))


NOTES={
    'Aliens Unlimited.md':'Recheck species equipment prose on PDF 111/113 and end indexes on 192–193; phrase flags may include independent-OCR mistakes.',
    'Heroes Unlimited - Powers Unlimited 1.md':'Additional manual proofreading needed, especially Abnormal Energy Sense/Adrenaline Surge (PDF 11–12) and Color Manipulation/Conduct Electricity (PDF 19–21). Short-word corruption can evade automatic flags.',
    'Heroes Unlimited - Powers Unlimited 2.md':'Two header-only tables are intentionally blank character-sheet fields, visually confirmed on PDF 97; review remaining tables for numerical fidelity.',
    'Heroes Unlimited - Powers Unlimited 3.md':'Random super-ability lists on PDF 108–111 need entry-by-entry checking. Source contains duplicate printed pages 86–87; garbled rotated duplicates removed.',
    'Heroes Unlimited - RPG - 2E.md':'Contents/quick-find tables and experience tables remain priorities. Remaining automatic table flags concern front-matter layout. Untouched numerical tables are not certified.',
    'Rifts - Merc Ops.md':'Quick-find table remains merged. Recheck contents, remaining equipment statblocks and experience data. Four missile charts have been rebuilt.',
    'Rifts - Mercenaries.md':'Independent OCR is unreliable on this faint scan. 150 low-correspondence pages are not 150 missing pages. Some duplicated weapon-proficiency lines and damaged story/stat prose remain; requires a stronger visual proofreading pass.',
    'Rifts - Ultimate Edition.md':'Contents/quick-find, experience tables (PDF 298) and skill-list numbers (305–306) require detailed checking. Attribute/speed and four missile charts rebuilt.',
    'Rifts - World Book 02 - Atlantis.md':'No low-correspondence page flags after comparison; this does not certify reading order, tables or untouched mechanics.',
    'Rifts - World Book 06 - South America 1.md':'Contents and experience tables (PDF 169) require checking; rebuilt Hak-Talon column continuation and corrected spaced Advisor Iridna label.',
    'Rifts - World Book 07 - Underseas.md':'Contents/quick-find and experience tables (PDF 213) require checking. Restored missing ship weapon/sensor sections on PDF 206.',
    'Rifts - World Book 09 - South America 2.md':'CONFIRMED SOURCE GAP: PDF 108 / printed 107 is 56.8% uniform gray, obscuring Destroyer ’Borg abilities. Readable omitted text restored; missing M.D.C./abilities 2–4 cannot be recovered from this copy. Experience table (PDF 192) and front matter also require checking.',
    'Rifts - World Book 21 - Splynn Dimensional Market.md':'Cronus description/statblock order and missing real name restored. Contents page remains a review priority; untouched statblocks not certified.',
}


def main():
    lexical={x['file']:x for x in read('corrections.json')}
    duplicates={x['file']:x['repairs'] for x in read('duplicate-repairs.json')['files']}
    patches=Counter()
    for path in REPORT.glob('source-repairs*.json'):
        for r in json.loads(path.read_text(encoding='utf8'))['repairs']:patches[r['file']]+=1
    percentile=Counter(x['file'] for x in read('percentile-order-repairs.json')['repairs'])
    audits={x['file']:x for x in read('audit.json')['files']}
    coverage={x['file']:x for x in read('source-coverage.json')['files']}
    sources={x['markdown']:x for x in read('pdf-inventory.json')}
    rows=[]
    for name in sorted(lexical):
        rows.append(dict(file=name,pdf_pages=sources[name]['pdf_pages'],lexical_changed_lines=len(lexical[name]['changes']),
            duplicate_lines_removed=duplicates[name],section_or_artifact_patches=patches[name],percentile_runs_reordered=percentile[name],
            remaining_text_flags=len(audits[name]['text_findings']),remaining_table_flags=len(audits[name]['table_findings']),
            low_correspondence_pages=[x['pdf_page'] for x in coverage[name]['pages'] if x['needs_completeness_review']],
            review_status='Further source proofreading required; not certified for rules ingestion',remaining_review=NOTES[name]))
    result=dict(status='corpus review and substantial correction pass complete; source certification incomplete',
        confirmed_source_gap=dict(file='Rifts - World Book 09 - South America 2.md',pdf_page=108,printed_page=107),files=rows)
    (REPORT/'review-summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    table=['| Book | PDF pages | Lexical lines | Duplicate lines | Section/artifact patches | Percentile runs |',
           '| --- | --- | --- | --- | --- | --- |']
    table += [f"| {r['file']} | {r['pdf_pages']} | {r['lexical_changed_lines']} | {r['duplicate_lines_removed']} | {r['section_or_artifact_patches']} | {r['percentile_runs_reordered']} |" for r in rows]
    notes='\n\n'.join('**'+r['file']+'** — '+r['remaining_review'] for r in rows)
    text='''# OCR corpus review — 2026-10-02

All 13 Markdown files in `sources-markdown` were screened for structure, OCR corruption, duplicated content, percentile ordering and source-page correspondence. Corrections were made in place. The matching supplied PDFs contain 2,503 pages and live in `C:\\Users\\jaken\\Git-Hub\\rpg-docling-pipeline\\data\\raw`.

This is a substantial correction pass, **not a certification that the corpus is complete or ready for accurate rules ingestion**. Known unresolved source/content issues are listed below. No absent rule was filled from memory or from another edition.

## Confirmed source damage

South America 2, PDF page 108 / printed page 107, has its lower half obscured by a gray block. A raster screen of all 193 pages flagged only this page; visual inspection confirmed the damage. The readable page text was also absent from the Markdown and has now been restored. The remaining Destroyer ’Borg M.D.C. description, abilities 2–4 and the beginning of a continuing paragraph require an intact source. A `SOURCE GAP` HTML comment marks the location in the book. The readable right-column continuation remains a fragment because its beginning is obscured.

**Hold that section from rules ingestion until an intact page is supplied.** Do not interpret the absent mechanics as zero, optional or nonexistent.

## Applied changes

The logs record 1,038 lexical changed lines, 437 duplicated-line removals, 174 section/artifact patches and 13 reordered percentile runs. These counts overlap and must not be added together as a count of independent mistakes. Every book received a filename-derived H1 and consistent UTF-8/LF line endings.

Major repairs include HU2/RUE attribute and speed charts; Merc Ops/RUE missile charts; HU2 size/height/weight charts; PU1/PU2 contents and quick-find lists; lost power headings and rules; column continuations; omitted ship weapon/sensor sections; Cronus’s description/statblock; and three corrupted South America 2 passages. Numerical edits use the supplied edition, with visual checking of the rebuilt rules charts. Some prose repairs use independently extracted native text or Windows OCR, as identified in their patch reasons. Batch 23 is editorial artifact cleanup, not a PDF transcription batch.

'''+ '\n'.join(table)+'''

## Remaining review by book

'''+notes+'''

## Interpretation of findings

`audit.json` contains current line/section locators for text, table and percentile candidates. These are heuristic findings. Valid dotted game abbreviations are excluded from letter-fragment detection. Blank character-sheet fields in PU2 were checked against the source and are intentional. Header-only contents tables, by contrast, can represent collapsed rows.

`source-coverage.json` compares unique five-word source phrases with the Markdown. A match can occur anywhere in the book. It does not verify numbers, column order, completeness, artwork or maps. Low correspondence can result from table layout or bad independent OCR; it is not proof that a page is missing. Mercenaries’ faint scan makes that metric especially unreliable. Zero flags does not mean zero errors. Short-word damage and plausible but incorrect numbers can evade these checks.

Image placeholders contain no image data. Maps, diagrams, illustrations and character-sheet layouts have not been made recoverable assets. Existing headings were generally preserved; a fully reconstructed semantic book hierarchy has not been asserted.

Printed inconsistencies were retained where verified: missile-chart `64.3 m`, `804 m` and mini-plasma `1.5 m`; RUE Electrokinesis `10 feet (0.3 m)`; PU1 Plasma’s divided-blast example; and the printed blank Size 20 Long cell. Speed fractions were represented as equivalent decimal MPH values. The initial lexical batch’s Physical Prowess abbreviation repair is an editorial consistency correction, not new game content.

## Verification and traceability

`verification.json` records successful exact reconstruction of all 13 original Markdown files from the logs, including their original line endings. All 13 supplied PDF SHA-256 hashes are unchanged. This establishes provenance and reversibility, not correctness of untouched text.

`structural-validation.json` records valid UTF-8, LF-only line endings, one H1 per book, consistent table column counts, paired fence counts, and no NUL or Unicode replacement characters. Syntactic validity does not establish numerical accuracy.

Applied logs: `corrections.json`, `duplicate-repairs.json`, `percentile-order-repairs.json`, `source-repairs.json`, `source-repairs-02.json` through `source-repairs-23.json`, and `newline-normalization.json`. Native/column/paragraph/duplicate candidate reports are historical proposals; they may refer to already corrected text and must not be applied blindly. `proposed-corrections.json` is the latest lexical dry run.

The exact transaction order is encoded in `scripts/verify_ocr_repairs.py`. Scripts for applied batches deliberately refuse to overwrite their logs. Do not rerun them against this corrected corpus. Read-only checks can be rerun with:

```powershell
python scripts/verify_ocr_repairs.py
python scripts/review_ocr.py
python scripts/audit_source_coverage.py
python scripts/summarize_ocr_review.py
```

Reports and source Markdown are currently excluded by the repository’s existing `.gitignore`. Changes remain local; no commit or publication was performed.
'''
    (REPORT/'README.md').write_text(text,encoding='utf8')
    print('Wrote per-book review-summary.json and README.md')


if __name__=='__main__':main()
