from fastapi_mongo_base.models import OwnedEntity

from .schemas import BurnTaskSchema


class Burn(BurnTaskSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes
