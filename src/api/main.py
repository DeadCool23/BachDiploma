import argparse

from types import SimpleNamespace

import uvicorn

import os
import dotenv
import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from routers import scale, reduce

from models.rcan import RCAN, RCANConfig
from artifacts_fixes.color_artifacts import fix_by_histogram
from scale_services import NeuralScaleService, InterpolationScaleService, InterpolMethod
from services.images_scale_services import TandemImageScaleService


app = FastAPI(
    title="ImgScaler API",
    description="Сервис сведения изображений с разными разрешениями к одному разрешению",
    version="1.0.0",
)

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')

app.state.services = SimpleNamespace(
    interpolation_scale_service=InterpolationScaleService(),
    images_scale_service=TandemImageScaleService(
        neural_scale_service=NeuralScaleService(
            model=RCAN,
            args=RCANConfig,
            trained_models_dir=os.getenv("MODELS_DIR"), 
            model_filename_pattern="RCAN_X{:d}.pt",
            available_scales=[2, 3, 4],
        ),
        interpolation_scale_service=InterpolationScaleService(method=InterpolMethod.LANCZOS),
    ),
)

app.include_router(scale.router, prefix="/api/v1/image/scale", tags=["Масштабирование"])
app.include_router(reduce.router, prefix="/api/v1/images/reduce", tags=["Сведение"])


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    with open("./static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ImgScaler API Server")
    parser.add_argument("--port", "-p", type=int, default=os.getenv("API_PORT"), help="Port of the API server")
    parser.add_argument("--host", "-H", type=str, default=os.getenv("API_HOST"), help="Host of the API server")

    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)