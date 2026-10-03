# Portable saves and backup validation

Validated against main 7fb7945. The full 23-test suite, mypy, and Python/JavaScript syntax checks pass. Focused HTTP verification also passes after closing the error response explicitly.

Portable workflow checks reopen exports in a separate offline data folder, preserve manual values/history/skills, retain independent duplicate identities, include both rule packs for untouched characters, and reject unsupported/altered packs, inconsistent values, forged dice, missing fields, and false source citations without changing existing saves. Import replays the recorded generation and verifies its source against the pinned pack. Earlier records without generation metadata remain compatible; their already-used domestic v1.0.0 is pinned explicitly rather than resolving a later version.

Backup checks reopen an actual SQLite snapshot and inject a publication failure to verify that the previous backup and live save survive. A SQLite failure at the HTTP adapter returns a controlled JSON error.

Browser checks duplicate the character, download a 13,009-byte portable JSON file through Microsoft Edge, inspect its exact core/domestic versions, import that file through the embedded browser without replacing either existing character, and create a database backup. The browser download event API did not report the completed Edge download; its actual file was verified. Edge's extension could not automate file selection without its file-URL permission, so import was verified through the embedded browser instead. No extension permissions were changed. See [backup and library evidence](18a-portable-backup.jpg).

Independent standards/spec reviews found missing domestic pins, incomplete value/dice validation, and missing provenance validation. These are repaired and both focused reviews approve. Rule archives, explicit correction previews/upgrades, additional games/options, and higher levels remain in parent 18 and later slices.
