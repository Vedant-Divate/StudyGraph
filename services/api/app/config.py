"""Application configuration. All secrets come from the environment; nothing is logged."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://studygraph:studygraph@localhost:5432/studygraph"

    # LLM / VLM (NVIDIA NIM; see ADR-0005)
    llm_provider: str = "mock"
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nim_api_key: str = ""
    llm_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    vision_model: str = "meta/muse-glimmer-30b"
    verifier_model: str = "openai/gpt-oss-20b"
    judge_model: str = "z-ai/glm-5.3"
    llm_rpm: int = 20
    llm_concurrency: int = 2
    llm_cache_dir: str = "./.cache/llm"
    llm_timeout_s: float = 25.0

    # Ingestion
    asr_backend: str = "mock"
    asr_model_size: str = "small"
    embed_backend: str = "hash"
    embed_model: str = "nvidia/nemotron-3-embed-1b"
    embed_dim: int = 2048
    max_upload_mb: int = 200
    max_figures_per_source: int = 20

    # Grounding / learner / assessment constants
    retrieval_top_k: int = 8
    question_dup_threshold: float = 0.88
    bkt_p_learn: float = 0.15
    propagation_alpha0: float = 0.4
    exploration_rate: float = 0.2


def get_settings() -> Settings:
    return Settings()
