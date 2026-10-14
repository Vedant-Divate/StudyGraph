"""Offline question-bank builder, threaded x4. Resumable. Target: 30 generated."""

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "services", "api"))
os.environ["LLM_TIMEOUT_S"] = "120"
os.environ["LLM_PROVIDER"] = "nim"
os.environ["EMBED_BACKEND"] = "nim"

path = os.path.join(REPO, ".env.local")
with open(path, encoding="utf-8") as handle:
    for line in handle:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

from sqlalchemy import select  # noqa: E402

from app.assess import dedup, generate, verify  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.kb.embeddings import embed_texts  # noqa: E402
from app.llm.factory import get_llm  # noqa: E402

settings = get_settings()
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 30
lock = threading.Lock()
generated = discarded = 0
t0 = time.monotonic()


def snapshot():
    with session_scope() as session:
        course = session.scalars(select(models.Course).limit(1)).first()
        concepts = session.scalars(select(models.Concept)).all()
        rows = [
            (str(c.id), c.name, c.summary or "", float(c.importance or 0)) for c in concepts
        ]
        misc = session.scalars(select(models.Misconception)).all()
        miscmap: dict[str, list[str]] = {}
        for m in misc:
            miscmap.setdefault(str(m.concept_id), []).append(m.label)
        hashes = {r[0] for r in session.execute(select(models.Question.stem_hash)).all()}
    assert course is not None
    return course.id, rows, miscmap, hashes


course_id, concept_rows, miscmap, bank_hashes = snapshot()
print(f"concepts={len(concept_rows)} banked={len(bank_hashes)}", flush=True)


def build_one(cid: str, name: str, summary: str, mislabels: list[str], difficulty: str) -> None:
    global generated, discarded
    llm = get_llm(settings)
    with session_scope() as session:
        n_have = len(
            session.execute(
                select(models.Question.id).where(models.Question.concept_id == cid)
            ).all()
        )
        if n_have >= 2:
            return
        tags = session.execute(
            select(models.UnitConcept.unit_id).where(models.UnitConcept.concept_id == cid).limit(4)
        ).all()
        units = [session.get(models.ContentUnit, t[0]) for t in tags]
        units = [u for u in units if u is not None]
    if not units:
        return
    unit_context = "\n".join(f"[{u.id}] {u.text[:700]}" for u in units)[:3000]
    source_ids = [str(u.id) for u in units]
    question = None
    verification: dict = {"ok": False}
    for _ in range(3):
        try:
            q = generate.generate_mcq(
                concept_name=name, concept_summary=summary, unit_context=unit_context,
                misconceptions=mislabels, difficulty=difficulty,
                complete=llm.complete_structured, model=settings.llm_model,
            )
            v = verify.verify_mcq(
                q, unit_context, mislabels,
                solve=llm.complete_structured, model=settings.verifier_model,
            )
        except Exception as exc:  # noqa: BLE001
            v = {"ok": False, "error": type(exc).__name__}
        if v.get("ok"):
            question, verification = q, v
            break
        verification = v
    with lock:
        if generated >= TARGET:
            return
    if question is None:
        with lock:
            discarded += 1
        print(f"DISCARD {name} [{difficulty}]", flush=True)
        return
    stem_vec = embed_texts([question["stem"]], settings=settings)[0]
    with session_scope() as session:
        vecs = [list(r[0]) for r in session.execute(select(models.Question.embedding)).all() if r[0]]
        hashes = {r[0] for r in session.execute(select(models.Question.stem_hash)).all()}
        if dedup.is_duplicate(question["stem"], stem_vec, hashes, vecs, threshold=0.88):
            with lock:
                discarded += 1
            print(f"DISCARD dup {name}", flush=True)
            return
        options = []
        for i, opt in enumerate(question["options"][:4]):
            mid = None
            if not opt.get("is_correct") and opt.get("misconception"):
                hit = session.execute(
                    select(models.Misconception.id).where(
                        models.Misconception.concept_id == cid,
                        models.Misconception.label.ilike(f"%{opt['misconception'][:30]}%"),
                    )
                ).first()
                mid = str(hit[0]) if hit else None
            options.append({
                "key": "ABCD"[i], "text": opt.get("text", ""),
                "is_correct": bool(opt.get("is_correct")),
                "misconception_id": mid, "why_wrong": opt.get("why_wrong"),
            })
        session.add(models.Question(
            course_id=course_id, type="mcq", stem=question["stem"],
            options_json={"options": options},
            answer_key_json={"key": next(o["key"] for o in options if o["is_correct"])},
            explanation=question.get("explanation", ""), concept_id=cid,
            difficulty=question.get("difficulty", difficulty),
            source_unit_ids_json=source_ids, stem_hash=generate.stem_hash(question["stem"]),
            embedding=stem_vec, verification_json=verification,
        ))
        session.commit()
    with lock:
        generated += 1
        print(f"OK {name} [{difficulty}] total={generated} {time.monotonic() - t0:.0f}s", flush=True)


tasks = []
for cid, name, summary, _imp in concept_rows:
    for difficulty in ("medium", "easy"):
        tasks.append((cid, name, summary, miscmap.get(cid, []), difficulty))

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(build_one, *t) for t in tasks]
    for f in futures:
        try:
            f.result()
        except Exception as exc:  # noqa: BLE001
            print("TASK ERROR", type(exc).__name__, flush=True)
        if generated >= TARGET:
            break

print(f"BANK DONE generated={generated} discarded={discarded} {time.monotonic() - t0:.0f}s")
