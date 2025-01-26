import secrets

from fastapi_mongo_base.models import OwnedEntity
from pydantic import Field
from server.config import Settings

from .schemas import BurnTaskSchema


class Burn(BurnTaskSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes
