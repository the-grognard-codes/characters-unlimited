# 18A: Portable characters, duplicates, and backups

**Status:** complete — merged in PR #5

Independent part of parent 18: duplicate a saved character, export/import a portable JSON bundle including exact supported rule definitions, reject malformed/incompatible bundles without overwriting saves, and create a consistent SQLite backup atomically. UI actions must flush autosaves before exporting or duplicating. Imports create a new identity, preserve values/history and rule pins, and require no network access.

This slice supports the currently accepted Rifts core/domestic pack versions. Unknown versions and altered definitions are rejected explicitly; rule upgrades and an accepted-version archive remain in 18B after corpus review and both-game integration. Parent 18 stays open.

- [x] Application checks prove cross-directory offline round trips, independent duplicates, rejected imports, and backup restore/failure safety.
- [x] Browser buttons support duplicate, portable download/import, and backup.
- [x] Reviews, local checks, and Windows CI pass; scoped PR merged.
