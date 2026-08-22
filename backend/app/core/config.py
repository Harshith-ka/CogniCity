from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ai-twin-city"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+asyncpg://city_user:city_pass@localhost:5432/ai_twin_city"

    redis_url: str = "redis://localhost:6379/0"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j_pass"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1"
    ollama_embed_model: str = "nomic-embed-text"

    embedding_dim: int = 0

    simulation_tick_seconds: float = 1.0
    simulation_time_scale: int = 60
    initial_population: int = 100
    max_population: int = 10000

    random_seed: int = 42

    # Admin portal auth (Phase 1 of the multi-tenant platform plan). jwt_secret_key
    # MUST be overridden via env var outside local dev — the default here is only safe
    # because this is a single local deployment with no real tenants yet.
    jwt_secret_key: str = "dev-only-insecure-secret-change-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h session
    initial_admin_email: str = "admin@cognicity.local"
    initial_admin_password: str = "changeme123"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
