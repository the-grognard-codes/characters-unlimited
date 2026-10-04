# Shared retained resource growth (22D2)

Additional growth belongs to advancement definitions, not class/race handlers. Rifts `advancement` and `higher_advancement`, and the corresponding Heroes packs, may declare `resource_gains` keyed by generated starting-resource identities (HP, SDC, PPE, ISP or another declared identity). Each value contains exactly `formula` and `source`; ordinary numeric formula bounds apply, and source needs nonempty book and section evidence. Optional page metadata is retained. Every declaration validates before any advancement dice in a multi-level request.

Each attained-level receipt stores `resource_gains` entries with exactly `value`, raw `rolls` and the exact pinned `source`. Generation, replay and validation use one module across both games. Additional dice ignore initial attribute house options. Empty declarations retain legacy event shapes. Ordinary HP growth remains separate and unchanged.

Resource projections add active first/later contributions with level labels and source evidence. Undo retains receipts but excludes inactive gains; replay, portable reopening and historical snapshots verify the pinned formula without drawing again. Manual fixed totals remain authoritative and adjustments remain additive. Combined calculated totals must stay within the supported exact whole-number range, even when individual terms are valid. Save/import failures preserve the prior character.

A nondefault class cannot inherit the default class's additional growth merely by omitting its own advancement group. This is a bounded ownership guard; legacy ordinary advancement fallback is unchanged and full class/race/R.C.C. composition certification remains open. Both editable PDF exports show resource totals and book/section evidence, including citations without page metadata.

Synthetic fixtures establish the shared engine contract only. No new book rules are accepted. Conditional schedules, ability grants, resource spending, complete class imports, and spell/psionic catalogs remain open.
