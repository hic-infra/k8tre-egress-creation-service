from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    aws_endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    s3_bucket_name: str
    jwt_secret_key: str
    jupyterhub_api_url: str
    jupyterhub_api_token: str
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )


settings = Settings()
