# 22F4 ability and player-scope validation

Review base: 0f31766e5c05e6e9fa84f5bbb0fb7781ef8cf4e6 (PR107), identical product tree to merged main f5bdffcf77a91ca892f18266e6a063c2dcb0b7da.

Before: the synthetic ordinary ability failed with KeyError attribute_bonus. A book/section-only PDF source also failed with KeyError printed_page. After: shared retained acquisitions support explicit empty/ordinary groups without attribute mutation, and common source citation formatting accepts optional page locators.

30 affected tests pass (19.147 seconds): player scope, ordinary abilities, attribute saves, mental endurance, physical proficiency, scuba, swimming and ticket coverage. Mypy passes for 153 source files; compilation, all browser JavaScript syntax and whitespace pass. Both independent standards/spec reviews APPROVE with zero actionable findings. Full integration and frozen Windows validation will run in CI before merge.

Browser verification shows the synthetic descriptive ability, unchanged attributes, 140-foot parameter and source without missing-page errors; optional unarmed choices are collapsed. Coverage shows the explicit Mega-Hero exclusion reason. See 22f4-descriptive-ability.jpg and 22f4-scope-exclusion.jpg. The synthetic preview is not accepted book content.

Current editable PDF: 3 pages, 204 fields, no SAVE_INSANITY. Rendered page 1 is legible with the ability, source and four general saving fields; earlier continuation rendering remains legible. Focused public PDF tests confirm normal skill percentages remain and calculated swimming pace/endurance strings are absent. Historical backend calculations and receipts stay compatible.

User amendment excludes general insanity, HU Mega Heroes, super-vehicle/base design, while preserving Crazy traits/permanent injuries and required robot/bionic construction. Canonical audit entries are retained; two known excluded identities are annotated separately. No accepted book definitions change. Broader class/race/ability catalogs and construction remain open.

A final expectation search found one legacy SAVE_INSANITY assertion in the general HU PDF workflow. It now asserts absence; all three editable-PDF workflow tests pass (3.368 seconds). No product changes followed the reviewed/visually verified implementation. Combined focused coverage: 33 passing tests.

The first final-head Windows integration run exercised all 452 tests (519.331 seconds) and found one remaining legacy running-distance PDF expectation. Its two assertions now verify absence of derived miles/km; both affected endurance workflows pass (2.153 seconds). A focused search confirms remaining activity assertions concern preserved backend behavior or descriptive source limits. Product code is unchanged. Combined local affected coverage: 35 passing tests. The corrected final head must pass the full Windows/package gate before merge.

## Final Windows and merge evidence

PR108 merged as `071e80fb83d9c22866cff32e96fe55f5c36f69bd`. Final head `d2d4800d4cf6231415f1f7ee7029489db4b0bd0f`; Windows runs37265040415/37265036825 both pass, including frozen executable validation. Full suite452 tests, one frozen-only skip exercised separately; local affected35 tests, mypy153/static checks and both independent reviews pass. The successful full-suite run recorded460.886 seconds; its frozen workflow passed separately in60.760 seconds.
