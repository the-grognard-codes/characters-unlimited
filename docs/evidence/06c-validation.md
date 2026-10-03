# 06C validation

The source-grounded High School regression first failed with Research 57% instead of 52% at I.Q. 16. Immutable program pack 1.1.0 removes the unsupported High School scholastic bonus while retaining choices with visible eligibility guidance. The 1.0.0 bytes and accepted hash remain unchanged.

The earlier-version preview tracer then failed because Heroes updates were unavailable. The shared preview/apply workflow now dispatches by game, compares Heroes program skill values, preserves other exact pins and creates a before-update backup. CharacterApplication checks verify preview is read-only, portable import retains an old pin, apply changes only the program pin, and restored backup data matches the pre-update character. Tampered tokens, changed revisions and failed backups preserve saved work. The HTTP adapter exercises token protection, before/after values, exact target pin and stale 409 behavior. Existing Rifts update regressions remain passing.

Full local validation passes 130 tests (one frozen-only skip), mypy over 43 files, compilation and all browser script syntax checks. After exposing warnings beside the skill results, the affected browser scripts pass syntax checks again. The frozen Windows check now includes importing a legacy Heroes program bundle and explicitly upgrading it without developer tools on PATH; CI must validate it before merge.

Edge opened a legacy High School/I.Q. 16 character at program 1.0.0 with Research 57%. Preview showed Research 57→52, Mathematics 52→47, Computer 47→42, Business 42→37, Law 32→27 and unchanged Pilot Automobile 62. Cancel retained 57%. Apply produced the expected 1.1.0 pin and backup path, preserving the choice, education and attributes. Reopening retained Research 52% and the visible eligibility warning. Both captures were inspected: [before/after preview](06c-heroes-update-preview.png) and [corrected character](06c-heroes-updated.png).

Source evidence: [06C locators and arithmetic](06c-source-locators.md). Remaining Heroes programs, Secondary skills, native-language interpretation, powers, combat, equipment, progression and PDF remain unfinished; this slice does not close parent 06.

PR #35 merged after both Windows builds passed; the frozen acceptance described above is satisfied.
