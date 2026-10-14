# Test-set human review — `eval/testset/rag.jsonl`

Status: **LLM-DRAFTED, NOT YET REVIEWED.** Per PROJECT.md 11.1, no item may be
used for reporting until a team member checks its question, gold answer and
gold locations against the lecture material, then edits the file header's
`status` field to record the review (name + date).

How the file was built (see `eval/testset/build_rag_testset.py`):

- Questions drafted by an AI agent from read-only `data/demo-course/lec01.srt`
  + `lec02.srt` via the app's own SRT parser.
- Gold `unit_id`/`source_id` values recomputed with the same deterministic
  uuid5 scheme as `scripts/store_cached_artifacts.py`, so they equal the DB
  rows. The live DB was unreachable in the build sandbox (no Docker daemon);
  locations were NOT read from a DB connection.
- Every gold location carries guard keywords asserted present in the window
  text at build time (build fails otherwise). 10 items below are listed for
  manual verification; please check all 30 before signing off.

## Composition

15 in-scope, 4 multi-hop, 5 near-miss, 3 unrelated, 3 false-premise.
`must_refuse=true` on all 11 off-material items (near-miss + unrelated +
false-premise).

## 10 items to verify

### 1. rag-01 (in_scope) — three axioms of probability

Q: "What are the three axioms of probability stated in Lecture 1?"
Gold: non-negativity; P(omega)=1; finite additivity for disjoint A, B.
Locations: Lecture 1 windows 1477.08–1508.11 (W44), 1508.11–1541.52 (W45),
1651.14–1685.34 (W49).
Check: wording of each axiom against the audio/slides; timestamps in range.

### 2. rag-05 (in_scope) — result vs outcome terminology

Q: distinction between a stage "result" and the overall "outcome".
Gold: result = one stage (e.g. 2 on first roll); outcome = full pair (2,3).
Location: Lecture 1, 1160.58–1196.47 (W35).
Check: the exact-quote guard (`reserve the word "outcome"`); confirm the
example numbers match the lecture.

### 3. rag-09 (in_scope) — P(A) <= 1 is derived, not assumed

Q: "Is 'probabilities are at most one' an axiom? How is it obtained?"
Gold: derived via omega = A ∪ A^c; uses all three axioms.
Locations: Lecture 1, 1750.11–1782.58 (W52), 1816.80–1848.15 (W54),
1848.15–1880.23 (W55).
Check: derivation steps; that W52 contains the "mathematicians are laconic"
remark justifying why it is not a fourth axiom.

### 4. rag-12 (in_scope) — P(min of two rolls = 2) = 5/16

Q + counting breakdown (1 + 2 + 2 ways).
Locations: Lecture 1, 2440.49–2471.62 (W72), 2474.23–2514.24 (W73).
Check: the 5/16 value and the counting against the lecture diagram.

### 5. rag-14 (in_scope) — countable additivity + P(wait is even) = 1/3

Q: why finite additivity is not enough for the coin-waiting example.
Gold: P(wait=n) = 2^-n over infinite integers; countable-additivity axiom;
P(even) = 1/3 via geometric series.
Locations: Lecture 1, 2821.73–2856.25 (W83), 2856.25–2888.38 (W84),
2888.38–2920.84 (W85), 2953.74–2985.14 (W87).
Check: formula 2^-n, value 1/3, and that the axiom is named in W87.

### 6. rag-16 (multi_hop) — L1 5/16 + L2 conditional 1/5

Q: given min=2 (prob 5/16, Lecture 1), P(max=2 | min=2)?
Gold: 1/5; equally-likely outcomes stay equally likely under conditioning.
Locations: L1 2474.23–2514.24 (W73); L2 1385.56–1421.58 (W40),
1421.58–1457.23 (W41).
Check: cross-lecture consistency; the uniformity-preservation claim.

### 7. rag-18 (multi_hop) — why countable additivity does not save the 1=0 proof

Q connects L1 countable additivity (sequences only) to the L2 unit-square
fallacy (uncountable union).
Locations: L1 3015.34–3070.63 (W89); L2 441.74–472.62 (W11),
472.62–503.07 (W12), 503.07–535.47 (W13), 535.47–569.28 (W14).
Check: that W13 really contains the "uncountable" diagnosis; lecture-accurate
framing of sequence vs uncountable union.

### 8. rag-21 (near_miss, must_refuse) — disease-diagnosis Bayes numbers

Q asks for P(disease | positive) from sensitivity/specificity/prior.
Gold: REFUSE — lectures work this arithmetic only for the airplane radar;
doctors are a one-line aside (L2 ~1966–2003s), never taught.
Gold locations: none (empty list).
Check: agree this is adjacent-but-uncovered (not answerable from radar
windows alone without transferring domains, which the tutor must not do);
decide whether to keep `gold_locations` empty for near-miss items.

### 9. rag-28 (false_premise, must_refuse) — "P(omega) = 0"?

Q presupposes the lecture sets P(sample space) = 0.
Gold: REFUSE/correct — Axiom 2 states P(omega) = 1.
Location: Lecture 1, 1508.11–1541.52 (W45, the contradicting passage).
Check: the contradicting location indeed states = 1; false-premise framing.

### 10. rag-30 (false_premise, must_refuse) — "the lecture's proof that 1 = 0"

Q treats the unit-square 1=0 derivation as a valid proof.
Gold: REFUSE/correct — presented as a fallacy with an explicit mistake.
Locations: L2 376.83–411.03 (W10, "we just proved that one is equal to zero …
some mistake"), 503.07–535.47 (W14, axiom does not apply).
Check: W10 really frames it as a mistake; timestamps correct.

## Sign-off

Reviewer: ______________  Date: __________  Items checked: ____ / 30
After sign-off, update the `status` field of the header record in
`eval/testset/rag.jsonl` (do not delete the provenance note).
