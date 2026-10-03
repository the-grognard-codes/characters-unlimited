# Required Vagabond skills validation

Original Ultimate Edition PDF pages were visually checked for class allowances, Eyeball/Streetwise bonuses, language/radio bases, both horsemanship checks, pilot values and General Repair. Printed page references are retained in pack 1.2.0; older packs remain immutable.

Application tests cover saved/reopened and portable choices, contribution totals, duplicate/native/excess language guidance, both horsemanship checks, invalid/stale writes and correctly paired upgrade previews including secondary checks. The full check script also validates types and Python/JavaScript syntax.

Browser verification used a disposable local database: I.Q. 16 gives native 90%, Barter 58%, identification 62%, radio 52%, Streetwise 32%, other languages 67%, automobile 72%, repair 47% or horsemanship 47%/27%. Immediate navigation preserved unsaved choices. Duplicate and excess languages remained visible with counts and warnings. See `05b2-required-skills.jpg` for the expanded secondary check and source/contribution explanation.

Begging, combat effects/choices, broader catalogs and conditional checks remain pending and are displayed as gaps.

All 39 workflow tests, type checking and syntax checks passed. Spec review found no blocking issue. Standards review caught invalid/duplicate language labels being projected as separate learned grants; the correction preserves all entered labels and warnings while granting only distinct nonblank non-native languages. Focused regression checks cover blank labels as well. Browser preview/cancel from 1.1.0 also preserved existing selections and pins.
