import io
import time
import zipfile
import logging
from pathlib import Path

from PIL import Image

from typing import Literal
from services.abstract import AbstractImagesScaleService
from scale_services import InterpolMethod, InterpolationScaleService

from fastapi import APIRouter
from fastapi import File, UploadFile, Query, Request, HTTPException
from fastapi.responses import Response


router = APIRouter()

@router.post("/method/")
async def scale_image(
    request: Request, 
    image: UploadFile = File(...),
    scale: float = Query(2, ge=0.1, le=4.0, description="Scale factor in [0.1, 4.0]"),
    disposition: Literal["inline", "attachment"] = Query(
        "attachment",
        description="File serve: 'inline' - show in browser, 'attachment' - download"
    )
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    

    service: AbstractImagesScaleService = request.app.state.services.images_scale_service
    
    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    original_size = pil_image.size

    start_time = time.time()
    scaled_image = service.scale_image(pil_image, scale)
    processing_time = (time.time() - start_time) * 1000
    
    new_size = scaled_image.size
    
    img_buffer = io.BytesIO()
    scaled_image.save(img_buffer, format=pil_image.format or "JPEG", quality=95)
    img_buffer.seek(0)
    
    return Response(
        content=img_buffer.getvalue(),
        media_type=image.content_type,
        headers={
            "Content-Disposition": f"{disposition}; filename=x{scale}_{Path(image.filename).name}",
            "X-Original-Width": str(original_size[0]),
            "X-Original-Height": str(original_size[1]),
            "X-New-Width": str(new_size[0]),
            "X-New-Height": str(new_size[1]),
            "X-Processing-Time-MS": str(processing_time),
            "X-Original-Size": str(image.size),
            "X-New-Size": str(len(img_buffer.getvalue()))
        }
    )

api_interpolation_methods = {
    "nearest": InterpolMethod.NEAREST,
    "bilinear": InterpolMethod.BILINEAR,
    "bicubic": InterpolMethod.BICUBIC,
    "lanczos": InterpolMethod.LANCZOS
}

@router.post("/interpolation/")
async def interpolation_scale_image(
    request: Request,
    image: UploadFile = File(...),
    scale: float = Query(2, ge=0.1, le=20.0, description="Scale factor in [0.1, 20.0]"),
    interpolation: Literal["nearest", "bilinear", "bicubic", "lanczos"] = Query(
        "bilinear",
        description="interpolation method: 'nearest', 'bilinear', 'bicubic', 'lanczos'"
    ),
    disposition: Literal["inline", "attachment"] = Query(
        "attachment",
        description="File serve: 'inline' - show in browser, 'attachment' - download"
    )
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    service: InterpolationScaleService = request.app.state.services.interpolation_scale_service
    service.set_method(api_interpolation_methods[interpolation])
    
    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    original_size = pil_image.size

    start_time = time.time()
    scaled_image = service.scale_by_factor(pil_image, scale)
    processing_time = (time.time() - start_time) * 1000
    
    new_size = scaled_image.size
    
    img_buffer = io.BytesIO()
    scaled_image.save(img_buffer, format=pil_image.format or "JPEG", quality=95)
    img_buffer.seek(0)
    
    return Response(
        content=img_buffer.getvalue(),
        media_type=image.content_type,
        headers={
            "Content-Disposition": f"{disposition}; filename=x{scale}_{Path(image.filename).name}",
            "X-Original-Width": str(original_size[0]),
            "X-Original-Height": str(original_size[1]),
            "X-New-Width": str(new_size[0]),
            "X-New-Height": str(new_size[1]),
            "X-Processing-Time-MS": str(processing_time),
            "X-Original-Size": str(image.size),
            "X-New-Size": str(len(img_buffer.getvalue()))
        }
    )
