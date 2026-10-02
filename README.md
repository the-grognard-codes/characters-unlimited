# Characters Unlimited

An offline Windows character workshop for Rifts Ultimate Edition and Heroes Unlimited Second Edition. Work is being delivered in the approved slices; the current build supports the initial Rifts Human/Vagabond attribute path, identity, notes, and local saves. Class mechanics and the remaining catalogs are not yet implemented.

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

See [the specification](docs/character-creator-spec.md), [ticket plan](docs/character-creator-ticket-plan.md), and [design decisions](docs/design-interview.md). Book transcriptions and reference PDFs remain local inputs and are not committed with the application.

## Source inventory

The Book sources & coverage view searches provisional section candidates and displays source/PDF fingerprints. It never counts a heading as an implemented character option. Rebuild its metadata from completed pipeline outputs:

```powershell
python -m characters_unlimited.coverage <processed-markdown-directory> --pdf-directory <original-pdf-directory>
```

The inventory contains names and locations rather than the books' full text. A complete option audit must also inspect prose and tables and resolve duplicate headings, aliases, missing references, and uncertain passages before source coverage is closed.
