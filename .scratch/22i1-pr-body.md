## Summary

Future psionic, magic and power adapters need one selection boundary rather than separate class handlers. This slice supplies game-separated, source-bound selections and retained rolls using existing common primitives.

```text
ability catalog + pinned skill catalog
  → whole-catalog preflight
  → retained acquisition state
  → allowances / descriptions / requirements / skill bonuses
```

Parent22I stays open for natural psionics/ISP, application/save/import integration and builder/editable-sheet presentation. No accepted source catalog is activated here.

## Evidence

- **Before:** shared primitives had no neutral combined selection state.
  **After:**23 focused tests pass, including retained2D6+3=11 after removal/JSON replay/reselection, level3 range20, Concealment+10, Biology+0 and honor-system allowance guidance. Invalid inactive receipts/catalogs reject before dice.
- Mypy159, compileall, browser syntax and both independent review axes pass. Exact-head Windows regression and frozen executable checks required before merge.
- Contract and evidence: `docs/common-ability-selection-contract.md`, `docs/evidence/22i1-common-ability-selection-validation.md`.

## Merge Danger

**Door:** two-way

Standalone engine module; no accepted archive, save schema or UI change.

**Blast Radius:** bounded

Future adapters consume the common state. Synthetic fixtures do not certify source imports.
