"""
Configuration management for the backend application.
Loads environment variables and provides centralized config access.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    # AuraDB instances often use the instance ID as the database name, not "neo4j"
    neo4j_database: str = "neo4j"
    
    # Google Gemini Configuration (chat / inference)
    gemini_api_key: str
    
    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # LLM Configuration (chat / inference still uses Google Gemini)
    gemini_model: str = "gemini-3.1-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 2048

    # Embedding Configuration
    # Vector embeddings run locally via a downloaded IBM Granite model
    # (sentence-transformers). No embedding API key is required.
    # https://huggingface.co/collections/ibm-granite/granite-embedding
    embedding_model: str = "ibm-granite/granite-embedding-30m-english"
    embedding_device: str = "cpu"
    embedding_normalize: bool = True

    # Hybrid retrieval
    vector_top_k: int = 5
    graph_expansion_limit: int = 5
    
    # Debate Configuration
    debate_rounds: int = 3
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()

# Made with Bob
