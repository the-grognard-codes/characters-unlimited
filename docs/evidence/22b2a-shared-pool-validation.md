# 22B2A shared entered-selection pools

Base: `ec893471c9296ce75e52a1114fc4a2815feb3111`. Scope: entry-count policy shared by Rifts optional pools and Heroes Secondary skills. Category/tag selectors and full grants are subsequent22B2B work.

## Before / after

- Four Heroes Secondary malformed-cost fixtures (zero, boolean, fractional and unknown reference) were RED: an empty selection could be saved. Shared validation makes all four GREEN and preserves the prior character exactly.
- Four Rifts fixtures (boolean/negative pool allowance, zero unselected cost and unknown cost reference) were RED. Shared validation makes all four GREEN with atomic rejection.
- Existing source-grounded workflows protect weighted Paramedic costs, duplicate entry spending, excess/outside-category honor choices, specialty normalization, once-only benefits, advancement, portable reopening and explicit correction previews. A slot debit does not grant another effect.
- Read-only audit found no archived cost incompatibilities in either game's existing packs/profiles. Accepted pack bytes and save shapes are unchanged.

## Checks

23 affected tests passed in9.329 seconds. Required mypy passed over123 source files and Python compilation passed. The fixture import initially conflicted with mypy's test module mapping; isolated archive setup resolved it without changing tool configuration. Standards and Spec reviews both APPROVE. Standards noted a stale distinct-only docstring; corrected before final approval. Reviewers did not rerun tests. Full suite passed:385 tests in243.663 seconds, with one frozen-only skip. Browser-script syntax and whitespace passed. Exact-head Windows/frozen verification remains pending.

No UI/PDF layout changes; existing editable-PDF/HTTP workflows remain in the full suite.
