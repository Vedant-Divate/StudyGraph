# ADR-0004: Demo course — MIT OCW 6.041SC + OpenStax Introductory Statistics 2e

- Status: accepted
- Date: 2026-10-12
- Phase: 0

## Context

PROJECT.md 5.2 fixes the demo course; Phase 0 verifies availability, licences,
lecture selection, slides-vs-notes, video downloadability and textbook fit.

## Decision

**Course:** MIT OpenCourseWare 6.041SC, *Probabilistic Systems Analysis and Applied
Probability*, Fall 2013, Prof. John Tsitsiklis. Licence **CC BY-NC-SA 4.0**
(confirmed via the footer "Creative Commons License" link on the course, Unit I
and Lecture 1 pages, fetched 2026-10-12).

**Lectures (Unit I chain, slides + video):**

| # | Lecture | Video | Slides PDF | Course-textbook reading |
|---|---------|-------|------------|-------------------------|
| 1 | Probability Models and Axioms | 00:51:11 | `..._MIT6_041SCF13_L01.pdf` | §§1.1–1.2 |
| 2 | Conditioning and Bayes' Rule | 00:51:11 | `..._MIT6_041SCF13_L02.pdf` | §§1.3–1.4 |
| 3 | Independence | 00:46:30 | `..._MIT6_041SCF13_L03.pdf` | §1.5 |
| 4 | Counting | 00:51:35 | `..._MIT6_041SCF13_L04.pdf` | §1.6 |

Total video ≈ 3h20m (slightly over the "about 3 hours" guidance; kept because it is
exactly the chain the spec asks for: axioms → Bayes → independence → counting).
Lecture PDFs are **slides** (each lecture page says "Slides (PDF)"); both slides and
notes go through the same PDF page pipeline, so either is fine.

**Video download:** each lecture page links a `lecture-N-video` resource page with
OCW's own "Download video" (+ transcript) option. The files are hosted on
`archive.org/download/MIT6.041F10/MIT6_041F11_lec0N_300k.mp4` — OCW's own upload,
not YouTube scraping. Direct URLs resolved 2026-10-12 and baked into
`scripts/fetch_demo_course.sh` with checksum verification.

**Textbook:** OpenStax *Introductory Statistics 2e*
(https://openstax.org/details/books/introductory-statistics-2e).
Licence per the OpenStax CMS API **and** the PDF copyright page (p.3, extracted
2026-10-12): **CC BY-NC-SA 4.0** — this corrects PROJECT.md 5.2's "expected CC BY
4.0". No action needed (both demo sources share the same licence; non-commercial
hackathon demo with attribution complies). Chapters from the PDF bookmarks (847 pp):
Ch 3 *Probability Topics* pairs with Lectures 1–4; Ch 4 *Discrete Random Variables*
pairs with Lectures 5+ (kept for Phase 2+; Phase 0 fetches the whole PDF).
The textbook is a good match: no alternative proposed.

**Attribution:** `data/demo-course/ATTRIBUTIONS.md`. Media files are never committed;
`scripts/fetch_demo_course.sh` downloads them locally with sha256 verification.

## Consequences

Ingestion (Phases 2–3) targets these 9 files (4 videos, 4 slide PDFs, 1 textbook PDF).
Licence notices (BY-NC-SA, non-commercial, share-alike) must appear wherever the
material is redistributed, including the demo deployment.
