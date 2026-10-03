# 23A: Early self-contained Windows package

**Status:** done

Merged in PR #20 after both reviews and Windows frozen-build CI passed. Final controller visual/interaction acceptance remains with parent 23.

**Dependencies:** Current local application and editable Rifts export. Parent 23 stays open for Heroes Unlimited, advancement, complete coverage and final offline release acceptance.

Build an unpack-and-double-click Windows folder with a bundled Python runtime, accepted rule versions, browser assets, PDF template and licensed fonts. Provide a small desktop controller to open the local browser and stop the application. Data remains under the established user-data directory, outside the package. Report startup failures clearly with a local diagnostic log.

Verify the actual frozen executable from an unrelated working directory with Python and Node absent from PATH. Exercise create/save/reopen, rule lookup, coverage, portable duplicate/import and PDF export through its HTTP adapter. Add a packaged smoke runner for Windows CI. Preserve originals and unrelated work; do not call this the final content-complete release.
