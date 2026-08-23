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
    # because this is a single local deployment with no real tenants yet. See
    # _validate_production_config() below, which refuses to boot with these defaults
    # once APP_ENV isn't "development".
    jwt_secret_key: str = "dev-only-insecure-secret-change-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h session
    initial_admin_email: str = "admin@cognicity.local"
    initial_admin_password: str = "changeme123"

    # Comma-separated allowed browser origins for CORS. "*" is only accepted while
    # app_env == "development" — see _validate_production_config(). Real browser
    # clients here are the Expo web build and any future standalone web frontend;
    # server-side callers (Streamlit, native mobile) aren't subject to CORS at all.
    cors_allowed_origins: str = "*"

    # Requests per minute per client IP for unauthenticated auth endpoints
    # (login/signup) — the only endpoints cheap enough for credential-stuffing /
    # signup-spam to matter before a real WAF is in front of this.
    auth_rate_limit_per_minute: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def _validate_production_config() -> None:
    """Fail loud at startup rather than silently serving insecure defaults.

    Local dev (APP_ENV=development, the .env default) is unaffected. Anything else —
    staging, production, a forgotten APP_ENV in a real deployment — must have every
    one of these overridden or the process refuses to start.
    """
    if settings.app_env == "development":
        return

    problems = []
    if settings.jwt_secret_key == "dev-only-insecure-secret-change-before-any-real-deployment":
        problems.append("JWT_SECRET_KEY is still the insecure default — set a real random secret.")
    if settings.initial_admin_password == "changeme123":
        problems.append("INITIAL_ADMIN_PASSWORD is still the seeded default — set a real password.")
    if settings.cors_allowed_origins.strip() in ("", "*"):
        problems.append("CORS_ALLOWED_ORIGINS must be a specific comma-separated origin list outside development.")
    if settings.debug:
        problems.append("DEBUG must be false outside development.")

    if problems:
        raise RuntimeError(
            f"Refusing to start with APP_ENV={settings.app_env!r} and insecure config:\n  - "
            + "\n  - ".join(problems)
        )


_validate_production_config()
