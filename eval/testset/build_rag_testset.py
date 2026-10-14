"""Build eval/testset/rag.jsonl from read-only lecture artifacts.

Read-only: parses data/demo-course/*.srt with the app's own SRT parser and
recomputes the deterministic stable IDs used by
scripts/store_cached_artifacts.py (uuid5 under the same namespace), so every
gold_location unit_id/source_id is identical to the row already in the
database. No DB connection, no writes, no network, no LLM.

Each item declares (lecture, window_index, keyword guards); the builder
asserts every guard keyword appears in the referenced window text, so a
drifted transcript fails loudly instead of silently mis-grounding a question.

Run from services/api so the app venv is used:
    uv run --frozen python ../../eval/testset/build_rag_testset.py
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "api"))

from app.ingestion.video import merge_windows, parse_srt  # noqa: E402

# Same namespace + ID scheme as scripts/store_cached_artifacts.py.
NAMESPACE = uuid.UUID("a4301776-1a6a-49ec-b265-27717d3c7634")
COURSE_ID = uuid.uuid5(NAMESPACE, "mit-ocw-6.041sc-fall-2013")


def source_id(lecture: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"source:lecture-{lecture:02d}")


def transcript_unit_id(lecture: int, index: int, start: float, end: float) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"transcript:{lecture}:{index}:{start:.3f}:{end:.3f}")


SOURCE_FILENAMES = {1: "MIT 6.041SC Lecture 1", 2: "MIT 6.041SC Lecture 2"}

WINDOWS: dict[int, list[tuple[float, float, str]]] = {}
for _lec in (1, 2):
    _segs = parse_srt(str(REPO / "data" / "demo-course" / f"lec{_lec:02d}.srt"))
    WINDOWS[_lec] = merge_windows(_segs)
assert len(WINDOWS[1]) == 90, f"expected 90 L01 windows, got {len(WINDOWS[1])}"
assert len(WINDOWS[2]) == 88, f"expected 88 L02 windows, got {len(WINDOWS[2])}"


def loc(lecture: int, index: int) -> dict[str, Any]:
    """Gold location for transcript window `index` of `lecture` (guard-checked by caller)."""
    start, end, _text = WINDOWS[lecture][index]
    return {
        "source_id": str(source_id(lecture)),
        "source": SOURCE_FILENAMES[lecture],
        "unit_id": str(transcript_unit_id(lecture, index, start, end)),
        "t_start_s": round(start, 3),
        "t_end_s": round(end, 3),
    }


def check(lecture: int, index: int, *keywords: str) -> dict[str, Any]:
    """Assert guard keywords are present, then return the gold location."""
    text = WINDOWS[lecture][index][2].lower()
    for kw in keywords:
        assert kw.lower() in text, f"L{lecture}W{index:02d} missing guard {kw!r}"
    return loc(lecture, index)


# (id, type, question, gold_answer, [(lec, idx, [guards])], must_refuse, notes)
ITEMS: list[tuple[str, str, str, str, list[tuple[int, int, list[str]]], bool, str]] = [
    (
        "rag-01",
        "in_scope",
        "What are the three axioms of probability stated in Lecture 1?",
        "Non-negativity P(A) >= 0; normalization P(omega) = 1; finite additivity: "
        "P(A union B) = P(A) + P(B) for disjoint A, B.",
        [(1, 44, ["non-negative"]), (1, 45, ["entire sample space", "equal to one"]),
         (1, 48, ["third axiom", "no common elements"]),
         (1, 49, ["sum of the individual", "cream cheese"])],
        False,
        "Core Lecture 1 theory; asked in the route probe S1.",
    ),
    (
        "rag-02",
        "in_scope",
        "What two requirements must a sample space satisfy, and what do they mean?",
        "Mutually exclusive (exactly one outcome occurs) and collectively exhaustive "
        "(no possible outcome left out).",
        [(1, 22, ["mutually exclusive", "collectively exhaustive"]),
         (1, 23, ["Collectively exhaustive means", "Mutually exclusive means"])],
        False,
        "Lecture 1 sample-space setup.",
    ),
    (
        "rag-03",
        "in_scope",
        "In the coin-flip example with rain as a possible detail, which sample space "
        "does the lecturer keep, and what general modelling point does he draw from it?",
        "He keeps {heads, tails}, dropping the rain detail as irrelevant, to show that "
        "setting up a sample space involves art/judgment about which details to keep.",
        [(1, 24, ["tails and it's raining"]), (1, 25, ["superstitious", "rain"]),
         (1, 26, ["zillions of details", "irrelevant"]),
         (1, 27, ["element of art", "judgment", "outside your model"])],
        False,
        "Lecture 1 modelling-judgment example.",
    ),
    (
        "rag-04",
        "in_scope",
        "For the experiment of rolling a four-sided die twice, what is the sample space "
        "and how many outcomes does it have? Does outcome order matter?",
        "16 ordered pairs (i, j); (2,3) and (3,2) are distinct outcomes.",
        [(1, 28, ["four faces", "two rolls"]), (1, 30, ["distinguished", "backgammon"]),
         (1, 31, ["16 elements", "finite set"])],
        False,
        "Lecture 1 two-roll die example.",
    ),
    (
        "rag-05",
        "in_scope",
        "In the two-roll die example, what distinction does the lecturer draw between "
        "a 'result' and an 'outcome'?",
        "A result is what happens at one stage (e.g. 2 on the first roll); the outcome "
        "is the overall pair (e.g. 2,3) at the end of the whole experiment.",
        [(1, 35, ['reserve the word "outcome"', "overall outcome"])],
        False,
        "Lecture 1 terminology; exact-quote guard.",
    ),
    (
        "rag-06",
        "in_scope",
        "Describe the darts example and explain why its sample space is infinite.",
        "Darts always land in a square target; an outcome is a point (x,y) with real "
        "coordinates in [0,1], so there are infinitely many outcomes.",
        [(1, 36, ["playing darts", "inside the square"]),
         (1, 37, ["pair of numbers", "infinitely many points"])],
        False,
        "Lecture 1 infinite-sample-space example.",
    ),
    (
        "rag-07",
        "in_scope",
        "Why does the lecturer assign probabilities to subsets (events) rather than to "
        "individual outcomes?",
        "In continuous models an individual point (e.g. one dart hit to infinite "
        "precision) has probability zero, so pointwise assignment says nothing; "
        "subsets carry the information.",
        [(1, 39, ["exactly this point", "zero"]), (1, 40, ["subsets of the sample space"])],
        False,
        "Lecture 1 events-vs-outcomes motivation.",
    ),
    (
        "rag-08",
        "in_scope",
        "What intuition does the lecturer give for the additivity axiom using cream cheese?",
        "Total probability 1 is a pound of cream cheese spread over omega; P(A) is how "
        "much sits on A, so disjoint A, B give P(A union B) = P(A) + P(B), like mass.",
        [(1, 49, ["cream cheese", "sum of the individual"]),
         (1, 50, ["behave like mass"])],
        False,
        "Lecture 1 additivity intuition.",
    ),
    (
        "rag-09",
        "in_scope",
        "Is 'probabilities are at most one' an axiom? How is it obtained?",
        "No: it is derived. omega = A union A^c (disjoint), so 1 = P(A) + P(A^c) and "
        "P(A) = 1 - P(A^c) <= 1 by non-negativity. Uses all three axioms.",
        [(1, 52, ["laconic", "less than or equal to one"]), (1, 54, ["complement", "disjoint"]),
         (1, 55, ["less than or equal to one"])],
        False,
        "Lecture 1 P(A) <= 1 derivation.",
    ),
    (
        "rag-10",
        "in_scope",
        "How does the lecturer extend additivity from two disjoint sets to three?",
        "Write A union B union C as (A union B) union C; A union B is disjoint from C, "
        "so apply the two-set axiom twice to get P(A)+P(B)+P(C). Repeats to any finite n.",
        [(1, 57, ["union of three sets", "sum of the three"]),
         (1, 58, ["disjoint from C", "additivity axiom"]),
         (1, 59, ["hundred disjoint", "finite number"])],
        False,
        "Lecture 1 finite-additivity extension.",
    ),
    (
        "rag-11",
        "in_scope",
        "State the discrete uniform law and use it for P(first roll equals 1) with the "
        "two-roll four-sided die.",
        "If N outcomes are equally likely, P(A) = n/N. {x=1} has 4 of 16 outcomes, "
        "so 4/16.",
        [(1, 69, ["set of all outcomes", "x is equal to one"]),
         (1, 70, ["four outcomes", "4/16"]),
         (1, 74, ["discrete uniform law", "equally likely"])],
        False,
        "Lecture 1 discrete uniform law + worked value.",
    ),
    (
        "rag-12",
        "in_scope",
        "What is the probability that the minimum of the two rolls equals 2, and how "
        "is it counted?",
        "5/16: both equal 2 (1 way), x=2<y (2 ways), y=2<x (2 ways); 5 outcomes of 16.",
        [(1, 72, ["minimum of the two rolls", "several ways"]),
         (1, 73, ["five possible outcomes", "5/16"])],
        False,
        "Lecture 1 minimum-equals-2 worked example.",
    ),
    (
        "rag-13",
        "in_scope",
        "In the darts (area) model, what is P(x + y <= 1/2) and how is it computed?",
        "1/8: the event is a triangle with intercepts 1/2, 1/2; area = "
        "1/2*1/2*1/2 = 1/8, and probability equals area.",
        [(1, 79, ["below this line", "x plus y equals to 1/2"]),
         (1, 80, ["intercepts", "area of this triangle", "1/8"])],
        False,
        "Lecture 1 continuous-area worked example.",
    ),
    (
        "rag-14",
        "in_scope",
        "Why is finite additivity not enough for the coin-flip waiting-time example, "
        "and what fixes it? What is P(the wait is even)?",
        "P(wait=n) = 2^-n over infinitely many integers needs summing infinitely many "
        "disjoint probabilities; the countable-additivity axiom licenses it. P(even) = 1/3 "
        "via the geometric series.",
        [(1, 83, ["first time", "all possible integers"]),
         (1, 84, ["two to the minus n", "even number"]),
         (1, 85, ["geometric series", "1/3"]),
         (1, 87, ["countable additivity axiom"])],
        False,
        "Lecture 1 countable-additivity motivation + value.",
    ),
    (
        "rag-15",
        "in_scope",
        "State the definition of conditional probability P(A|B) and the caveat about P(B).",
        "P(A|B) = P(A intersection B) / P(B); undefined when P(B) = 0.",
        [(2, 28, ["into a definition", "fraction of that probability"]),
         (2, 29, ["2/6", "2/3", "zero probability", "not defined"])],
        False,
        "Lecture 2 conditional-probability definition.",
    ),
    (
        "rag-16",
        "multi_hop",
        "Combine both lectures: for the two-roll die, the minimum equals 2 with "
        "probability 5/16. Given that event, what is P(maximum equals 2), and why is "
        "there a shortcut?",
        "1/5. Conditioning on the 5-element event: the five red outcomes were equally "
        "likely and stay equally likely, so the one outcome with max 2 has probability "
        "1/5 (formally (1/16)/(5/16)).",
        [(1, 73, ["five possible outcomes", "5/16"]),
         (2, 39, ["only one point", "1/5"]),
         (2, 40, ["remain equally likely", "five red elements"]),
         (2, 41, ["shortcut", "uniform distribution"])],
        False,
        "Multi-hop L1 (5/16) + L2 (conditional 1/5, uniformity preserved).",
    ),
    (
        "rag-17",
        "multi_hop",
        "Lecture 1 gives axioms for a probability law; Lecture 2 claims conditional "
        "probabilities 'do not taste or smell different'. What is the combined claim?",
        "Fixing the conditioning event C, the map A -> P(A|C) satisfies the same axioms "
        "(e.g. additivity over disjoint A, B) and is itself a legitimate probability law "
        "on the new universe where C occurred.",
        [(1, 49, ["sum of the individual", "cream cheese"]), (2, 33, ["new universe", "legitimate"]),
         (2, 34, ["taste or smell", "probability law"])],
        False,
        "Multi-hop L1 axioms + L2 conditional-as-law.",
    ),
    (
        "rag-18",
        "multi_hop",
        "Lecture 1 introduces countable additivity for sequences of disjoint events. "
        "Lecture 2 shows a 'proof' that 1 = 0 from the unit square. Why does the axiom "
        "not rescue that proof?",
        "Countable additivity applies only to a sequence (first, second, third, ...) of "
        "events; the unit square is uncountable and cannot be exhausted by any sequence "
        "of points, so the step writing 1 as a sum over points is invalid.",
        [(1, 89, ["arranged in order", "first event, the second"]),
         (2, 11, ["sequence of disjoint events", "sequence of sets"]),
         (2, 12, ["cover the whole unit square", "sequence of one element points"]),
         (2, 13, ["uncountable", "more elements than any sequence"]),
         (2, 14, ["does not apply", "not dealing with a sequence"])],
        False,
        "Multi-hop L1 countable additivity + L2 uncountability diagnosis.",
    ),
    (
        "rag-19",
        "multi_hop",
        "In the airplane-radar example, what are the prior, the total probability the "
        "radar registers something, and the posterior? Which general theorem does the "
        "middle step illustrate?",
        "Prior P(plane) = 0.05; total P(register) = 0.05*0.99 + 0.95*0.10 = 0.1445 "
        "(total probability theorem over the plane/no-plane partition); posterior "
        "P(plane|register) = 0.0495/0.1445 = 0.34.",
        [(2, 43, ["five percent", "95%"]), (2, 50, ["0.05 times 0.99", "0.1445"]),
         (2, 52, ["relative odds", "definition of conditional probabilities"]),
         (2, 53, ["ratio", "0.34"]), (2, 71, ["add the probabilities", "three contingencies"])],
        False,
        "Multi-hop radar numbers + total-probability theorem.",
    ),
    (
        "rag-20",
        "near_miss",
        "Derive the binomial distribution for the number of heads in n independent "
        "Bernoulli trials.",
        "REFUSE (not_covered): independence and Bernoulli/binomial trials belong to "
        "Lecture 3+ material, not the ingested Lectures 1-2.",
        [],
        True,
        "Near-miss: adjacent probability topic (independence/counting lectures), not covered.",
    ),
    (
        "rag-21",
        "near_miss",
        "A disease test has sensitivity 99%, specificity 90%, and the disease prior is "
        "5%. What is P(disease | positive)?",
        "REFUSE (not_covered): the lectures work this arithmetic only for the airplane "
        "radar; disease diagnosis is mentioned as a one-line aside and never taught.",
        [],
        True,
        "Near-miss: Lecture 2 mentions doctors as an aside (L2W57) but teaches radar only.",
    ),
    (
        "rag-22",
        "near_miss",
        "Define independent events and state the multiplication rule for independent events.",
        "REFUSE (not_covered): independence is the topic of Lecture 3, which is not ingested.",
        [],
        True,
        "Near-miss: next-lecture topic (ADR-0004 chain axioms -> Bayes -> independence).",
    ),
    (
        "rag-23",
        "near_miss",
        "How do I count permutations and combinations for discrete uniform problems "
        "with a 52-card deck?",
        "REFUSE (not_covered): Lecture 1 says counting gets complicated and defers it "
        "to a later lecture (Lecture 4); no counting methods are taught.",
        [],
        True,
        "Near-miss: explicitly deferred in-lecture (L1W76).",
    ),
    (
        "rag-24",
        "near_miss",
        "Define a continuous random variable's pdf and compute E[X] for the darts model.",
        "REFUSE (not_covered): the darts example uses area-as-probability only; pdfs and "
        "expectation are never introduced.",
        [],
        True,
        "Near-miss: adjacent continuous-probability topic, not taught.",
    ),
    (
        "rag-25",
        "unrelated",
        "How does a TLS handshake negotiate encryption keys?",
        "REFUSE (not_covered): unrelated to probability lectures.",
        [],
        True,
        "Unrelated probe O1 from the Phase 3-4-5 calibration (below threshold).",
    ),
    (
        "rag-26",
        "unrelated",
        "How does photosynthesis convert light into chemical energy?",
        "REFUSE (not_covered): unrelated to probability lectures.",
        [],
        True,
        "Unrelated probe O2 from the Phase 3-4-5 calibration (below threshold).",
    ),
    (
        "rag-27",
        "unrelated",
        "How does quicksort partition and sort an array?",
        "REFUSE (not_covered): unrelated to probability lectures.",
        [],
        True,
        "Unrelated probe O3 from the Phase 3-4-5 calibration (below threshold).",
    ),
    (
        "rag-28",
        "false_premise",
        "Why does the lecture set the probability of the entire sample space to 0?",
        "REFUSE/correct (false premise): the lecture states the opposite — P(omega) = 1 "
        "by the second axiom, since omega is certain to occur.",
        [(1, 45, ["entire sample space", "equal to one"])],
        True,
        "False-premise: directly contradicts Axiom 2; gold loc states the true axiom.",
    ),
    (
        "rag-29",
        "false_premise",
        "How does the lecture show that rain affects the outcome of the coin flip?",
        "REFUSE/correct (false premise): the lecture keeps {heads, tails} and treats "
        "rain as an irrelevant detail; it never claims rain affects the coin.",
        [(1, 25, ["superstitious", "rain"]), (1, 26, ["zillions of details", "irrelevant"]),
         (1, 27, ["outside your model", "element of art"])],
        True,
        "False-premise: lecture says the opposite (modeler's choice to neglect rain).",
    ),
    (
        "rag-30",
        "false_premise",
        "Explain the lecture's proof that 1 = 0 using the unit square.",
        "REFUSE/correct (false premise): the 1 = 0 derivation is presented as a fallacy "
        "with an explicit mistake (applying countable additivity to an uncountable union), "
        "not as a valid proof.",
        [(2, 10, ["proved that one is equal to zero", "mistake"]),
         (2, 14, ["does not apply", "incorrect step"])],
        True,
        "False-premise: material marks the argument a mistake; gold locs pinpoint that.",
    ),
]


def build() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = [
        {
            "header": True,
            "status": "LLM-DRAFTED — REQUIRES HUMAN REVIEW. No item may be used for "
            "reporting until a team member has checked its question, gold answer and "
            "gold locations and recorded the review in docs/review/testset-check.md.",
            "course": "MIT OCW 6.041SC (Lectures 1-2 ingested)",
            "course_id": str(COURSE_ID),
            "provenance": "Questions drafted by an AI agent from read-only "
            "data/demo-course/lec01.srt + lec02.srt via the app SRT parser; "
            "gold unit_ids/source_ids recomputed with the same deterministic uuid5 "
            "scheme as scripts/store_cached_artifacts.py, so they equal the DB rows. "
            "DB was unreachable in this sandbox (no Docker daemon); locations were "
            "NOT read from a live DB connection. Guard keywords asserted per item.",
            "composition": {
                "in_scope": 15,
                "multi_hop": 4,
                "near_miss": 5,
                "unrelated": 3,
                "false_premise": 3,
                "total": 30,
            },
            "licence": "Source material MIT OCW CC BY-NC-SA 4.0; see data/demo-course/ATTRIBUTIONS.md.",
        }
    ]
    for item_id, qtype, question, gold_answer, refs, must_refuse, notes in ITEMS:
        gold_locations = [check(lec, idx, *guards) for lec, idx, guards in refs]
        records.append(
            {
                "id": item_id,
                "type": qtype,
                "question": question,
                "gold_answer": gold_answer,
                "gold_locations": gold_locations,
                "must_refuse": must_refuse,
                "notes": notes,
            }
        )
    counts: dict[str, int] = {}
    for rec in records[1:]:
        counts[rec["type"]] = counts.get(rec["type"], 0) + 1
    assert counts == {"in_scope": 15, "multi_hop": 4, "near_miss": 5,
                      "unrelated": 3, "false_premise": 3}, counts
    assert sum(1 for r in records[1:] if r["must_refuse"]) == 11
    return records


def main() -> None:
    records = build()
    out = REPO / "eval" / "testset" / "rag.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {len(records) - 1} items + header -> {out}")


if __name__ == "__main__":
    main()
