from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/crypto.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # Vercel preview 배포는 커밋마다 도메인이 바뀌므로 정규식으로 허용한다.
    # 예: https://cryptovol-.*\.vercel\.app
    cors_origin_regex: str = ""
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    fng_base_url: str = "https://api.alternative.me/fng/"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
