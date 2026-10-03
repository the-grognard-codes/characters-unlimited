# Corrected-source provenance validation

The active inventory was captured from the source-review workstream's local `sources-markdown` copies. Originals remain in `C:/Users/jaken/Git-Hub/rpg-docling-pipeline/data/raw`. The initial processed inventory is preserved byte-for-byte at `characters_unlimited/data/source-snapshots/initial-inventory.json`.

Compared snapshots: all 13 book identities and 13 original PDF SHA-256 hashes are unchanged; all 13 Markdown hashes changed. The active scan contains 7,065 provisional heading candidates, zero reviewed books, zero fully automated options, and one explicit source gap. Corrected text changes candidate identities even when headings/line positions are unchanged. This is provenance evidence, not certification of rules accuracy.

South America 2's containing candidate is “Destroyer 'Borg Abilities and Bonuses,” lines 5435–5448; its gap marker at line 5439 identifies PDF 108 / printed 107. The entire option remains held for an intact source, not merely the containing candidate. The scanner recognizes explicit markers; it cannot discover unmarked damage or certify completeness.

Focused coverage checks verify multiline markers and changed-content identity. All 25 workflow checks, mypy, Python compilation, and JavaScript syntax validation pass. Embedded-browser and Windows Edge checks show the summary, book-level gap description, and searched candidate's expanded `source-gap` details. The narrow browser screenshot is retained in `02a2-source-gap.jpg`; Edge's full-page screenshot timed out, while its accessibility state confirmed the same content. No browser permissions were changed.
