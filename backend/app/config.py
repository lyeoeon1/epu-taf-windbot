from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    llama_cloud_api_key: str = ""

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_connection_string: str = ""

    frontend_url: str = "http://localhost:3000"
    backend_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
