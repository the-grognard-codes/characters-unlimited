# 05D8: Horsemanship and Cowboy percentile validation

Immutable 2.20.0 adds six paired Horsemanship definitions and four Cowboy percentiles, bringing the shared catalog to 191 identities. Original RUE printed 306-307 and 310-312 (PDF 309-310 and 313-315) visually checked against processed Markdown, with Secondary restrictions on printed 300. General preserves the existing required identity. Other occupation-specific riding and Cowboy entitlements remain source guidance; the current Vagabond/City Rat paths receive no invented permission or extra Roping bonus. Trick Riding still needs shared referenced-proficiency training; category completion is not claimed.

44 affected public workflow tests pass in 43.935 seconds. They cover every pair/rate, I.Q., permissions, duplicate required/optional training, late acquisition/reselection/import/undo, old 2.19 pin and explicit upgrade, and editable PDF. Typing (173 files), compileall, Node 22 syntax and whitespace pass. Rebuilt ordinary-user Windows executable passes packaged validation in 40.531 seconds. Full regression, two independent reviews and exact-head hosted gates are required before merge.

Chrome verified optional General 40/20 -> required General selected -> both copies 45/25. Clearing the required choice restored optional 40/20; reselection restored both 45/25. Exotic remains 30/20. Screenshot `05d8-riding-builder.png` shows expanded pairs and source contributions. Mounted effects remain contextual descriptions rather than standing combat totals.

The same save exports `05d8-riding-sheet.pdf`: four pages, 1232 canonical fields and 176 populated widgets, all matching logical values and non-empty normal appearances. Primary and continuation pages visually checked with no clipped values; page 3 (`05d8-riding-notes.png`) preserves all paired checks, source notes and contextual riding guidance. Earlier accepted archive bytes are unchanged.

Spec review corrected Cowboy mounted initiative increments to levels2/5/10/15 (printed311). Seven focused riding workflows pass8.100 seconds after the correction; PDF continuation regenerated and visually verified. Final exact-head gates replace superseded runs before merge.

PR120 merged as a3501f7ce8a16ce7157b966e24d9f44bc8aa2ab4;05D8 done. Both independent axes approve final2334dc7. Final537 local regression575.038s and rebuilt frozen42.472s pass. Both exact-head hosted Windows runs37396456156/37396452670 pass537 tests and separate packaged checks. Broader skill/class/race/ability and construction scope remains open.
