.PHONY: verify up down ingest-demo eval

verify:
	cd services/api && uv run --frozen ruff check . && uv run --frozen ruff format --check .
	cd services/api && uv run --frozen mypy app
	cd services/api && LLM_PROVIDER=mock ASR_BACKEND=mock EMBED_BACKEND=hash uv run --frozen pytest -q
	cd apps/web && pnpm typecheck && pnpm lint && pnpm test && pnpm build
	./scripts/check_no_secrets.sh

up:
	docker compose up --build

down:
	docker compose down

ingest-demo:
	@echo "ingest-demo: placeholder (Phase 9 wires live ingestion)."
	@echo "Download the demo course first: bash scripts/fetch_demo_course.sh"

eval:
	@echo "eval: placeholder (Phase 8 wires the RAGAS runner)."
	LLM_PROVIDER=mock ASR_BACKEND=mock EMBED_BACKEND=hash cd services/api && uv run --frozen pytest -q
