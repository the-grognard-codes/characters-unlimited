# Implementation progress

The user approved the work plan and the branch → implementation → review → validation → commit → PR → merge workflow on 2026-10-02.

## Source strategy

Read completed Markdown from the rpg-docling-pipeline project and use its original PDFs for clarification. Do not mutate that workstream. Snapshot source identity and hashes during corpus inventory because the pipeline can replace processed files. Application work proceeds without waiting for later conversions; content work depending on unavailable or ambiguous passages remains explicitly tracked.

## Slices

- 01: Complete, merged in PR #1. Local Rifts Human/Vagabond identity, initial attributes, notes, transactional saves, and reopen path work. Type checking, four application workflow tests, Python/JavaScript syntax checks, and narrow/desktop browser checks pass. Windows GitHub CI also passes.
- 02: In progress, split into 02A (complete, merged in PR #2) and 02B (complete option audit and bounded content tickets). The scan finds 7,053 section candidates in all 13 books; zero candidates are claimed fully automated. Classifying headings is not a completed corpus audit.
- 03: Draft normal-attribute creation, separate game catalogs, and game-aware identity/save support are prepared on `codex/03-heroes-character`. Heroes Unlimited exceptional-die interpretation awaits the user's ruling; the original PDF (printed page 15) confirms the uncapped wording. Do not publish this slice as complete before resolving that rule. Its owned draft files are preserved in a named Git stash while independent Rifts work proceeds.
- 04: Rifts generation options can proceed independently as 04A; the full two-game slice remains dependent on 03.
- 05–24 and corpus content batches: Not complete.

## Pending source ruling

Heroes Unlimited Second Edition adds a die to an initial 16–18 and says to roll again on another six without stating a terminal cap; Rifts explicitly caps at two bonus dice. An asynchronous question asks the user to choose repeated bonus sixes or a two-bonus-die cap. The original PDF page was visually inspected; do not infer approval from elapsed time or silently copy the Rifts cap.

## Retrospective

Perform the requested retro only after all slices are completed. Compare functionality, visual/media outcomes, and intent with the original ticket plan and record the final assessment in Markdown. Do not label a partial implementation as the completed retrospective outcome.
