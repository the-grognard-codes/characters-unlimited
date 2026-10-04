# 22E2 racial source provenance verification

Review base: `fc68c770214584daea9c8a4b37b532e7839e8895` (22E1/PR96). Publication base: `dfa6706f6c2b8150d8f340547ad96ea3b1e91251`, the identical merged tree.

The public race-default/per-attribute citation fixture was RED: I.Q. retained the global core citation instead of its declared race source. The shared resolver now supplies race defaults and individual overrides to generation and rerolls. Portable reopening preserves current attributes, roll history and the retained starting-HP P.E. snapshot; tampered citations in all three locations reject.

Legacy core fallback with a single Heroes attribute override passes. Seven malformed default/override declarations reject before any die. These safeguards passed first execution against the implementation. An initial fallback test used the wrong public game identifier; correcting the fixture to `heroes-unlimited` resolved that test error.

Fourteen affected public tests pass in9.290 seconds. Full regression passed405 tests in315.473 seconds, with one frozen-only skip. Required mypy passed132 source files; compilation, all browser syntax and whitespace passed. Independent Standards and Spec reviews both APPROVE without rerunning tests. Compatibility audit validated4 core archives/4 races/32 unchanged legacy citations. Exact-head Windows/frozen validation is pending. No accepted book definitions change. The contract is bounded to citations, not complete class import or source certification.
