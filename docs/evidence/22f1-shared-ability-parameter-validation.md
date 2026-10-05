#22F1 shared ability parameter verification

Review base:5dee95d1dbb2332e2b3cded2070e4ad9ff44c412 (PR102).

The first public test found raw metadata without a calculated value. Shared projection now computes source-bound range/cost/duration and literal save guidance. The synthetic duration grows2→6 minutes across levels1→3; energy remains24 because display costs are not automatically spent. Portable reopening and a newer active fixture catalog retain old pinned duration6. Editable PDF fields include calculated values and source book/section.

Origin1 separately yields5→11 minutes, including retained inactive views/PDF and remove/reselect without new power rolls. Invalid unselected metadata (null list, missing citation, boolean number, fixed overflow or executable callback key) rejects before power dice and preserves saved state; these safeguard tests first passed after implementation and are not claimed as initial failing tests. Four focused tests pass (3.612 seconds); mypy142 and power-script syntax passed before the fourth fixture. Final static/full regression, actual browser verification, independent reviews and Windows/frozen validation pending.

All new fixtures are synthetic; no actual spell, psychic or power metadata is accepted. Original PDFs are available in the pipeline raw directory; Rifts is image-only, and a native HU extraction scan failed at a later malformed CMap. Partial extraction is not complete source verification.

Final local430 tests pass (351.866 seconds, one frozen-only skip); mypy142, compilation, all browser scripts and whitespace pass. Actual browser proofs show active and retained inactive duration6 with all four source-bound rows. Browser inspection caught a Windows encoding error in new separators; literal Unicode escapes and UTF-8 document writes repair it. Screenshots: `22f1-ability-parameters-active.jpg`, `22f1-ability-parameters-inactive.jpg`. Standards review APPROVE; Spec and exact-head Windows/frozen checks pending.

Spec review APPROVE: no actionable findings. Neither reviewer reran tests. Legacy optional-parameter compatibility passes for every archived accepted power pack at levels1/15. Exact-head Windows/frozen validation pending.

PR103 merged as563bcee20757dd9f9332b4e21424d8e1af4cc0e4. Both Windows runs37246351844/37246382013 passed at exact head d33357783092fb19002a3261700f2f6bd0b9b518, including frozen executable checks. Attachment failed because this thread exceeds100 attachment identities; no previous attachments were removed.
