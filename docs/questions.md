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

**RESOLVED (same source).** Rules tab: "Team size: one to four members, including
solo participation", "Inter-college teams are permitted", "One team can submit in
only one track, and an individual may only be a member of one submitting team".
Overview: "Ages 14+ only", "Students only", "Companies/professional organizations
excluded". Registration status of our team: **UNRESOLVED — human must confirm they
registered / joined (solo or team) on Devpost.**

## A-3 — Required demo-video host and length

**UNRESOLVED — need human to paste Rules tab text (or the problem-statement doc).**
The overview says "Submisson Requirements will be shared with problem statements"
and the problem statements live in a Google Drive doc we did not open. Default
applied: public YouTube video, 3–10 minutes.

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

**UNRESOLVED — need human to paste Rules tab text.** Nothing about third-party or
open-licensed material was found on the fetched pages. Default: demo uses only openly
licensed material (MIT OCW CC BY-NC-SA 4.0 + OpenStax CC BY-NC-SA 4.0) with full
attribution in data/demo-course/ATTRIBUTIONS.md.

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

**UNRESOLVED — waiting on human.** Human will upload screenshots of available models,
then share base URL + API key. ADR-0005 records placeholders. No live API calls made.

## A-9 — Hindi support

Out of scope for MVP per PROJECT.md (F-24 is P2). No question.
