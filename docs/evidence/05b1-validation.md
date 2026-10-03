# I.Q. skill bonuses and domestic-rule correction validation

Original Rifts Ultimate Edition printed p. 281 (PDF 284) was visually checked: I.Q. 16 grants +2%, increasing to +16% at 30. Printed p. 284 (PDF 287) specifies +2% for each five additional points above 30. The corrected Markdown definition paragraph also states that the bonus applies once to all O.C.C., related, and secondary skills. The new domestic pack records these source pages; 1.0.0 remains unchanged and accepted alongside 1.1.0.

Four focused workflow checks verify chart boundaries and beyond-30 intervals, effective fixed/additive attributes, every currently supported pool, repeated-domestic bonus precedence, the 98% cap, read-only previews, exact pre-update backup restoration, portable imports, and stale/tampered/backup-failure/SQLite-update-interruption rejection. All 34 workflow tests, mypy, compilation, and JavaScript syntax checks pass.

Browser evidence: Rowan's I.Q. 16 character retained Cook 50%, Dance 45%, Fishing 55%, and Sewing 40% before accepting the update. Preview showed 52/47/57/42 and unchanged selection counts. Cancel retained 50/45/55/40. Applying created an actual before-update backup and switched the pin to 1.1.0. Expanded Cook shows base 35 + class 15 + intelligence 2, citing pp. 281/284. A second preview has identical before/after values and disables application. Screenshots: `05b1-rule-preview.jpg` and `05b1-updated-skills.jpg`.

Other attribute effects and low-I.Q. entitlement/penalty rules remain explicitly identified as gaps. This is a domestic-only correction workflow, not completion of every rule-update case or the representative whole skill path. Reviews and Windows CI are required before merge.

Spec review caught a missing cap explanation. The projection now retains each uncapped total, and expanded rows explicitly state the 98% limit when it applies. Focused checks, type checking, and browser verification confirm I.Q. 1000 produces Cook 98% from an uncapped 454%, with the p. 301 citation. Focused re-review approved the repair; standards review found no issues.
