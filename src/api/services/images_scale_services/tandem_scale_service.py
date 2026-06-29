import logging
import numpy as np
from PIL.Image import Image
from services.abstract import AbstractImagesScaleService
from scale_services import NeuralScaleService, InterpolationScaleService

class TandemImageScaleService(AbstractImagesScaleService):
    AVAILABLE_INTERPOLATION_SCALING = 1e-3

    def __init__(
            self,
            neural_scale_service: NeuralScaleService,
            interpolation_scale_service: InterpolationScaleService):
        self.neural_available_scales = neural_scale_service.available_scales
        self.neural_scale_service = neural_scale_service
        self.interpolation_scale_service = interpolation_scale_service
    
    def scale_image(self, image: Image, scale_factor: float) -> Image:
        if scale_factor <= 0:
            err_msg = f"Invalid scale factor: {scale_factor}. Scale factor must be a positive number."
            logging.log(logging.ERROR, err_msg)
            raise ValueError(err_msg)
        
        if scale_factor == 1:
            logging.info("Scale factor is 1, returning original image")
            return image
        
        img_size = image.size
        new_size = (int(img_size[0] * scale_factor), int(img_size[1] * scale_factor))
        if new_size[0] == img_size[0]:
            logging.info("New width is the same as original, returning original image")
            return image

        neural_scale_factor = self._select_neural_factor(scale_factor)
        return self._scale_images([image], [neural_scale_factor], new_size)[0]
    
    def reduce_images(self, images: list[Image]) -> list[Image]:
        if len(images) == 0:
            logging.info("No images provided, returning empty list")
            return []
        
        if len(images) == 1:
            err_msg = "At least 2 images are required for reduction"
            logging.warning(err_msg)
            raise ValueError(err_msg)
        
        imgs_sizes = np.array([img.size for img in images])
        logging.info(f"Original images sizes: {imgs_sizes}")
        imgs_aspect_ratios = imgs_sizes[:, 0] / imgs_sizes[:, 1]

        aspect_ratios_equal = np.allclose(imgs_aspect_ratios, imgs_aspect_ratios[0])
        if not aspect_ratios_equal:
            err_msg = "All images must have the same aspect ratio"
            logging.error(err_msg)
            raise ValueError(err_msg)

        max_size = np.max(imgs_sizes, axis=0)
        logging.info(f"Reducing to it max image size: {max_size}")
        scale_factors = max_size[0] / imgs_sizes[:, 0]
        logging.info(f"Calculated scale factors for images: {scale_factors}")
        neural_scale_factors = [self._select_neural_factor(sf) for sf in scale_factors]

        return self._scale_images(images, neural_scale_factors, tuple(max_size))


    def _select_neural_factor(self, scale_factor: float | int) -> int | None:
        if scale_factor <= 1 + self.AVAILABLE_INTERPOLATION_SCALING:
            logging.info(f"Scale factor {scale_factor} is too small for neural scaling, using interpolation")
            return None
        
        neural_scale_factor = None
        int_scale_factor = int(scale_factor)
        frac_scale_factor = round(scale_factor - int_scale_factor, 2)

        if frac_scale_factor <= 0.05 and int_scale_factor in self.neural_available_scales:
            neural_scale_factor = int_scale_factor
        else:
            for scale in sorted(self.neural_available_scales):
                if scale > int_scale_factor:
                    neural_scale_factor = scale
                    break
            else:
                neural_scale_factor = max(self.neural_available_scales)
        
        logging.info(f"Selected neural scale factor: {neural_scale_factor} for requested scale factor: {scale_factor}")
        return neural_scale_factor

    def _scale_images(
            self,
            images: list[Image],
            neural_scale_factors: list[int | None],
            new_size: tuple[int, int]
        ) -> list[Image]:
        if len(images) != len(neural_scale_factors):
            err_msg = f"Number of images and neural scale factors must be the same. Got {len(images)} images and {len(neural_scale_factors)} neural scale factors."
            logging.error(err_msg)
            raise ValueError(err_msg)
        
        proc_imgs = []
        for img, nsf in zip(images, neural_scale_factors):
            proc_img = img
            if nsf is not None:
                logging.info(f"Scaling image of size {img.size} with neural scale factor {nsf}")
                proc_img = self.neural_scale_service.scale_by_factor(proc_img, nsf)
            proc_imgs.append(self.interpolation_scale_service.scale_to_size(proc_img, new_size))
        
        return proc_imgs
