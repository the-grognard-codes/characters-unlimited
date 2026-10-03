# 02A2: Corrected source provenance and source-gap visibility

**Status:** complete — merged in PR #6

**Blocked by:** 02A

Preserve the original 13-book inventory and fingerprint the corrected Markdown copies without changing accepted character rule pins. Expose source-gap descriptions and line locators in the book/candidate coverage UI. Candidates containing a marked gap carry `source-gap` status. Changed source content receives a new candidate identity, preventing earlier review identities from silently transferring to corrected text. Keep all extraction provisional; this slice does not complete 02B's canonical option/dependency audit or content-ticket fan-out.

Validate multiline gap extraction, unchanged heading with changed content, manifest/PDF identity preservation, and rendered browser guidance. Complete standards/spec review and Windows CI before merging.
