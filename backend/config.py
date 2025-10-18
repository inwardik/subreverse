from pydantic_settings import BaseSettings, SettingsConfigDict
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int

    model_config = SettingsConfigDict(env_file=os.path.join(BASE_DIR, ".env"))

settings = Settings()
print(settings.DB_HOST)