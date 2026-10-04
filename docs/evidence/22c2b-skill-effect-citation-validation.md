# 22C2B skill-effect citation verification

Base: `d15d9e3bb54d0ee6e320c1dfb75ad12027145a25` (22C2/PR98).

Actual browser inspection found Cooking67 and its7-point contribution visible, but the projected synthetic source citation absent from the explanation. A shared browser helper now formats each effect's display name, existing book/page citation and section; both game renderers append it only when effects exist.

Browser verification confirmed Rifts Cooking67 with `Synthetic framework fixture — Shared skill effects`, and Heroes Basic Mathematics52 with the selected power's7-point effect and `Synthetic framework fixture, printed p.1 — Shared mutant skill effects`. Fixtures are explicitly synthetic and accept no book content. Both screenshots are retained beside this record. All browser scripts pass syntax and whitespace checks. The underlying22C2 full413-test regression/type checks remain applicable because this slice changes browser presentation only. Both independent re-reviews APPROVE without rerunning tests. Exact-head Windows/frozen checks are pending. Publication base is the identical merged22C2 tree `d59bd14d1fa13dd53a9d48ce6f95bb02df093a90`.


The Spec review found that Heroes shared ability rows hide the ordinary Acrobatics/Gymnastics rows. A per-member evidence loop now shows both effect citations without changing best-proficiency calculations. Actual browser verification through Physical/Athletic confirmed both sources and shared balance72 rather than adding72+62; the third screenshot records this path. No new automated test was added for this presentation-only change; browser verification covers all three affected display paths. Required mypy134 and compilation pass as well.

PR99 merged as `6debd9a12fc69dd541f7f8ff84c3751e84d30475` after both exact-head Windows runs37241071135/37241068412 succeeded, including frozen executable validation.
