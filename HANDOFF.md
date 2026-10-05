# Characters Unlimited: handoff to the main Windows PC

Prepared 2026-10-05. This is a continuation checkpoint, not a completed-product report.

## Instructions for the receiving Codex

Read this document, inspect the destination checkout and restore the attached local checkpoint before implementing anything. The latest user instruction was: **stop when the next slice is complete**. That stopping point has been reached: natural psionics is merged, and hourly continuation is PAUSED. Moving the discussion does not itself authorize restarting implementation or scheduling. Present the restored checkpoint and wait for the user to resume. Once resumed, follow the existing plan and amended scope without repeating the design interview.

Earlier the user explicitly authorized working branches, implementation, self-review, testing, scoped staging/commits, PR creation and reviewed merges after required tests pass. The paused state takes precedence over that ongoing authorization until resumed. Do not recreate an hourly automation on this machine unless the user asks to resume unattended continuation. The old machine's schedule must remain paused to avoid simultaneous writers.

## Exact checkpoint

- Repository: https://github.com/the-grognard-codes/characters-unlimited
- Original checkout: `C:\Users\jaken\Git-Hub\characters-unlimited`; the destination may use another path. Resolve all repository-relative references below against that destination.
- Current branch: `main`.
- Latest merge: `8a30948f3b807b7656ca7c6c07b3b77a82e40461`.
- Completed slice:22I2, source-backed Rifts natural psionics; parent22I is now complete.
- PR112: https://github.com/the-grognard-codes/characters-unlimited/pull/112
- Tested PR head: `a5b9255a8dbc0f35e15058c2c00315b9d35ac662`.
- Both review axes approved. Both exact-head Windows runs passed474 tests, with one frozen-only skip exercised in a separate successful packaged-executable test:
  - https://github.com/the-grognard-codes/characters-unlimited/actions/runs/37354701718
  - https://github.com/the-grognard-codes/characters-unlimited/actions/runs/37354708432
- Temporary preview servers and browser tab were closed. No outstanding PR validation remains for this slice.
- Paused automation on the old machine: `complete-character-creator-modified-plan`, thread `01a0fdce-60ec-7a43-8e74-a4f7fd9af219`.

The delivered slice adds56 ordinary Rifts psionic powers through reusable, declarative ability/path contracts: potential, category/count guidance, retained ISP and level gains, psychic saving targets, exact portable state, searchable source references and editable PDF output. Source-review corrections are included. Class/RCC psychic entitlements and other game families are not certified by this ordinary natural path.

## Restore the local checkpoint

GitHub contains the implementation and pre-merge validation document. Four subsequent completion/status receipts are uncommitted on the old PC. `checkpoint.patch` preserves exactly those tracked changes:

- `.scratch/character-creator/issues/22i-common-ability-paths.md`
- `.scratch/character-creator/issues/22i2-rifts-natural-psionics.md`
- `docs/evidence/22i2-natural-psionics-validation.md`
- `docs/implementation-progress.md`

The newly prepared, untracked next ticket is supplied separately under `checkpoint/.scratch/character-creator/issues/05d1-rifts-rogue-skill-catalog.md`. It has not been implemented.

For a fresh checkout at the merge above, inspect first, then restore:

```powershell
git status --short
git rev-parse HEAD
git apply --check 'C:\path\to\handoff\checkpoint.patch'
git apply 'C:\path\to\handoff\checkpoint.patch'
Copy-Item -LiteralPath 'C:\path\to\handoff\checkpoint\.scratch\character-creator\issues\05d1-rifts-rogue-skill-catalog.md' -Destination '.scratch\character-creator\issues\05d1-rifts-rogue-skill-catalog.md'
```

Do not overwrite an existing destination ticket or apply the patch twice. If the destination has advanced, reconcile these completion receipts instead of resetting the checkout. Keep them for the next authorized scoped commit; do not publish a new PR merely to resume a conversation.

`old-pc-working-tree.txt` inventories additional local files. Untracked source-processing scripts and personal character-generation scripts belong to other work and must not be deleted, staged wholesale or reverted. They are **not included** in this small checkpoint bundle; copy them separately if their owner needs them on the main PC. Temporary browser data, source-page renders and proposal/PR-body files are not required to continue the build.

## Start with the existing artifacts

These are the authorities; do not regenerate their contents from this handoff:

