# Characters Unlimited: unattended implementation handoff

Updated 2026-10-24. Repository: `C:\Users\jaken\Git-Hub\characters-unlimited`; remote: <https://github.com/the-grognard-codes/characters-unlimited>. This is the current continuation entry point. Recheck live state at startup; the facts below are a verified checkpoint.

## Execution scope and startup

Current continuation checkpoint2026-10-24: the user explicitly resumed unattended implementation and authorized the normal publication process. PR137 has now merged at2026-10-24T15:11:02Z as `c95d03d17f8acea7d7e4fd26c14f274836ac2431`, after fresh exact-head/job-step success readbacks. Local main fast-forwarded to that SHA and `git status --porcelain` was empty before creating `codex/rifts-psi-stalker-paths`. All preserved local documents and the historical folder were then restored onto the new branch.05D25 is done.05D26 is in progress: neutral retained numeric contributions and public workflow tests exist; source candidates are inactive, with no Psi-Stalker mechanical acceptance or activation claimed. See `.scratch/character-creator/issues/05d26-psi-stalker-paths.md`. The earlier documentation-refresh scope and open-PR checkpoint below are historical; this paragraph supersedes them.

The current request updates documentation for a future queued run. It does not itself start implementation, merge PR137, commit these documents, or configure an automation. When the user queues a task explicitly requesting continuation, follow that task's budget/stop conditions and the previously authorized implementation, scoped commit, PR and reviewed-merge process. The October13 two-hour stop ended that run; it is historical, not a reason to refuse a new explicit continuation request. Reading this file alone does not create a recurring schedule.

Queue against this existing local checkout to include the updated handoff, untracked detailed guide and local receipts. A fresh worktree, cloud checkout or clone will not inherit these uncommitted files or ignored source/proof assets. Before running elsewhere, arrange their authorized publication or explicit transfer and verify the destination has the current handoff; the October5 zip is not a substitute.

The root handoff previously described an October5 transfer at PR112. PRs113–136 and the reviewed pilot work in PR137 supersede that checkpoint. Preserve `characters-unlimited-handoff-20261005-143727/` and its zip as historical/user material. Continue from the actual checkout. Applying its old `checkpoint.patch` or restoring its old source ticket would regress completed work.

Start in this order:

1. **Inspect ownership.** Read current personal/repository instructions and `C:\Users\jaken\.codex\SUBAGENT_ROUTING.md`. Inspect `git status --short`, branch, HEAD and remote state. Account for each existing local change before editing. Completion: distinguish published implementation, local receipts, this handoff and unrelated files.
2. **Close PR137's acceptance gate.** Recheck its head, reviews, both run results and any newer required checks. If the reviewed head is unchanged and all gates still pass, complete the already authorized normal merge in the resumed implementation task. If already merged, record the actual merge rather than trying again. If state changed, inspect the delta/failure first. Completion: actual merged SHA/time and successful committed-head validation are recorded, or a specific new blocker is documented.
3. **Reconcile receipts safely.** Mark05D25 done only after that merge; update evidence and progress. Preserve local documents when synchronizing main. Inspect branch relationships and synchronize without resetting/cleaning or overwriting existing changes. Include owned receipt/handoff updates in a later authorized scoped commit. Receipt edits alone do not require repeating unchanged pilot validation.
4. **Implement the next bounded batch.** Use the Psi-Stalker plan below and [detailed source preparation](docs/next-implementation-steps.md). Resolve the remaining source decisions and shared contract gap before activating content. Completion: both Civilized and Wild paths satisfy the complete slice acceptance, including their applicable equipment variants, rather than merely appearing in a catalog.
5. **Continue the amended project.** After a reviewed passing merge, choose the next coherent capability/content batch from existing tickets and actual dependencies. Continue within the queued task's authorization/budget. Finishing one small slice or reaching the end of this document does not complete the product. At a requested deadline or actual blocker, leave a precise checkpoint and stop.

No implementation or merge was performed during this handoff refresh. Historical chronological evidence may still say “pending”; the latest verified receipt takes precedence.

## Verified repository and PR checkpoint

