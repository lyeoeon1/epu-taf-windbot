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
    enable_hyde: bool = False  # Disabled: reduces latency ~10s, dense search already covers semantic
    enable_bm25: bool = True
    enable_reranking: bool = True
    enable_glossary_expansion: bool = True

    # Retrieval tuning parameters
    dense_weight: float = 0.5   # Equal weight: BM25 proven to find correct chunks from large PDFs
    sparse_weight: float = 0.5  # Was 0.2 — increased to give BM25 keyword matches fair ranking
    rerank_top_k: int = 10      # Was 8 — more context for LLM, reranker ensures quality
    bm25_top_k: int = 30        # Was 20 — wider net for keyword search across 2900+ chunks
    dense_top_k: int = 30       # Was 20 — wider net for semantic search
    multi_query_count: int = 2  # Was 3 — reduced to lower latency

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
