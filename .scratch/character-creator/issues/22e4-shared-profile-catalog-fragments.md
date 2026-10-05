#22E4: Explicit shared class-profile fragments

**Status:** DONE. **Review base:**c859a03b70472e7f317f881f7537e762792abb90 (PR101).

Owned profile fields currently replace whole mappings. This isolates mechanics but fields such as combat mix shared catalogs with class choices, so broad imports would repeat those catalogs. Add explicit source-bound catalog references for mapping-valued profile fields, with exact referenced field identity, bounded catalogs, missing-reference rejection and no recursive/executable operations. Class overrides remain explicit and cannot overwrite catalog-owned keys. Resolve all unselected references during preflight and exact-pinned portable replay. Two distinct class profiles must share one combat catalog while retaining different class choices; legacy and plain owned profiles unchanged. This does not certify missing catalog content or actual source-reviewed imports.

Merged in PR102 as f98dc05d1381e358f098a677a0dccdef5ae18e73 after both exact-head Windows runs37245098538/37245095773 passed, including frozen executable validation.