| Item | State verified2026-10-24 |
| --- | --- |
| Checkout branch | `codex/rifts-robot-pilot-paths` |
| Local/published reviewed HEAD | `904e98bbf44ba0f6388b6990bd09130385399019` |
| GitHub main | `f5f40285c59bda93fdc8b70397e2280640282972` |
| Last merged slice |05D24 Human Cyber-Knight paths, PR136 |
| Current slice |05D25 Human Power Armor Pilot and Robot Pilot |
| [PR137](https://github.com/the-grognard-codes/characters-unlimited/pull/137) | Open, non-draft, mergeable/clean; not merged |
| [Push38351032330](https://github.com/the-grognard-codes/characters-unlimited/actions/runs/38351032330) | Success, attempt1, reviewed head; updated2026-10-13T07:23:04Z |
| [PR38351050663](https://github.com/the-grognard-codes/characters-unlimited/actions/runs/38351050663) | Success, attempt1, reviewed head; updated2026-10-13T06:45:23Z |

Both run job-step readbacks confirm typing, full unittest regression, Python compilation, all browser-script syntax checks, Windows packaging, separate frozen executable validation and artifact upload succeeded. Refresh actual status/head and newer requirements before merging. The old runs do not need more waiting or repetition merely because an agent takes over. October13's “CI pending” stop receipts are historical.

At the start of this refresh, tracked local changes were status receipts in:

- `.scratch/character-creator/issues/05d25-robot-pilot-human-paths.md`
- `docs/evidence/05d25-robot-pilot-validation.md`
- `docs/implementation-progress.md`

`docs/next-implementation-steps.md` was untracked, as was the preserved October5 handoff directory. This refresh updates the root handoff, detailed guide and those three owned receipts. Preserve them. Stage explicit owned paths; broad staging would capture historical/unrelated files. No new commit is created for this documentation request.

### Accepted definitions and implementation

The pilot branch uses core1.16.0, skills2.37.0 (215 skill identities), equipment1.24.0. Merged main uses core1.15.0, skills2.36.0 and equipment1.23.0. [accepted.json](characters_unlimited/packs/accepted.json) owns active versions and immutable hashes; inspect it rather than guessing a future version.

PR137 adds `robot-pilot-power-armor` and `robot-pilot-robot`, specialty-qualified Elite combat training and shared source-bound `level_awards` for named pools. It preserves first-learning levels, initial/later entitlements, explicit early choices, inactive preflight, undo and portable replay. It adds no class-name runtime dispatch or new persisted schedule field. Historical archives/pins remain unchanged. Vehicles and typical implants are source-described possessions, separate from Human personal armor/attributes; pilot creation does not complete robot/bionic construction.

Implementation entry points are `skill_pool_learning.py`, `application.py`, `skills.py`, `profile_preflight.py`, `nonpercentile_skills.py` and browser `web/app.js`, all under `characters_unlimited/`. Read the [award contract](docs/skill-pool-awards-contract.md), [pilot ticket](.scratch/character-creator/issues/05d25-robot-pilot-human-paths.md) and [pilot evidence](docs/evidence/05d25-robot-pilot-validation.md) for exact behavior/source interpretations.

## Acceptance completed for05D25

- Final local regression:726 tests in5063.783 seconds; one packaged-only skip covered separately.
- Focused integration:42 tests in526.223 seconds, plus conventional-sidearm validation in2.073 seconds.
- Typing214 files, Python compilation, all browser scripts under Node22 and whitespace checks pass.
- Final Windows build and rebuilt frozen executable pass; frozen workflow162.190 seconds.
- Actual packaged GUI creation covers both pilots; Robot Pilot advancement reaches level6 and dates named models1/1/3/6. Other fixture completion used disclosed loopback helpers, not claimed browser clicks.
- Exact no-dice portable import/export and reopen agree with public projections; all selection pools can be completed.
- PDFs: Power Armor Pilot9 pages, Robot Pilot11 pages. Canonical fields/widgets/appearances agree; root and independent reviewers inspected all20 pages.
- Independent Standards and Spec reviews approve. Standards retained one nonblocking P3 combat-catalog duplication observation. It is not a reason to change the accepted head before merge.
- Both hosted Windows runs now pass every required step.

Tracked proof artifacts are the two PDFs and three browser PNGs beside [the validation receipt](docs/evidence/05d25-robot-pilot-validation.md). Existing ignored receipts include `tmp/05d25-full-final.log`, `tmp/05d25-focused.log`, `tmp/05d25-build-final.log`, `tmp/05d25-frozen-final.log`, `tmp/05d25-20261012-public-proof.json` and `tmp/05d25-20261012-export-proof-v2.log`. Original/whole-sheet renders are under `tmp/pdfs/05d25/`. These exist on this checkout but a clone does not restore them. Use tracked evidence if scratch files are unavailable; re-render only what is needed.

## Product support and remaining gaps

The product has usable, validated Human Rifts workflows within reviewed skill/equipment catalogs: creation, meaningful choices, applicable percentages/resources, advancement, exact saves/portable transfer and editable sheets. Every legal source-book alternative is not yet available.

Merged main has38 selectable Human profiles:37 usable bounded profiles plus the partial City Rat foundation. Usable families are Vagabond, Wilderness Scout, Rogue Scholar, Rogue Scientist, wandering/city Body Fixer and Cyber-Doc, wandering/city Operator and Psi-Operator, Burster, Mind Melter, Coalition Grunt, Coalition SAMAS/Elite RPA Pilot, seven Technical Officer MOS paths, two Glitter Boy paths, eight Merc Soldier paths and four Cyber-Knight psychic variants. PR137 adds two locally/hosted-validated pilot profiles; these are not yet in main. The newest local executable includes them.

Material limitations:

- Human is the only active Rifts race. No nonhuman/R.C.C. path is certified end to end; Psi-Stalker preparation is not activation.
- City Rat has real PPE/age-reduction, starting implant and selection-rule gaps. Selectability and a passing foundation slice do not certify the whole O.C.C.
- Weapon/equipment/proficiency catalogs remain bounded. Broader racial pairings and supporting families remain open. Some embedded `automation_gaps` prose is historical: inspect current owned declarations/tests before treating it as current truth. Conversely, preserve real missing choices as gaps rather than relabeling them descriptive.
- Heroes Unlimited has existing shared/category/power work; this Rifts checkpoint does not certify every HU family. Consult its actual tickets/evidence.
- Saved-character race/class revision, broader magic/psionic/class/RCC/corpus coverage, robot/bionic construction, maintainer/import certification and final release acceptance remain required.

Advertise bounded supported paths, not unqualified full-book/all-race coverage. Honor-system manual entries preserve player freedom; they do not silently close missing implementation/source dependencies.

## Next batch: Civilized and Wild Psi-Stalker

After PR137 closes, use [ticket12](.scratch/character-creator/issues/12-create-a-nonhuman-or-racial-class-character.md) and canonical [Psi-Stalker](.scratch/character-creator/issues/02b11-rue-psi-stalker.md), [Civilized](.scratch/character-creator/issues/02b11-rue-civilized-psi-stalker.md) and [Wild](.scratch/character-creator/issues/02b11-rue-wild-psi-stalker.md) owners. Preserve ownership/dependencies. Add a bounded implementation child only if needed for the actual shared change/acceptance. One representative pair does not close parent12 or the corpus.

Read [next-implementation-steps.md](docs/next-implementation-steps.md) before coding. It contains the original-page audit, exact pool/award schedules, XP endpoints, independently checked attribute/resource/percentage fixtures and equipment variants. Keep those numerical rules there as the single preparation reference. No Psi-Stalker product declarations or workflow tests have been implemented.

The first concrete framework gap is a permanent rolled saving bonus: class numeric additions currently accept fixed integers, while Psi-Stalkers receive a retained1D4 magic-save bonus. Assess `recorded_formulas.py`, `retained_acquisitions.py`, `numeric_contributions.py` and `class_contributions.py` for a neutral source-bound solution. Require no-dice projection/reopen, retained replay, inactive malformed-declaration rejection and compatibility before activation. Do not approximate the die or add a class-name handler.

Candidate ownership: one Psi-Stalker race with shared racial pools, Civilized/Wild class variants and source-bound Wild P.S./P.P. additions. Review its source fit; this is a candidate, not an imposed schema. Reuse creation pairings, per-attribute pools/provenance, owned skill/equipment profiles, ordinary skill effects/awards and fixed psychic entitlements. Preserve Human pairings and exact saved pins.

Resolve the remaining source decisions in one coherent audit: exceptional dice for3D6 versus modified/4D6 pools; starting ISP versus later gains; psychic save target; six Sensitive choices and distinct inherent senses; animal-empathy riding/taming bonuses; Coalition/independent/Wild equipment ownership. General HP/SDC and XP have reviewed fixtures in the detailed guide. Resolve ordinary ambiguity autonomously, record the interpretation concisely and obtain independent Spec review rather than repeatedly asking minor rules questions.

Exercise both variants and each implemented equipment variant through public creation/selections, advance/undo, exact no-roll portable/reopen and actual packaged browser/PDF acceptance. Required attributes, resources, saving bonuses and skill percentages must work. Optional situational simulation may remain descriptive. Full saved-identity migration is separate required work; establish an actual dependency before making it block initial nonhuman creation.

Afterward reassess actual ticket dependencies for further races/classes, completing partial paths such as City Rat, magic/Heroes families and construction. The user has not replaced the broader scope with a Psi-Stalker-only project.

### Optional measured performance follow-up

The detailed guide records a scratch probe: repeated skill views decode131 immutable definitions although the witness pins nine. A counterfactual containing only nine preserved canonical output and lowered median view time about57%. This is a lead, not a production fix or full-suite speed claim. Harness: `tmp/05d25-performance-probe.py`; baseline/profile files are named in the guide.

Treat optimization as a separate bounded change if justified. A shared exact-pin resolver must preserve every history frame, inactive class dependency, missing/conflicting-pin rejection, old-save fallback, mutation isolation and export semantics. Preserve historical archives. This is not an additional source-content activation gate; its value is shorter player interactions and validation as the catalog grows.

## Authorities and scope

Load references selectively rather than rereading the entire historical backlog:

1. [Player-focused amendment](docs/player-focused-scope.md): authority over conflicting older exhaustive calculation requirements.
2. [Specification](docs/character-creator-spec.md), [design decisions](docs/design-interview.md) and [original ticket plan](docs/character-creator-ticket-plan.md): requirements/final comparison baseline.
3. [Issue-tracker rules](docs/agents/issue-tracker.md), active child/canonical tickets and latest [progress](docs/implementation-progress.md): ownership/dependencies/completion.
4. [Class import review](docs/class-import-framework-review.md), [owned profiles](docs/owned-class-profile-contract.md), [shared catalogs](docs/shared-profile-catalog-contract.md), [racial creation](docs/racial-creation-contract.md) and [psychic entitlements](docs/class-psychic-entitlements.md): shared boundaries and their actual limits.
5. [Accepted manifest](characters_unlimited/packs/accepted.json), current declarations, focused workflow tests and final evidence: executable/versioned truth. Identity inventory and synthetic tests alone are not source certification.

The frozen13-book corpus and owning entries are recorded in [source-inventory.json](characters_unlimited/data/source-inventory.json) and the canonical source tickets. Preserve that inventory and its distinction between identity review, mechanical review and actual automation. It remains the coverage frontier after representative paths work.

Games remain Rifts Ultimate Edition and Heroes Unlimited2E, with separate UI/catalogs. Palladium Fantasy is deferred. Applicable supplied options remain required. Prioritize character choices, prescribed attribute/house-rule generation, granted/selected skills and actual percentages with applicable bonuses, meaningful ability choices, categorized equipment, safe revision/saves and editable sheets.

Exhaustive maneuvers, activity speeds/fatigue and encounter simulation are not release gates. General insanity is excluded except option-specific Crazy/permanent injuries. HU Mega Heroes, bases/headquarters and super-vehicle design are excluded. Ordinary vehicle possessions are in scope; robot and bionic construction remain required. Eligibility/count guidance stays honor-system, without GM gates or mandatory override markers.

The final retrospective must compare the original plan, user-approved simplification and delivered utility, after required delivery/final acceptance are actually complete. It is not due now.

## Validation and publication process

For each meaningful slice:

1. Identify exact source facts, owned declarations, affected callers and required workflow witnesses. Preserve historical accepted files; add new immutable versions/update the manifest only after source review.
2. Implement shared declarative boundaries. Run narrow meaningful source/compatibility selectors first. Preserve raw rolls, learning ages, revision conflicts, undo/replay and exact pins.
3. Run required static/final integrated checks on a stable candidate. Independently review Standards and Spec against a fixed baseline, originating ticket and amended scope. Verify review-driven deltas at appropriate scope.
4. Build Windows and exercise the separate packaged workflow. Verify actual UI creation/revision/advancement and public portable/reopen behavior. Check canonical PDF fields/widgets/appearances and visually inspect every page. Label helper-based fixture completion honestly.
5. Prepare scoped commit/PR using the repository template. Recheck committed head and both push/PR Windows workflows, including packaging/frozen/artifact steps, before merge. Mark done only after verified merge and receipt.

Required commands are owned by [.github/workflows/check.yml](.github/workflows/check.yml). Existing environments are present; verify them before installing/recreating anything. Python3.14/Node22 match CI. Dependency versions come from `requirements-dev.txt` and `requirements-build.txt`. Available Node22 is `tmp/node22/node_modules/node/bin/node.exe`; locate an equivalent if that scratch install is absent. The global Node may differ.

Typical local commands from the repository root:

```powershell
$ErrorActionPreference = 'Stop'
.\.venv\Scripts\python.exe -m unittest tests.test_named_skill_pool_awards tests.test_robot_pilot -v
if ($LASTEXITCODE -ne 0) { throw 'Focused workflows failed' }
.\.venv\Scripts\python.exe -m mypy --check-untyped-defs characters_unlimited tests
if ($LASTEXITCODE -ne 0) { throw 'Typing failed' }
.\.venv\Scripts\python.exe -m compileall -q characters_unlimited tests
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
foreach ($browserScript in Get-ChildItem characters_unlimited/web -Filter '*.js') {
    & '.\tmp\node22\node_modules\node\bin\node.exe' --check $browserScript.FullName
    if ($LASTEXITCODE -ne 0) { throw "Browser syntax failed: $($browserScript.Name)" }
}
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace check failed' }
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Full regression failed' }
.\scripts\build-windows.ps1 -Python '.\.venv\Scripts\python.exe'
$env:CHARACTERS_UNLIMITED_EXE = (Resolve-Path 'dist\CharactersUnlimited\CharactersUnlimited.exe').Path
.\.venv\Scripts\python.exe -m unittest tests.test_packaged_app -v
if ($LASTEXITCODE -ne 0) { throw 'Frozen executable workflow failed' }
```

These are references, not instructions to repeat accepted pilot checks on startup. Select tests for the new slice. Check each exit status/preserve complete logs; partial/interrupted runs are not passes. `scripts/check.ps1` mixes `.venv` and bare `python`; explicitly use the intended interpreter if environment resolution is uncertain.

The final local suite took about84 minutes; hosted runs can take roughly1–2 hours. Plan the queued budget accordingly and keep long jobs observable in task-owned logs. Source review/preparation can proceed while CI validates a fixed commit. Avoid changing that commit or repeating expensive passing checks without a new concern. Follow runtime wait limits/report meaningful progress. At a deadline preserve job/run identities and stop local watchers; remote CI may finish independently. Conversation transfers or receipt-only changes do not invalidate unchanged product acceptance.

## GitHub authorization and tools

Follow the current personal instructions' owner-gh policy. Repository-scoped operations use:

```powershell
& 'C:\Users\jaken\AppData\Local\Programs\Python\Python314\python.exe' '-I' '-S' 'C:\Users\jaken\.codex\tools\owner-gh\owner_gh.py' --repo the-grognard-codes/characters-unlimited pulls/137
```

Use `--help` for REST/query/body options, `--auth-status` if needed. Request outside-sandbox execution for this exact installed command when host authentication/network is needed. Its saved allowance is repository-scoped; it does not extend to direct `gh`, arbitrary GraphQL, account-wide operations, credentials or local `git push`. Existing workflow authorization and actual runtime approval boundaries both apply. Never copy tokens or change credentials as a workaround.

Useful GET endpoints: `branches/main`, `pulls/137`, `actions/runs/38351032330`, `actions/runs/38351050663`, and each run's `/jobs`. Current step success was checked through `/jobs`, not inferred from old logs.

When the resumed task reaches the authorized merge, use `PUT pulls/137/merge` with the exact reviewed `sha` and `merge_method: "merge"`. Refresh state beforehand and confirm response/actual merged state afterward. Inspect remote state before retrying an uncertain write. Use `--input-stdin` for JSON bodies if convenient. Local development stays sandboxed; normal runtime approvals apply to Git metadata/push where required. Explain a real auto-review rejection and its concrete blocked action; do not invent broad shell privileges.

## Sources, runtime and artifacts

External original sources:

- Corrected RUE Markdown: `C:\Users\jaken\Git-Hub\rpg-docling-pipeline\data\processed\Rifts - Ultimate Edition.md`.
- Original RUE PDF: `C:\Users\jaken\Git-Hub\rpg-docling-pipeline\data\raw\Rifts - Ultimate Edition.pdf`.

Both are present here. Fingerprints/page/candidate locators are in owning tickets/evidence; the detailed Psi-Stalker guide records the expected PDF SHA256. Recheck the relevant fingerprint before consuming sources for new accepted content. Pipeline outputs/originals are read-only creator inputs. Historical `sources-markdown/` and `sources-pdf/` mirrors are absent here; resolve references to actual pipeline files. A clone does not provision those inputs.

Scanned PDF text extraction can be empty. Render cited pages/inspect columns. Adjacent class columns interleave in RUE OCR; preserve class ownership rather than importing a neighboring schedule/package. Psi-Stalker renders under `tmp/pdfs/05d26/` are reviewed scratch conveniences, not accepted content. Discover a trusted Poppler installation; keep machine-specific cache paths out of product code.

Latest local binary: `dist/CharactersUnlimited/CharactersUnlimited.exe`, built for the pilot slice. No new build was performed for this refresh. A clone does not restore `dist/`, environments, source mirrors, scratch proofs or player data; runtime templates and tracked evidence remain in Git. Hosted artifact retention is14 days, so inspect availability rather than assuming an old download exists.

For a new browser proof choose a free port and isolated task-owned data directory, for example:

```powershell
.\.venv\Scripts\python.exe -m characters_unlimited.server --data-dir '.scratch\psi-stalker-browser-data' --port 8876 --no-browser
```

Use supported browser/computer-use tools for actual UI evidence and public application interfaces for portable/projection witnesses. Close only task-created servers/tabs. Preserve player libraries under `%LOCALAPPDATA%\CharactersUnlimited` or the configured location. Last pilot test servers/tabs were closed and its local CI monitor exited at the October13 stop; recheck ports/processes before reuse. This document starts no monitor/server/schedule.

The host may print an `InitializeDefaultDrives` FileSystem-provider warning even when the requested read succeeds. Judge actual exit code/expected output; investigate genuine missing files or failed commands separately. It is not a reason to reset the workspace.

## Suggested skills and delegation

Read actual available files; installed paths/catalogs can change:

- `code-review`: `.agents/skills/code-review/SKILL.md`; independent Standards/Spec axes. It explicitly requests parallel review agents. Follow current routing/model pins; reuse prior agents when their retained context is relevant.
- `pr`: `.agents/skills/pr/SKILL.md`; required PR-body template for new publication.
- `codebase-design`: neutral retained-saving-bonus interface or a real resolver optimization.
- `diagnosing-bugs`: demonstrated behavior/performance failures; establish a tight reproducer first.
- `pdf:pdf` and `computer-use:computer-use`: rendered/editable-sheet and actual UI acceptance.
- `writing-for-agents` and repository `handoff`: future continuation documents. Update this requested repository handoff in place; preserve historical transfer bundles.
- `retro`: environment-review aid at final completion, alongside the separately required original-plan-versus-product retrospective.

Respect current routing. Routine lookups/known small document edits do not automatically need agents. Keep ownership bounded, preserve concurrent edits and avoid repeating passing validation. Independent review should evaluate source correctness and implementation rather than echoing the implementer's assertions.

## Stop and full completion criteria

At a requested deadline stop active local implementation/monitoring and record branch/head, owned changes, test/job state, PR/run URLs, review findings, source decisions and first safe resumption action. Preserve incomplete work honestly; pending CI or a ready prototype is not a completed slice. Do not create a schedule/hidden continuation to evade a stop.

Claim full completion only when amended required corpus/capabilities, construction, safe saved revision/portability, representative end-to-end workflows, Windows release package and final acceptance have evidence. Then deliver the retrospective comparing original plan, approved simplification and usable product. Until then report bounded support and material gaps explicitly.

## Suggested queued task

The user can use the following as an explicit implementation prompt, adding the desired time limit in the queued task:

> Resume Characters Unlimited using HANDOFF.md and docs/next-implementation-steps.md. Recheck current state, finish the reviewed passing PR137 merge if still applicable, reconcile receipts, then implement the Civilized/Wild Psi-Stalker batch and continue the approved amended plan. Use the normal process, including scoped commits, push, PR creation, independent reviews and merges after all required validation passes, within the available runtime permissions. Continue across completed slices within this task's work budget. At its stop condition, preserve exact progress and next actions and stop. Do not create a separate recurring automation. Report supported capabilities and remaining gaps honestly; deliver the final retrospective only when the required product is complete.
