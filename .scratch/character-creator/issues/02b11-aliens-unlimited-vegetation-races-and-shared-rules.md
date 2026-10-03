# 02b11-aliens-unlimited-vegetation-races-and-shared-rules: Implement option family, race, rule from Aliens Unlimited: Camleans, Standard Plant Features & Abilities, Chianas and 6 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-camleans` | Camleans / `race` | — | 140 / 141 | `d40ab5c9cd0f822f8d4e` | Original body profile and printed footer confirm the identity. Singer skills are embedded; Kisentite weapons are an external equipment dependency. All numerical and edition-dependent rules remain pending. |
| `au-plant-standard` | Standard Plant Features & Abilities / `rule` | — | 140 / 141 | `81cc558ccae9a0a2fae4`, `3d7739f7ce277fbdf2dd`, `6b98364500b0a64cd3d4`, `188b95a4d28f133125d2` | Original printed 140 / PDF 141 confirms common plant features, three body-armor choices and heightened senses. Complete numerical, sensory, magic and edition reconciliation remain pending. |
| `au-chianas` | Chianas / `race` | Chiana | 141 / 142 | `e08eaf060e0cf91168b1` | Original body profile and printed footer confirm the identity. The separate villain index uses “Chiana”; profile heading is “Chianas.” All numerical and edition-dependent rules remain pending. |
| `au-erythros` | Erythros / `race` | — | 142 / 143 | `7ec0b2848f2ee20440a6` | Original body profile and printed footer confirm the identity. Alphabetical list truncates to “Erythro”; profile heading is “Erythros.” All numerical and edition-dependent rules remain pending.; Truncated OCR index text is a source transcription discrepancy, not an independently confirmed alternate species. |
| `au-kisent` | Kisent / `race` | Kisents | 143 / 144 | `8c46b0099732f0562ce3` | Original body profile and printed footer confirm the identity. Stat heading plural “Kisents”; related Kisentite weapon entries are separate equipment identities. All numerical and edition-dependent rules remain pending. |
| `au-lachinelians` | Lachinelians / `race` | — | 144 / 145 | `14afb47054ca35fc4850` | Original body profile and printed footer confirm the identity. Source describes magic and psionic paths; review their shared class/power dependencies. All numerical and edition-dependent rules remain pending. |
| `au-ikta` | Ikta / `option-family` | — | 145, 146 / 146, 147 | `194202d6777bd54f2ae2`, `8bc7b6f03ba0a1d368c4` | Original printed 145-146 / PDF 146-147 describes a named experimental Anti-Thilik assault division and separate Ikta power/bonus allocation. This records its augmentation branch, not another species or a general organization-as-race rule. Drug and experimental augmentation mechanics remain pending.; Markdown column ordering puts the actual Ikta power paragraph at lines 6591-6593 inside the adjacent Powerball candidate. Original printed 146 / PDF 147 locates it within Sprekalian abilities. The Sprekalians stat-heading candidate at line 6612 does not contain that paragraph and is excluded; mechanical ingestion must reconcile the columns before acceptance. |
| `au-sprekalians` | Sprekalians / `race` | — | 145 / 146 | `194202d6777bd54f2ae2` | Original body profile and printed footer confirm the identity. Ikta is an embedded experimental/enforcer branch, not an independent profile heading. Thilik-3 / Pówerball drug rules are adjacent dependencies, not racial identities. All numerical and edition-dependent rules remain pending. |
| `au-tedeschians` | Tedeschians / `race` | — | 147 / 148 | `4f53efd1f53ec55f36fb` | Original body profile and printed footer confirm the identity. Source says most follow magic; review shared magic dependencies. All numerical and edition-dependent rules remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
