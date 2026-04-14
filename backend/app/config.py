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
    rerank_top_k: int = 13      # Was 10 — more context chunks for detailed answers
    bm25_top_k: int = 20        # Was 30 — reduced to lower reranking latency (candidates #21+ rarely make top-13)
    dense_top_k: int = 20       # Was 30 — reduced to lower reranking latency
    multi_query_count: int = 1  # Was 2 — still have: original + glossary expanded + 1 variant = 3 query angles
    max_rerank_candidates: int = 25  # Cap candidates before reranking (FlashRank on 2-core VPS is slow)

    # LLM model selection
    llm_model: str = "gpt-4o-mini"  # Options: "gpt-4o-mini", "gpt-4.1-mini"

    # Vietnamese document priority
    enable_vi_priority: bool = True
    vi_score_boost: float = 2.0       # score multiplier for VN chunks before reranking
    vi_reserved_slots: int = 8        # reserved VN positions in final top-K (~60% of rerank_top_k=13)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
