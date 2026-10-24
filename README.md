# Characters Unlimited

An offline Windows character workshop for Rifts Ultimate Edition and Heroes Unlimited Second Edition. The implemented Rifts paths include Human classes and Civilized (independent or Coalition) and Wild Psi-Stalkers, with source-backed choices, resources, combat, advancement, local saves, portable files and editable sheets. City Rat remains partial. Broader races, magic, construction, Heroes coverage and final release acceptance remain incomplete; consult [implementation progress](docs/implementation-progress.md) and its evidence receipts for exact supported scope.

Reviewed Rifts equipment includes class starting packages, weapons, armor, ammunition and ordinary possessions within a bounded catalog. Use Equipment to record credits, purchase quantities, equip possessions, move them between carried and stored locations, edit shot counts and exchange compatible clips. Starting grants retain their original dice and receipts. Negative budgets and exceptions remain visible. Equipped attacks explain W.P. and weapon bonuses; armor capacities and possessions appear in editable PDF exports. See the [equipment contract](docs/equipment-contract.md).

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

Use **Duplicate** for an independent character copy. **Export portable save** downloads a JSON bundle containing the character and its exact supported rule definitions; **Import portable save** creates a new character and retains existing saves. Supported paths retain their exact accepted versions and recorded dice through transfer and reopening. Altered definitions, inconsistent dice or values, and unsupported versions are rejected. PDF imports are not supported.

**Back up all characters** writes a consistent SQLite snapshot to the `backups` folder beside the live database and displays its full path. To restore a backup, close the application, preserve the current database separately, and copy the chosen snapshot to `characters.sqlite3` in the data directory. Portable saves move individual characters; database backups retain the whole library.

See [the specification](docs/character-creator-spec.md), [ticket plan](docs/character-creator-ticket-plan.md), and [design decisions](docs/design-interview.md). Book transcriptions and reference PDFs remain local inputs and are not committed with the application.

**Review rule updates** previews source-backed changes before applying them. Existing characters keep exact saved versions; applying a supported update creates a before-update backup. New characters use the active versions in [accepted.json](characters_unlimited/packs/accepted.json). Attributes, acquired Physical bonuses, generated resources and permanent saving-bonus dice retain separate source receipts. Removing and reselecting training reuses recorded dice and learning levels. Changes that reinterpret acquired permanent dice or generated resources require a separate migration and are rejected by ordinary correction previews. Missing, duplicate or excess choices remain visible.

## Source inventory

The Book sources & coverage view searches provisional section candidates and displays source/PDF fingerprints. It never counts a heading as an implemented character option. Rebuild its metadata from completed pipeline outputs:

```powershell
python -m characters_unlimited.coverage <processed-markdown-directory> --pdf-directory <original-pdf-directory> --verified-gaps characters_unlimited/data/verified-source-gaps.json
```

The inventory contains names and locations rather than the books' full text. Independently inspected PDF gaps are stored in `characters_unlimited/data/verified-source-gaps.json` and reconciled into the active view and CLI rescans using `--verified-gaps`. Custom scans can omit that option. Changed Markdown/PDF hashes require renewed evidence; the rebuild fails rather than carrying a stale gap forward. Use the full supplied source set when rebuilding the bundled inventory. A complete option audit must also inspect prose and tables and resolve duplicate headings, aliases, missing references, and uncertain passages before source coverage is closed.

The coverage view also searches confirmed canonical option identities and their aliases. Identity confirmation is separate from mechanical review and automation. The partial catalog includes O.C.C.s, hatchlings, categories, optional modifiers and named Hardware/training/robot paths; South America 1/Underseas, Atlantis/Splynn and Mercenary/South America 2 creation paths; Powers Unlimited supplement identities; and Aliens Unlimited racial groups, named generation paths and monster source identities. All 718 currently audited identities have bounded owning content tickets in `characters_unlimited/data/content-tickets.json`; the view shows their titles without claiming implementation. Remaining options, source gaps, supporting rules and complete dependencies stay open. See [the canonical audit contract](docs/canonical-option-audit.md) for the current count and scope.

## Editable Rifts sheets

**Export editable PDF** shows unfinished parts before downloading an editable copy of the supplied Rifts sheet. Supported identity, attributes, skills, combat and notes are projected; generated starting HP/S.D.C. are included; missing equipment and other rules remain blank. Long notes and skill checks receive matching continuation pages. PDF edits stay in the exported file; PDF import remains outside scope. Full game-specific projection and Heroes Unlimited sheets remain pending.

PDFs embed the bundled, licensed Droid Sans Fallback font for Unicode editing. Initial exports display characters outside its coverage as `[U+code]` while preserving their original editable value.

## Early Windows package

Run `scripts/build-windows.ps1` on Windows to build `dist/CharactersUnlimited/CharactersUnlimited.exe`. Unzip or copy the entire folder, then double-click the executable; the desktop controller opens the workshop and stops the local application. Player PCs need no Python or Node installation. This package covers the current implemented path; full content and release acceptance remain pending. See [package instructions](docs/windows-package.md).

Heroes Unlimited Revised Second Edition now has a basic Human-origin Mutant creation path: initial attributes with its repeated-six exceptional method and normal mortal ceilings, house rules, notes, manual values, local saves and portable export/import. Players can roll or choose all twelve education-table outcomes, retain their history and inspect program/Secondary allowances with exact education rule pins. Business, Medical Assistant, Computer and Communications have implemented grants and skill calculations; remaining programs, powers, combat, equipment, advancement and the editable Heroes sheet remain unfinished. The builder shows those gaps. Rifts choices and calculations stay separate.

Heroes Unlimited supports Business, Medical Assistant, Computer and Communications program choices with education/I.Q. skill percentages, universal Pilot Automobile and Basic Mathematics, and exact-version portable saves. Program rules 1.1.0 correct High School eligibility: retained Business choices receive no scholastic bonus and show an eligibility warning. **Review rule updates** previews the correction for earlier pins; **Keep current rules** cancels, and **Apply reviewed update** creates a backup before changing the program version. Education and other pins stay unchanged. Program rules 1.2.0 add Medical Assistant through the same explicit update workflow. Program rules 1.3.0 add categorized Secondary choices for supported skills, remaining education allowances and I.Q.-only percentages. Older pins gain them through explicit review/apply. Program rules 1.4.0 add Computer grants, the explicit Computer Repair/Radio alternative, distinct remaining-choice counts and labeled procedure/context checks. Program rules 1.5.0 add Communications, all nine category alternatives, Cryptography's short-study context and the once-only Optic Systems bonus to T.V./Video. Duplicate fixed-grant choice credit remains pending interpretation. Program rules 1.6.0 add First Aid and Holistic Medicine with visible one/two-selection Secondary costs. Other programs, the remaining Secondary catalog and native-language arithmetic remain pending; source notes are in `docs/evidence/06b-source-locators.md` and `docs/evidence/06c-source-locators.md`.

The reviewed Human Vagabond path can explicitly generate starting credits and Black Market saleable goods once. Each uses its separate 2D6 × 100 source roll. Credits add to the current balance; goods stay recorded as goods value. Original dice survive later purchases and balance edits. Older equipment pins require a reviewed rule update. Standard starting gear is still being implemented.

The fixed Vagabond personal-gear list can be added once without changing credits. The original grant receipt stays separate from editable possessions, including removed gear. Generic items retain unspecified prices and weights; carried weight is labeled incomplete when needed. Current personal gear fills the editable Rifts Equipment rows. Armor, gun, spare clip, knife and transport starting choices are the next equipment slice.
