# 18B3 exact rule resolution validation

In progress on `codex/exact-pinned-rule-resolution`, created from clean synchronized main `15c901abed58407af9234f657c7f8b199869b686` after PR138 merged2026-10-24T21:19:17Z. The unrelated historical transfer folder remains untracked and preserved.

Public application validation now supplies the archive's exact resolver to the existing portability collector. List-backed callers remain supported. The same dependency/history walk preserves output order, all source-bound inactive psychic dependencies and exact historical versions. Each collection validates pin strings before caching, checks returned identities, resolves each unique identity/version once and deep-copies each returned definition once. The cache lasts for one collection. Accepted archives/defaults, serialized saves, source validation, upgrade behavior and the10MB bundle guard are unchanged.

The public regression witness failed against the old implementation because reopen and views expanded the complete archive. After the change, the initial19 exact-resolution/portability/rules methods pass28.047s. The final exact-resolution subset adds a historical-cache rejection witness and explicit no-dice replay. Seven actual per-attribute racial-pool/provenance methods pass40.622s. Initial typing caught only two missing annotations in negative test tables; corrected typing passes217 files. Broader compatibility, final typing after the additional test, full regression, Windows/frozen, packaged output/PDF comparison and independent reviews remain pending.

Read-only timing comparison uses the same three completed primary Psi-Stalker saves, all135 accepted definitions and three repetitions of each public method. Every canonical result matches the original baseline, including complete portable bundles; no dice were drawn and primary saves are unchanged. Times are machine-specific supporting evidence; work-count tests protect the optimization without timing thresholds.

| Save | Reopen before / after seconds | Skill view before / after seconds | Export before / after seconds |
| --- | --- | --- | --- |
| Civilized independent |0.3296 /0.0833|0.5172 /0.1918|1.1533 /0.5195|
| Civilized Coalition |0.3445 /0.0980|0.4668 /0.2432|1.0735 /0.5899|
| Wild level5 |0.3816 /0.1068|0.4917 /0.2170|3.9903 /3.2359|

The other four public methods also match exactly. Logs, three-round metrics and exact collected outputs remain ignored under `tmp/05d27-resolution-*`. The first diagnostic attempted to serialize several independent outputs through the single-bundle10MB guard; only the diagnostic writer was corrected, then the complete read-only capture passed. An initial compatibility selector named a nonexistent `test_attribute_pools` module; its real per-attribute and provenance modules were selected separately and passed. Preserve diagnostic failures as such rather than relabeling them green.

No18B3 completion or merge is claimed. Parent18B, parent12 and the wider amended product remain open.
