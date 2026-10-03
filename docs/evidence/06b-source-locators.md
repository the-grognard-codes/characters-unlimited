# Heroes Unlimited Revised 2E — business/education skill evidence

Source: `sources-markdown/Heroes Unlimited - RPG - 2E.md`; original `C:\Users\jaken\Git-Hub\rpg-docling-pipeline\data\raw\Heroes Unlimited - RPG - 2E.pdf`. PDF page is printed page +1 in checked passages. Active IDs below are exact 20-character IDs from `characters_unlimited/data/source-inventory.json`; individual skills are nested under category candidates, not separate inventory records.

| Entry | Rule / dependency | Printed / PDF page; Markdown line; candidate |
|---|---|---|
| Universal skills | All characters know Pilot Automobile, Basic Mathematics, Speak Native Language (+25%), Read and Write Native Language (+20%) regardless of education. Only Pilot Automobile and Basic Mathematics have detailed base/rate definitions here; native-language entries are flat bonuses in the universal list, with no separate base/per-level progression stated. | p.45 / PDF 46; lines 2339–2345; `a58c1581b0b40748045a` (Special Restrictions & Notes). |
| Pilot Automobile | Pilot category. 60% +2%/level; untrained drivers can drive reasonably/follow the road, but stunts, combat, or trick driving crash. | p.56 / PDF 57; line 3300; `29c529c997172bafa9af` (Pilot, Basic). |
| Basic Mathematics | Science category. 45% +5%/level; requires Literacy. | p.59 / PDF 60; line 3412; `541d3dcc41d904060382` (Science). |
| Business Program | Fixed Scholastic grant: Research; Basic Mathematics; Computer Operation; Business & Finance; Law (general). Each gets the education-level bonus. | p.46 / PDF 47; lines 2322, 2349, 2351–2361; `5ad856c28b8b10feadd2` (Business Program). |
| Research | Technical category; 50% +5%/level. Anyone may research/ask questions; skill halves time, helps notice relevant data, and rolls are for difficult/secret/suppressed information. | p.60 / PDF 61; lines 3438–3442; `959908cc1439bf659b71` (Technical). |
| Computer Operation | Technical; 40% +5%/level; requires Literacy; does not include programming or hacking. | p.60 / PDF 61; line 3422; `959908cc1439bf659b71`. |
| Business & Finance | Technical; 35% +5%/level; career/occupation flavor, little direct adventuring effect. OCR corrupts part of the explanation, not the listed rate. | p.59–60 / PDF 60–61; line 3420; `959908cc1439bf659b71`. |
| Law (general) | Technical; 25% +5%/level; introductory coverage of law/customs/procedure across Western jurisdictions. | p.60 / PDF 61; line 3430; `959908cc1439bf659b71`. |

**Bonus/cap cross-check.** Attribute chart gives IQ 16–30 a one-time +2% to +16% to all skills (printed p.15/PDF 16; lines 803–807; `434a46446c6eaa474c6d`). Education bonus is one-time for Scholastic/program skills, never Secondary; IQ still applies to Secondary (lines 2290–2294, 2607–2613). Repeated skills across programs take the highest program bonus; repeats are ignored (line 2337). Business duplicates the universal Basic Mathematics grant; the text does not expressly reconcile that cross-list duplication. Sensible implementation is one Basic Mathematics skill, with the Business Scholastic bonus once if that program is selected—this is an interpretation, not explicit wording.

Ordinary maximum proficiency is 98%; special Hardware/Special Training roll procedures may show >100%, while retaining a 98% rating margin (line 2655; printed p.48/PDF 49; `1a76bf3bd8c875d13eff`). Street Schooled characters can trade a Street or Secondary skill for literacy; otherwise literacy is barely 3rd-grade, 30% +2%/level (line 2302; printed p.45/PDF 46). The general Literacy entry says 30% +5%/level and educated people have 98% native-language literacy (line 3434); the native-language +20% grant is not reconciled with these specific literacy rules. Treat the Street Schooled literacy path as explicit exception; flag the remaining interaction for adjudication.


# Heroes Unlimited Revised 2E — native language and literacy reconciliation

**Original-page check:** The original PDF confirms these locators (PDF page = printed page +1): universal grants on p.45/PDF 46; Street Schooled exception on p.44/PDF 45; Language and Literacy skill definitions on p.60/PDF 61. Markdown: lines 2339–2345, 2302, and 3432–3434 respectively.

> “Speak Native Language (+25%); Read and Write Native Language (+20%)”
>
> “30% +5% per level”
>
> “30% +2% per level”

The universal list grants every character both native-language entries with flat modifiers. The separate Language skill is explicitly for languages other than the character's native tongue and has a 50% base plus 5% per experience level; it does not specify a native-speaking base. The Literacy entry has a 30% base plus 5% per level, but says educated individuals have 98% literacy in their native language. It does not say whether the universal +20% is applied to that 98%, or whether it instead represents a separate native reading/writing skill. The ordinary proficiency ceiling is 98%, so applying +20 to an already-98% Literacy value would not increase its ordinary rating; the text does not explicitly direct that operation.

Street Schooled is the specific literacy exception: unless the character gives up a Street or Secondary skill for literacy, they can barely read/write, capped at third-grade level, with 30% +2% per level. The rule does not explain whether the universal +20% modifies that reduced rate. Trading a skill removes the stated illiteracy condition, but the resulting rating is not specified in that passage. Keep these as separate grant/rule records; any arithmetic reconciliation needs a table ruling rather than a claimed explicit book formula.
