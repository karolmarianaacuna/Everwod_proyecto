# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    
    db_name: str = "everwod_db"
    db_user: str = "postgres"
    db_password: str = "1234"
    db_host: str = "localhost"
    db_port: int = 5432

    
    faq_embedding_model: str = "intfloat/multilingual-e5-base"
    min_embedding_words: int = 2
    

    #Thresholds
    faq_similarity_very_similar :float = 0.72
    faq_similarity_related :float = 0.58
    faq_similarity_medium :float = 0.45

    faq_llm_model: str = "qwen2.5:7b"

    
    min_text_length: int = 5

   
    batch_size: int = 32
    embedding_batch_size: int = 64
    enable_cache: bool = True
    cache_ttl_hours: int = 24




# Singleton
settings = Settings()