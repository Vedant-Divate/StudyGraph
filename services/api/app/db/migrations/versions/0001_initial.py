"""Initial schema per PROJECT.md Section 7.2."""

from typing import Any

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

EMBED_DIM = 2048


def _id() -> sa.Column[Any]:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _created() -> sa.Column[Any]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "courses",
        _id(),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("is_demo", sa.Boolean, server_default="false"),
        _created(),
    )
    op.create_table(
        "sources",
        _id(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("duration_s", sa.Float, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("quality_json", sa.JSON, nullable=True),
        sa.Column("license_note", sa.Text, nullable=True),
        _created(),
    )
    op.create_table(
        "content_units",
        _id(),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("figure_description", sa.Text, nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("slide", sa.Integer, nullable=True),
        sa.Column("t_start_s", sa.Float, nullable=True),
        sa.Column("t_end_s", sa.Float, nullable=True),
        sa.Column("image_path", sa.Text, nullable=True),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("token_count", sa.Integer, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=True),
        _created(),
    )
    op.create_index("ix_content_units_source", "content_units", ["source_id"])
    op.create_table(
        "concepts",
        _id(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text, server_default=""),
        sa.Column("importance", sa.Float, server_default="0"),
        _created(),
    )
    op.create_index("ix_concepts_course", "concepts", ["course_id"])
    op.create_table(
        "concept_edges",
        _id(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prerequisite_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("evidence_json", sa.JSON, nullable=True),
    )
    op.create_table(
        "unit_concepts",
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float, server_default="0"),
        sa.PrimaryKeyConstraint("unit_id", "concept_id"),
    )
    op.create_table(
        "misconceptions",
        _id(),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("evidence_json", sa.JSON, nullable=True),
    )
    op.create_table(
        "students",
        _id(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        _created(),
    )
    op.create_table(
        "mastery_states",
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("p_mastery", sa.Float, server_default="0.3"),
        sa.Column("stability_days", sa.Float, server_default="3"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("n_correct", sa.Integer, server_default="0"),
        sa.Column("n_incorrect", sa.Integer, server_default="0"),
        sa.PrimaryKeyConstraint("student_id", "concept_id"),
    )
    op.create_table(
        "questions",
        _id(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("stem", sa.Text, nullable=False),
        sa.Column("options_json", sa.JSON, nullable=True),
        sa.Column("answer_key_json", sa.JSON, nullable=False),
        sa.Column("rubric_json", sa.JSON, nullable=True),
        sa.Column("solution_expression", sa.Text, nullable=True),
        sa.Column("explanation", sa.Text, server_default=""),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("source_unit_ids_json", sa.JSON, server_default="[]"),
        sa.Column("requires_figure", sa.Boolean, server_default="false"),
        sa.Column("figure_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stem_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("verification_json", sa.JSON, nullable=True),
        _created(),
    )
    op.create_index("ix_questions_course", "questions", ["course_id"])
    op.create_index("ix_questions_stem_hash", "questions", ["stem_hash"])
    op.create_table(
        "assessments",
        _id(),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("scope_json", sa.JSON, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="open"),
        _created(),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "assessment_items",
        _id(),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("selection_reason", sa.Text, server_default=""),
        sa.Column("mastery_before", sa.Float, nullable=True),
    )
    op.create_table(
        "responses",
        _id(),
        sa.Column("assessment_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_json", sa.JSON, server_default="{}"),
        sa.Column("score", sa.Float, server_default="0"),
        sa.Column("is_correct", sa.Boolean, server_default="false"),
        sa.Column("chosen_misconception_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feedback_json", sa.JSON, nullable=True),
        sa.Column("time_ms", sa.BigInteger, server_default="0"),
        _created(),
    )
    op.create_table(
        "chat_sessions",
        _id(),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        _created(),
    )
    op.create_table(
        "chat_messages",
        _id(),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("segments_json", sa.JSON, nullable=True),
        sa.Column("labels", sa.JSON, server_default="[]"),
        sa.Column("retrieved_unit_ids", sa.JSON, server_default="[]"),
        sa.Column("verifier_json", sa.JSON, nullable=True),
        sa.Column("latency_ms", sa.BigInteger, server_default="0"),
        _created(),
    )
    op.create_index("ix_chat_messages_session", "chat_messages", ["session_id"])
    op.create_table(
        "chat_signals",
        _id(),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        _created(),
    )
    op.create_table(
        "jobs",
        _id(),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("payload_json", sa.JSON, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("progress", sa.Float, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("attempts", sa.Integer, server_default="0"),
        _created(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "eval_runs",
        _id(),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("config_json", sa.JSON, server_default="{}"),
        sa.Column("results_json", sa.JSON, nullable=True),
        _created(),
    )


def downgrade() -> None:
    for table in (
        "eval_runs",
        "jobs",
        "chat_signals",
        "chat_messages",
        "chat_sessions",
        "responses",
        "assessment_items",
        "assessments",
        "questions",
        "mastery_states",
        "students",
        "misconceptions",
        "unit_concepts",
        "concept_edges",
        "concepts",
        "content_units",
        "sources",
        "courses",
    ):
        op.drop_table(table)
