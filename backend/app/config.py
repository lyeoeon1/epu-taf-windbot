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

    # ONNX reranker settings
    onnx_model_dir: str = "models/reranker-int8"
    reranker_threads: int = 4

    # Retrieval tuning parameters
    dense_weight: float = 0.5   # Equal weight: BM25 proven to find correct chunks from large PDFs
    sparse_weight: float = 0.5  # Was 0.2 — increased to give BM25 keyword matches fair ranking
    rerank_top_k: int = 13      # Was 10 — more context chunks for detailed answers
    bm25_top_k: int = 30        # Was 20 — wider net for keyword search across 2900+ chunks
    dense_top_k: int = 30       # Was 20 — wider net for semantic search
    multi_query_count: int = 2  # Was 3 — reduced to lower latency

    # LLM model selection
    llm_model: str = "gpt-4.1-mini"  # Final choice after A/B test

    # Vietnamese document priority
    enable_vi_priority: bool = True
    vi_score_boost: float = 2.0       # score multiplier for VN chunks before reranking
    vi_reserved_slots: int = 8        # reserved VN positions in final top-K (~60% of rerank_top_k=13)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
