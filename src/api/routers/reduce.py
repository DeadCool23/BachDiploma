import io
import time
import zipfile
import logging
from pathlib import Path

from PIL import Image

from services.abstract import AbstractImagesScaleService

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile, Request, HTTPException


router = APIRouter()

@router.post("/")
async def reduce_images(
    request: Request, 
    images: list[UploadFile] = File(...)
):
    if len(images) < 2:
        err_msg = "At least 2 images are required for reduction"
        logging.error(err_msg)
        raise HTTPException(400, err_msg)
    
    for image in images:
        if not image.content_type.startswith("image/"):
            err_msg = "File must be an image"
            logging.error(err_msg)
            raise HTTPException(400, err_msg)
    

    contents = [await image.read() for image in images]
    logging.info(f"Read {len(contents)} images for reduction")
    pil_images = [Image.open(io.BytesIO(content)).convert("RGB") for content in contents]
    logging.info(f"Converted images to RGB mode")
    
    service: AbstractImagesScaleService = request.app.state.services.images_scale_service

    start_time = time.time()
    try:
        reduced_images = service.reduce_images(pil_images)
    except ValueError as e:
        logging.error(f"Error during image reduction: {str(e)}")
        raise HTTPException(400, str(e))

    processing_time = (time.time() - start_time) * 1000
    logging.info(f"Reduced {len(images)} images in {processing_time:.2f} ms")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for original_image, reduced_image in zip(images, reduced_images):
            img_buffer = io.BytesIO()
            reduced_image.save(img_buffer, format=original_image.content_type.split("/")[1], quality=85, optimize=True)
            img_buffer.seek(0)
            
            new_filename = f"reduced_{Path(original_image.filename).name}"
            logging.info(f"Adding reduced image to zip: {new_filename}")
            zip_file.writestr(new_filename, img_buffer.getvalue())
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=reduced_images.zip",
            "X-Processing-Time-MS": str(processing_time),
            "X-Images-Count": str(len(images))
        }
    )
