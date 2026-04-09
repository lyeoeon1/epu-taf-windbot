from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    llama_cloud_api_key: str = ""

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_connection_string: str = ""

    frontend_url: str = "http://localhost:3000"
    backend_port: int = 8000

    # Advanced retrieval feature toggles
    enable_advanced_retrieval: bool = True
    enable_multi_query: bool = True
    enable_hyde: bool = True
    enable_bm25: bool = True
    enable_reranking: bool = True
    enable_glossary_expansion: bool = True

    # Retrieval tuning parameters
    dense_weight: float = 0.8
    sparse_weight: float = 0.2
    rerank_top_k: int = 8
    bm25_top_k: int = 20
    dense_top_k: int = 20
    multi_query_count: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
