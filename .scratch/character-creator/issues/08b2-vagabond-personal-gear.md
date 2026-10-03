# 08B2: Add fixed Vagabond personal starting gear

**Parent:** 08. **Blocked by:** 08B1, 18C. **Status:** in-progress.

- Add immutable equipment 1.2.0 with the 18 fixed personal-gear entries from the original Vagabond list, printed 98 / PDF 101. Preserve the 1.1.0 starting-funds definitions unchanged.
- Grant the declared quantities without cost on one explicit action, atomically preserving current credits and existing possessions while recording original grant identities and source. Do not grant again after edits or removal.
- Support generic personal-gear inventory with no weapon shots or combat/armor effects. Unspecified prices and weights stay unknown; purchases without reviewed prices are unavailable. Report known carried weight and the count of carried items with unknown weight without treating unknown as zero weight.
- Retain grant receipts through manual possession edits, storage, removal, duplicate, portable import/export and reopening. Reject tampered receipts and changed recorded grant definitions without migration. Old equipment pins require reviewed update before grant.
- Show the grant and unknown values in the builder and editable PDF. Verify public workflows and packaged grant/import/restart, self-review, Standards and Spec review, then commit/PR/merge.

This fixed personal-gear slice leaves armor, gun, spare clip, knife and transport choices in 08B3. Full starting gear, purchase catalogs, sales and parent 08 remain open.
