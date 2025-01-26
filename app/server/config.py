"""FastAPI server configuration."""

import dataclasses
import os
from pathlib import Path

import dotenv
from fastapi_mongo_base.core.config import Settings as BaseSettings

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent.parent
    base_path: str = "/v1/apps/ffmpeg"
    update_time: int = 10

    UFILES_API_KEY: str = os.getenv("UFILES_API_KEY")
    UFILES_BASE_URL: str = os.getenv("UFILES_URL", default="https://media.pixiee.io/v1")
    USSO_BASE_URL: str = os.getenv("USSO_URL", default="https://sso.pixiee.io")
    UFAAS_BASE_URL: str = os.getenv("UFAAS_BASE_URL", default="https://media.pixiee.io")
