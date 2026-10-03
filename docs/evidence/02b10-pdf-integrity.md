# Supplied PDF footer integrity audit (bounded)

I compared standalone terminal folio OCR/text across the 13 supplied PDFs and visually checked suspect transitions. This is a pagination-integrity pass, not a page-by-page content review. OCR false positives from contents/index tables and last-page ads were excluded; wide spreads were treated as containing multiple printed folios. Fingerprints are from the current `source-inventory.json`.

| Source book | Observed / established printed-to-PDF pattern | Finding |
|---|---|---|
| Rifts Ultimate Edition | Early PDF 4–6 → printed 1–3; visually PDF245→242, PDF246→243 (`+3`) | No new discontinuity at inspected pages; page sequence stable. |
| Heroes Unlimited RPG 2E | PDF3→2; visually PDF252→251 (`+1`) | No new jump found. |
| Aliens Unlimited | PDF3→2; scanned body late PDF191→190 (`+1`) | OCR’s contents/index rows produce false terminal-number hits; no confirmed new transition. |
| Powers Unlimited 1 | PDF4→2; visually PDF14→12, PDF15→13, PDF16→14 (`+2`) | OCR falsely read a contents number at PDF15; folios are sequential. |
| Powers Unlimited 2 | PDF3→2, PDF4→3, PDF97→96 (`+1`) | No new transition; PDF98 is unnumbered back matter. |
| Powers Unlimited 3 | Early `+2`; known PDF61→printed59 then PDF62→printed62 gap; later pages include PDF87 spread | Complex transition intentionally left to PU3 owner; do not apply a blanket offset. |
| Rifts Merc Ops | PDF3→2; PDF72→71; wide PDF73 contains printed72 and73; PDF74→74 | Piecewise locator rule: through printed71, PDF=printed+1; printed72–73 share PDF73; printed74 onward, PDF=printed. PDF73 is 1224×792, visually a two-page spread, not a missing folio. Only current canonical entry is Auto-G, printed48/PDF49; no existing post-72 locator needs repair. |
| Rifts Mercenaries | PDF3→1; visually PDF41→39, PDF42→41, PDF43→41, PDF44→42 | **New verified gap/repeat:** printed40 is absent; printed41 appears on both PDF42 and PDF43 (the same General Smith page content), after which the sequence resumes at printed42/PDF44. Single-page dimensions rule out a spread. |
| Rifts World Book 02 Atlantis | PDF3→2 and late PDF161→160 (`+1`) | No new transition surfaced. |
| Rifts World Book 06 South America 1 | PDF3→2; late PDF169→168 (`+1`) | No new transition surfaced. |
| Rifts World Book 07 Underseas | PDF3→3; PDF130→130, PDF131→132, PDF132→133 | Known omitted printed131, visually confirmed; retain existing 02A3 gap. |
| Rifts World Book 09 South America 2 | PDF3→3; PDF107→107, PDF108→108, PDF109→109 | PDF108 is damaged but present and numbered108; it is not a page-number jump. |
| Rifts World Book 21 Splynn Dimensional Market | PDF3→2; late PDF192→191 (`+1`) | No new transition surfaced. |

## Mercenaries gap evidence and scope

Current hashes: Markdown `fd039ce44880ef66b8596ade7ac05cf8a0573da4e83597902f748e4ce01cd466`; PDF `fa95e8e8d9bc7e43ff5d3169ff67ee793020097000177caa69124a18e5743144`. Boundary evidence is original PDF41/printed39, PDF42–43/printed41 (duplicate content), and PDF44/printed42. There is no physical PDF page to assign to printed40; record the missing folio as printed `[40,40]` between those anchors rather than inventing a PDF page.

Source candidates around the hole: Xiticix `76b093e0cbfb4626681f` (MD1895–1900) and Danger of Atlantis `ab324854940f400d7fb2` (1901–1906) precede it. The Markdown has Mechanoid Threat `9ea851e298d172de986a` (1907–1914) and Role-Playing Battles `d0161e0c320390efe5e4` (1915–1922) in the unverified transition region; original PDF folio40 is unavailable, so their page-level placement/content cannot be visually certified. General Smith is separately visible at printed41: heading `c13cc4fef8367c1ca760` (1935–1936) and named profile `337a87e55ecab606f49a` (1937–1964); it is an NPC, not a reusable mercenary class. Existing Mercenaries canonical entries end at printed50, so none are affected by the gap. The completed identity slice 02B6 is not blocked by this gap; any future acceptance of material assigned to missing printed40 should wait on the 02A3 source-gap record. The table’s company/occupation mechanics occur earlier and are unaffected.

## Limits

Scanned-books’ terminal folio extraction is Windows OCR and can confuse numbers in tables; I visually verified the flagged transitions above, not every page. Embedded-text books use extracted page text plus the prior verified offsets. PU3’s more complex per-page map remains owned by its parallel audit. No source hash or product file was changed.
