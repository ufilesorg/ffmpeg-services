from apps.ffmpeg.routes import router as burn_router
from fastapi_mongo_base.core import app_factory

from . import config, worker

app = app_factory.create_app(
    settings=config.Settings(),
    worker=worker.worker,
    origins=[
        "https://dkp.pixiee.io",
        "https://localhost:3000",
        "http://localhost:8000",
    ],
)
app.include_router(burn_router, prefix=f"{config.Settings.base_path}")