1. `docs/player-focused-scope.md`: user-approved amendment overrides conflicting detail in older documents.
2. `docs/character-creator-ticket-plan.md`: original plan and final retrospective baseline.
3. `docs/character-creator-spec.md` and `docs/design-interview.md`: accepted requirements and decisions.
4. `docs/implementation-progress.md` plus `.scratch/character-creator/issues/`: actual checkpoints and ticket dependencies.
5. `docs/agents/issue-tracker.md`: local tracker and completion rules.
6. `docs/class-import-framework-review.md`, `docs/owned-class-profile-contract.md`, `docs/racial-creation-contract.md`, `docs/ability-path-contract.md` and `docs/common-ability-selection-contract.md`: existing reusable seams and their remaining limits.
7. `docs/evidence/22i2-natural-psionics-validation.md`: latest proof; sibling builder PNG, editable PDF and rendered continuation are tracked in Git.
8. `characters_unlimited/packs/accepted.json`: immutable accepted archives and active versions.

At full completion use the repository retro skill, compare functional requirements, visual/media delivery and user intent against the original plan and amended scope, and present the Markdown retrospective. **That final retrospective is not due yet.**

## Scope reminders and next work

Games are Rifts Ultimate Edition and Heroes Unlimited2E, separated in the UI and catalogs. Palladium Fantasy is deferred. Every applicable supplied class/race/RCC remains required. Honor-system eligibility/count guidance needs no override marker.

Prioritize prescribed attribute generation/house rules, actual acquired skill percentages with applicable bonuses, skill entitlements, shared ability choices, categorized equipment, saved identity revisions, exact saves and editable PDFs. Use data declarations rather than handlers for individual classes or races. Conditional power/combat/activity effects may be concise descriptions. Do not spend additional slices on exhaustive kicks, swim speeds, fatigue/activity simulation or encounter mechanics. General insanity is excluded except option-specific Crazy/permanent injuries. HU Mega Heroes, bases and super-vehicle design are excluded. **Robot and bionic construction remain required.** Resolve ordinary ambiguities autonomously; do not restart the old stream of minor rules questions.

Prepared next slice on explicit resume:05D1, shared Rifts Rogue skill catalog, planned branch `codex/rifts-rogue-skill-catalog`. The exact17 named skills and acceptance are in the attached ticket. It targets normal percentages, applicable attribute/synergy bonuses, prerequisites and Vagabond/City Rat entitlements using existing contracts. No optional activity simulation. Verify actual tracker state before starting in case another machine has advanced.

The larger build remains incomplete: broader class/race/RCC and supporting-skill coverage, magic, Heroes category/power families, nonhuman traits and saved-identity backtracking, robot/bionic construction, general maintainer conversion/activation reporting and final release acceptance. Inventory ownership is not mechanical completion; synthetic fixtures are not source certification. See existing tickets rather than interpreting this as an exhaustive backlog replacement.

## Workspace and source access

Codex needs read/write access to the destination creator checkout and its Git metadata for the authorized branch/commit workflow, temporary artifact directories, local character-test data and preview-server execution. Follow the destination's actual sandbox/approval rules. On the old host escalated execution was sometimes necessary because of account-lock/sandbox behavior; that is an environmental fact, not permission to bypass destination controls.

The following are ignored by Git and a clone will not restore them:

- `sources-markdown/`: the13 supplied converted books. Copy the current local mirror or provision the completed pipeline Markdown.
- `sources-pdf/`: any local original-book mirror.
- `character-sheets/*.pdf`: user-supplied visual examples. Tracked runtime templates already support current tests, but reference originals are still useful for visual acceptance.
- Local data/output folders, environments and build artifacts.

Independent source-processing workspace on the old PC: `C:\Users\jaken\Git-Hub\rpg-docling-pipeline`.
Completed Markdown is under `data\processed`; original PDFs are under `data\raw`. The scanned Rifts source used for this slice is `data\raw\Rifts - Ultimate Edition.pdf`. Provision read access to those source folders on the main PC, preferably preserve that relative layout or explicitly record the new paths. Creator work should not modify pipeline output or unrelated processing scripts. Use completed Markdown plus original PDF verification when OCR damage matters; do not wait for all conversions unnecessarily. Required source facts must be reviewed before accepting definitions.

If player saves need transferring, use portable JSON exports/backups from `%LOCALAPPDATA%\CharactersUnlimited` or the actual configured data directory. Installing/cloning the app does not transfer these saves. Browser-test data in this handoff's inventory is disposable development evidence, not the player's library.

GitHub access: authenticate Git for repository read/write and `gh` for PR creation, CI/log/artifact inspection and authorized merges. Actions must be able to run the existing Windows workflow. Use `gh auth status` and `git remote -v`; never put tokens or credentials in the handoff, repository, PR body or logs. No credentials are included here. Network access to GitHub and the Python package index is needed for development/build setup; players run offline afterward.

## Toolchain on the main Windows PC

Required development tools:

