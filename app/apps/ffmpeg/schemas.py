from fastapi_mongo_base.schemas import OwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin
from pydantic import BaseModel


class BurnTaskSchema(TaskMixin, OwnedEntitySchema):
    pass


class VideoInfoCreateSchema(BaseModel):
    url: str


class VideoInfoSchema(BaseModel):
    duration: float
    width: int
    height: int
