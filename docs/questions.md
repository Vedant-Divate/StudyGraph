# Open questions and assumption log

Quoted sources for each resolution. `UNRESOLVED` items need the human to paste
the Rules tab text or confirm. Defaults applied per PROJECT.md Section 4.

## A-1 — Submission deadline and time zone

**RESOLVED (from Devpost public pages, fetched 2026-10-12).**
The manage URL (https://devpost.com/submit-to/31481-multimodal-ai-hackathon-2026/manage/submissions)
redirects logged-out visitors to the public page
https://multimodal-ai-hackathon-2026-7.devpost.com/, which states:

- "Deadline: Oct 15, 2026 @ 12:15am IST"
- "October 14 at 2:45pm EDT to deadline" (2:45pm EDT Oct 14 = 00:15 IST Oct 15; consistent)
- Rules tab dates: "Registration Begins: 22nd September 2026", "Problem Statements
  Release: 30th September 2026", "Development Period: 30th September to 14th October
  EOD", "Judging Period: 15th October to 20th October", "Final Showcase and Winner
  Announcement: 21st October 2026".

Same moment in IST: **00:15 IST, Thursday 15 October 2026**
(= 18:45 UTC Wed 14 Oct = 14:45 EDT Wed 14 Oct).

## A-2 — Team vs individual requirement and registration status

**RESOLVED (same source + human 2026-10-12).** Rules tab: "Team size: one to four members, including
solo participation", "Inter-college teams are permitted", "One team can submit in
only one track, and an individual may only be a member of one submitting team".
Overview: "Ages 14+ only", "Students only", "Companies/professional organizations
excluded". Human (2026-10-12): 4 people building one project per track; only the
best-performing project is submitted, to its track — a single submission, which
complies with "one team, one track". This repo (Track D) ships only if it wins the
internal comparison. Everyone on the submission needs a Devpost account with their
real full name on it, or no certificate.

## A-3 — Required demo-video host and length

**RESOLVED (Track D problem statement + Submission Guidelines, pasted by human
2026-10-12).** "Demonstration Video: A 3-10 minute youtube video" showing the working
system, upload workflow, grounded chat, assessment pipeline and architecture.
"Unlisted is fine. Private is not." "English audio or English subtitles required."
Matches the PROJECT.md default — default now confirmed, no change needed.

## A-4 — Rules on originality, build period and AI-assisted coding disclosure

**PARTIALLY RESOLVED.** Build period is explicit: "Development Period: 30th September
to 14th October EOD". AI assistance: "AI coding assistants are allowed with no
restrictions. You may use Cursor, Claude Code, Copilot, ChatGPT, v0, or any similar
tool. You must disclose it: list the AI tools you used in Built With and note in your
README which parts of the project were AI-assisted. Undisclosed use is treated as
misrepresentation." Disclosure added to README.md. No separate originality clause was
found on the fetched pages — default applied: honest commit history, disclose
AI-assisted development in README.

## Third-party / open datasets and course-material rules

**RESOLVED (Track D Technical Considerations, pasted by human 2026-10-12).**
"Teams may use any suitable course material (MIT OpenCourseWare, NPTEL, public
textbooks, self-created content); no fixed dataset is required." Our MIT OCW 6.041SC
+ OpenStax choice (both CC BY-NC-SA 4.0, attributed) complies.

## Track D requirements vs PROJECT.md (checked 2026-10-12, no spec change needed)

The Track D statement's 6 requirement blocks (multimodal KB, source grounding,
adaptive assessment, learner model, RAGAS/DeepEval/TruLens eval + simulated students,
optional map/flashcards/schedule/Hindi/audio) and the 20/15/20/15/15/15 judging
weights match PROJECT.md Sections 2.1, 8–11. Deliverables: working prototype, docs,
eval results, 3–10 min YouTube video. Submission needs 4 parts: Devpost description,
public GitHub repo + README with setup, video, team info.

## Organizer-provided resources

**RESOLVED (same source).** Problem statements:
https://drive.google.com/file/d/1sPrF1CWyJMGk8c3JOwu08_sboeaAE5xc/view
(not opened — needs human). Discord: https://discord.gg/UD8EVcdcq (post-registration).
Prizes: ₹1,00,000 pool (₹15,000 first + ₹10,000 second per track, 4 tracks).

## A-5 — Demo course

Fixed and verified in ADR-0004. OpenStax 2e licence is **CC BY-NC-SA 4.0, not
CC BY 4.0** as PROJECT.md expected — recorded in ADR-0004, no course swap needed.

## A-6/A-8 — Oracle VM limits and arm64

Confirmed in Oracle docs (fetched 2026-10-12): A1 Flex = 2 OCPU / 12 GB total;
idle instances (<20% CPU/network/memory over 7 days) may be reclaimed. Human
provisions the VM. Public URL: **pending**.

## A-7 — NIM models

**RESOLVED 2026-10-12.** Base URL `https://integrate.api.nvidia.com/v1`
(OpenAI-compatible); one key serves all models, lives in `.env.local` (gitignored).
All IDs confirmed verbatim from the human's snippets: chat
`nvidia/nemotron-3.5-lightning-30b-a3b`, vision `meta/muse-glimmer-30b`, verifier
`openai/gpt-oss-20b`, judge `z-ai/glm-5.3` (dot, not dash), embeddings
`nvidia/nemotron-3-embed-1b` (`input_type` query/passage, `float` encoding,
`truncate: END`). Rate limits unknown — start conservative. ADR-0005 accepted.
No live API calls made.

## A-9 — Hindi support

Out of scope for MVP per PROJECT.md (F-24 is P2). No question.
