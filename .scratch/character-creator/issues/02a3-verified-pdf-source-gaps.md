# 02A3: Preserve independently verified PDF gaps

**Status:** done (merged in PR #22)

The Underseas original skips printed page 131 between PDF pages 130 and 131. Ticonderoga systems and continuing text cannot be ingested completely. Record this independently verified gap without changing the source workstream's files. Bind the record to both source hashes, reconcile it into coverage and CLI rescans using an explicit registry input, reject stale evidence, and keep affected candidates blocked. Reconciliation must be idempotent and preserve unrelated metadata and the existing Destroyer Borg gap.

Verify the original neighboring pages visually. Test source hash changes, invalid ranges, containing/intact candidates, repeated reconciliation, original byte preservation and the active two-gap view through the source/application seams. Browser coverage must expose the finding. Pass both review axes, local checks and Windows package CI before merge. This is a prerequisite correction; parent 02 and complete supplement identities/mechanics stay open.
