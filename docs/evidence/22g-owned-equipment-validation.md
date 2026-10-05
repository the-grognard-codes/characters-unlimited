# 22G equipment import validation

Review base: `071e80fb83d9c22866cff32e96fe55f5c36f69bd` (PR108). Contract: `../owned-equipment-import-contract.md`.

Before implementation, the owned fixture was rejected by legacy profile shape checks and malformed unselected equipment drew initial dice. Six public workflow witnesses now pass: explicit empty ownership, pre-dice/pre-save whole-profile rejection, source-grounded Vagabond/City Rat grants with unchanged attributes/skills, shared catalog references and synthetic additional-owner choices, retained portable receipts, and credits-only fixed funds without dice or invented saleable goods. No accepted book archive changed.

Final affected suite: 27 tests passed in 26.925 seconds. Mypy with `--check-untyped-defs` passed all155 source files. Python compilation, all browser JavaScript syntax checks and `git diff --check` passed. Independent Standards and Spec reviews both approve with zero findings. Full Windows regression and frozen executable checks remain the merge gate.

Actual browser witness on local port8815 shows 1,500 fixed credits, the book/section-only synthetic citation and generic starting-equipment heading. The fixture is explicitly synthetic and is not a new book rule. Screenshot: [equipment import](22g-equipment-import.png). The editable three-page Rifts PDF was generated from the same witness; its third-page continuation visibly shows the constant formula, credits and citation without clipping. PDF field assertions also passed. Existing Poppler Symbol/ArialUnicode warnings did not affect the reviewed text. No layout/template changed.

PR109 merged as `32ad13d99c0aaf13bdd3693dfbae09f4dc59be50`. Both exact-head Windows runs37322644681/37322744587 passed at `23257468f732a505dbdca781bd845444ef5bdcf9`, including frozen executable validation. Full regression458 tests (one packaging-only skip exercised separately); first run356.307 seconds, frozen21.999 seconds.
