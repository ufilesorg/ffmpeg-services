import fastapi
from fastapi import BackgroundTasks
from fastapi_mongo_base.routes import AbstractBaseRouter
from usso.fastapi import jwt_access_security

from .models import Burn
from .schemas import BurnTaskSchema, VideoInfoCreateSchema, VideoInfoSchema
from .services import get_video_metadata_async

class BurnRouter(AbstractBaseRouter):
    def __init__(self):
        super().__init__(
            model=Burn,
            schema=BurnTaskSchema,
            user_dependency=jwt_access_security,
            # tags=["Subtitle"],
            prefix="",
        )

    def config_schemas(self, schema, **kwargs):
        super().config_schemas(schema, **kwargs)
        # self.retrieve_response_schema = SubtitleTaskSchemaDetails

    def config_routes(self, **kwargs):
        super().config_routes(prefix="/burn", **kwargs)
        self.router.add_api_route("/details", self.details, methods=["POST"], response_model=VideoInfoSchema)

    async def details(self, request: fastapi.Request, data: VideoInfoCreateSchema):
        return await get_video_metadata_async(data.url)


router = BurnRouter().router
