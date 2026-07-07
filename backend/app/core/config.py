from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Employee Knowledge Assistant"
    app_env: str = "local"
    app_debug: bool = True

    app_upload_dir: str = "storage/uploads"
    app_quarantine_dir: str = "storage/quarantine"

    database_url: str

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "employee_knowledge"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    ocr_enabled: bool = True
    ocr_dpi: int = 200
    ocr_min_text_chars_per_page: int = 50
    ocr_language: str = "eng"
    tesseract_cmd: str | None = None

    cors_allowed_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    login_rate_limit_requests: int = 10
    login_rate_limit_window_seconds: int = 60

    max_request_body_bytes: int = 10 * 1024 * 1024
    max_upload_file_bytes: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()