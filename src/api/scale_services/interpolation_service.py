import logging
import numpy as np
from enum import IntEnum

from PIL.Image import Resampling, Image

from scale_services import AbstractScaleService


class InterpolMethod(IntEnum):
    NEAREST = 0
    BOX = 4
    BILINEAR = 2
    HAMMING = 5
    BICUBIC = 3
    LANCZOS = 1

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

class InterpolationScaleService(AbstractScaleService):
    EPS = 1e-2
    methods_map = {
        InterpolMethod.NEAREST: Resampling.NEAREST,
        InterpolMethod.BOX: Resampling.BOX,
        InterpolMethod.BILINEAR: Resampling.BILINEAR,
        InterpolMethod.HAMMING: Resampling.HAMMING,
        InterpolMethod.BICUBIC: Resampling.BICUBIC,
        InterpolMethod.LANCZOS: Resampling.LANCZOS,
    }

    def __init__(self, method: InterpolMethod = InterpolMethod.BICUBIC):
        self.method = self.methods_map[method]

    def set_method(self, method: InterpolMethod):
        if method not in self.methods_map:
            err_msg = f"Unsupported interpolation method: {method}. Supported methods: {list(self.methods_map.keys())}"
            logging.log(logging.ERROR, err_msg)
            raise ValueError(err_msg)
        
        self.method = self.methods_map[method]
        logging.log(logging.INFO, f"Interpolation method set to {method.name}")
    
    def scale_by_factor(self, image: Image, scale_factor: float) -> Image:
        if scale_factor <= 0:
            err_msg = f"Invalid scale factor: {scale_factor}. Scale factor must be a positive integer."
            logging.log(logging.ERROR, err_msg)
            raise ValueError(err_msg)
        
        if scale_factor == 1:
            logging.log(logging.INFO, "Scale factor is 1, returning original image")
            return image
        
        logging.log(logging.INFO, f"Scaling image by factor {scale_factor} using method {self.method.name}")
        
        img_size = image.size
        new_size = (int(img_size[0] * scale_factor), int(img_size[1] * scale_factor))

        return self.scale_to_size(image, new_size)

    def scale_to_size(self, image: Image, size: tuple[int, int]) -> Image:
        if size[0] <= 0 or size[1] <= 0:
            err_msg = f"Invalid target size: {size}. Width and height must be positive integers."
            logging.log(logging.ERROR, err_msg)
            raise ValueError(err_msg)
        
        if size == image.size:
            logging.log(logging.INFO, "Target size is the same as original, returning original image")
            return image
        
        if not np.isclose(image.size[0] / size[0], image.size[1] / size[1], atol=self.EPS):
            err_msg = f"Non-uniform scaling is not supported. Original size: {image.size}, target size: {size}"
            logging.log(logging.ERROR, err_msg)
            raise ValueError(err_msg)
        
        logging.log(logging.INFO, f"Scaling image from size {image.size} to new size {size} using method {self.method.name}")
        return image.resize(size, self.method)