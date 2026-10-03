# Characters Unlimited

An offline Windows character workshop for Rifts Ultimate Edition and Heroes Unlimited Second Edition. Work is being delivered in the approved slices; the current build supports the initial Rifts Human/Vagabond attribute path, identity, notes, and local saves. Reviewed domestic, Communications, Science, Technical and several required Vagabond skills are available, with representative level-one hand-to-hand and weapon proficiency explanations. Remaining class mechanics, equipment and the other catalogs are still pending.

## Development

Python 3.11 or newer:

```powershell
python -m characters_unlimited.server
```

The browser opens a loopback-only local service. Characters autosave to `%LOCALAPPDATA%\CharactersUnlimited\characters.sqlite3`, independently of the installation folder. To use a disposable development location:

```powershell
python -m characters_unlimited.server --data-dir ./local-data
```

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\scripts\check.ps1
```

The check script fails immediately on type-check, test, or syntax errors. Individual checks:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q characters_unlimited tests
node --check characters_unlimited/web/app.js
```

The final Windows package will bundle its runtime; requiring Python is a development-only limitation of the first slice.

## Portable saves and backups

Use **Duplicate** for an independent character copy. **Export portable save** downloads a JSON bundle containing the character and its exact supported rule definitions; **Import portable save** creates a new character and retains existing saves. Current imports support the Rifts Human/Vagabond level-one path and accepted core/domestic pack versions. Altered definitions, inconsistent dice or values, and unsupported versions are rejected. PDF imports are not supported.

**Back up all characters** writes a consistent SQLite snapshot to the `backups` folder beside the live database and displays its full path. To restore a backup, close the application, preserve the current database separately, and copy the chosen snapshot to `characters.sqlite3` in the data directory. Portable saves move individual characters; database backups retain the whole library.

See [the specification](docs/character-creator-spec.md), [ticket plan](docs/character-creator-ticket-plan.md), and [design decisions](docs/design-interview.md). Book transcriptions and reference PDFs remain local inputs and are not committed with the application.

**Review rule updates** shows the domestic skill version, before/after percentages and combat values, selection counts, sources, and remaining gaps. Existing characters keep their saved versions until **Apply reviewed update** is selected. Applying creates a before-update database backup and displays its path; use the restoration procedure above if needed. New characters use version 1.7.0, including reviewed I.Q. bonuses, required language/pilot/repair choices, 57 selectable skill definitions and representative combat training. Choices autosave; missing, duplicate, or excess language choices remain visible. New characters also use primary 1.1.0, recording Vagabond M.A./P.S./P.E. bonuses separately from racial dice. Rerolls keep the original class contribution; fixed edits replace the final total and additive edits apply after the contributions. Existing primary pins remain unchanged; upgrades that introduce random class rolls are pending. Other attribute effects, remaining skill categories and broader rule upgrades are still pending.

## Source inventory

The Book sources & coverage view searches provisional section candidates and displays source/PDF fingerprints. It never counts a heading as an implemented character option. Rebuild its metadata from completed pipeline outputs:

```powershell
python -m characters_unlimited.coverage <processed-markdown-directory> --pdf-directory <original-pdf-directory>
```

The inventory contains names and locations rather than the books' full text. A complete option audit must also inspect prose and tables and resolve duplicate headings, aliases, missing references, and uncertain passages before source coverage is closed.

The coverage view also searches confirmed canonical option identities and their aliases. Identity confirmation is separate from mechanical review and automation. Current records cover 67 core identities across the games, including O.C.C.s, hatchlings, categories, optional modifiers and named Hardware/training/robot paths; remaining options and content-ticket assignments are tracked as open findings. See [the canonical audit contract](docs/canonical-option-audit.md).

## Editable Rifts sheets

**Export editable PDF** shows unfinished parts before downloading an editable copy of the supplied Rifts sheet. Supported identity, attributes, skills, combat and notes are projected; missing equipment, resources and other rules remain blank. Long notes and skill checks receive matching continuation pages. PDF edits stay in the exported file; PDF import remains outside scope. Full game-specific projection and Heroes Unlimited sheets remain pending.

PDFs embed the bundled, licensed Droid Sans Fallback font for Unicode editing. Initial exports display characters outside its coverage as `[U+code]` while preserving their original editable value.
