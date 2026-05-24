# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    
    db_name: str
    db_user: str  
    db_password: str 
    db_host: str 
    db_port: int 

    
    faq_embedding_model: str
    min_embedding_words: int 
    

    #Thresholds
    faq_similarity_very_similar :float 
    faq_similarity_related :float 
    faq_similarity_medium :float

    faq_llm_model: str 
    min_text_length: int 

   
    batch_size: int 
    embedding_batch_size: int 
    enable_cache: bool 
    cache_ttl_hours: int 

    clustering_small_dataset_threshold: int  #Si hay menos de 20 mensajes, usa DBSCAN. Si hay 20 o más, usa HDBSCAN
    clustering_min_cluster_messages: int 

    clustering_dbscan_eps: float  #Este controla qué tan cerca deben estar los mensajes.
    clustering_dbscan_min_samples: int 

    clustering_hdbscan_min_cluster_size: int #grupo minimo de mensajes
    clustering_hdbscan_min_samples: int 
    clustering_hdbscan_epsilon: float

    ollama_url: str
    ollama_model: str
    ollama_timeout: int
    max_cluster_messages: int
    
     







# Singleton
settings = Settings()