- Windows with PowerShell; PowerShell7 matches CI, and the build script also supports Windows PowerShell Desktop.
- Git and GitHub CLI (`gh`).
- Python3.14 to match Windows CI (project metadata permits3.11+, but validate release behavior with3.14).
- Node.js22 for syntax-checking the browser scripts; no npm application build is required.
- Python dependencies exactly as pinned in `requirements-dev.txt`; use that file rather than duplicating/updating package versions.
- Packaging dependencies pinned in `requirements-build.txt`; `scripts/build-windows.ps1` creates its own `.packaging-venv` and uses `CharactersUnlimited.spec`.

Create fresh environments on the main PC; do not copy `.venv` or `.packaging-venv` from the old computer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m mypy --check-untyped-defs characters_unlimited tests
.\.venv\Scripts\python.exe -m unittest tests.test_natural_psionics -v
```

The previous mypy result covered162 source files. Use `--check-untyped-defs`, not an invented strict configuration. Choose focused affected selectors first; avoid identical full reruns after passing checks without new changes or unresolved concerns.

Required integration/merge gates are in `.github/workflows/check.yml`: typing, full unit regression, compileall, all browser JavaScript syntax, Windows build, separate frozen executable test and package artifact. Wait for passing **exact PR-head** Windows regression and frozen checks before each merge; finish outstanding PR validation before overlapping product changes. Both push/PR runs were checked for the latest merge.

Local package validation:

```powershell
.\scripts\build-windows.ps1 -Python '.\.venv\Scripts\python.exe'
$env:CHARACTERS_UNLIMITED_EXE = (Resolve-Path 'dist\CharactersUnlimited\CharactersUnlimited.exe').Path
.\.venv\Scripts\python.exe -m unittest tests.test_packaged_app -v
```

For browser checks, run the local server in an isolated data directory:

```powershell
.\.venv\Scripts\python.exe -m characters_unlimited.server --data-dir '.scratch\browser-validation-data' --port 8817 --no-browser
```

Use `--port 8817` with a space if the CLI does not accept the compact spelling. Close only servers/tabs created for the check, and preserve user libraries.

Visual/PDF tools: provision Poppler (`pdftoppm`) for rendering original scans and exported sheets. Read the PDF skill before visual PDF work; runtime PDFs use pypdf/reportlab from the pinned dependencies. The old host used a Codex-bundled Poppler runtime discovered through workspace-dependency tooling; that absolute cached path is machine-specific and should not be copied into code. An equivalent trusted installation is sufficient. Source PDF scans may have no extractable text; inspect rendered pages where needed.

Browser interaction: enable the available Codex computer-use/unified-computer-use plugin and its supported CUA browser tools for actual UI proof. Follow its skill and browser docs; do not replace UI verification with private-state probes. The app can otherwise be launched manually in an ordinary browser, but record any automation limitation honestly. No cloud product service, database server, Docling runtime or Java/Flutter/Android toolchain is required for this character-creator project. The independent ingestion project has its own dependencies.

## Suggested skills

Load these through the destination's skill mechanism, reading the actual files and adapting old machine paths:

- `code-review`: `.agents/skills/code-review/SKILL.md`; two independent Standards/Spec review axes. This skill explicitly authorizes its parallel review agents. Otherwise respect the current delegation policy and personal routing instructions.
- `pr`: `.agents/skills/pr/SKILL.md`; required concise PR-body template.
- `codebase-design`: `.agents/skills/codebase-design/SKILL.md` for meaningful interface work, not routine edits.
- `pdf:pdf`: installed PDF skill for rendered/editable-PDF validation; discover its local path.
- `computer-use:computer-use`: installed computer-use skill for actual browser interaction; discover its local path.
- `retro`: `.agents/skills/retro/SKILL.md`, only when all required acceptance is actually complete.
- `handoff`: `.agents/skills/handoff/SKILL.md` for future discussion transfers.
- `openai-docs`: for Codex scheduling/tool setup questions if needed; not generic product implementation.

Repository skills are tracked. Also load the receiving machine's user instructions and any repository/nested AGENTS files. Personal routing on the old PC was `C:\Users\jaken\.codex\SUBAGENT_ROUTING.md`; it is outside this repository. If equivalent personal guidance is desired, transfer it separately rather than assuming Git restored it.

## Known operational details

Always stage scoped files, never `git add .` against this checkout's unrelated source changes. Prefer a new `codex/` working branch after the next explicit resume. Do not return to the completed `codex/common-ability-paths` or `codex/rifts-natural-psionics` branches.

The old chat reached the app's100-artifact attachment limit: attaching PR112 returned `thread attachment identity count exceeds100`. The PR itself is merged and its URL is above. A new chat may attach artifacts normally; do not remove unrelated attachments to make room.

On completion report what is implemented, what passed and material remaining scope. Do not claim full-corpus completion, invent a final retro, or resume the paused schedule merely because this handoff was read.
