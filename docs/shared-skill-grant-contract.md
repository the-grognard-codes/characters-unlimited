# Shared skill-derived grants (05D3)

A reviewed skill may declare `granted_skills`, a bounded list of objects with exactly `skill_id`, `bonus` and `source`. Targets must be distinct known ordinary percentile skills without specialties or Physical acquisition effects. Bonuses are nonnegative exact integers; source requires book and section. Every catalog declaration validates, including unselected parents. Unknown targets, malformed declarations and cycles reject before saving; owned-profile preflight rejects before generation draws. Older archives without declarations retain their behavior.

```json
{"granted_skills":[{"skill_id":"basic-mechanics","bonus":20,
  "source":{"book":"Rifts - Ultimate Edition","section":"Vehicle Armorer","pages":[312,313]}}]}
```

The shared resolver follows active acquisitions, including fixed/required and learned optional skills, through an acyclic graph. A granted target fills no optional choice. Overlapping parents and optional target selections retain one automatic acquisition and one training benefit. Each projected occurrence uses the highest ordinary class/selection training bonus or automatic training bonus; IQ, advancement and distinct source synergies apply normally. Projection retains grant origins. This adapter does not decide class eligibility, dice acquisition or activity simulation.

A first granted target shares its parent's recorded learned level; earlier existing target learning history remains authoritative. Explicit earlier acquisition input applies before resolving newly granted ages. The ordinary learning-history mechanism retains recorded ages after removal and reselection. At level one, as with existing skills, learning records are materialized on advancement; removing an acquisition before that checkpoint does not invent a retained history entry. Removal deactivates automatic proficiency and its bonuses when no other acquisition remains. Exact pinned definitions drive projection, upgrade preview, persistence, import and PDF output; guarded totals reject outside the exact integer range.

Vehicle Armorer is the accepted source witness:30% +5% per learned level, Basic Mechanics at+20%, Automotive Mechanics+10% once. Usual class availability, military driving, armor/speed tradeoffs, weapon hookups, facilities and legal restrictions remain descriptive. Secondary Mechanical permits only the existing Basic/Automotive identities; exceptions are retained with guidance. This does not certify robot/bionic construction or remaining class/race coverage. Synthetic chained and class-overlap fixtures validate the seam rather than additional source content.
