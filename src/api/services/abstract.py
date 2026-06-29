from PIL.Image import Image
from abc import ABC, abstractmethod

class AbstractImagesScaleService(ABC):
    @abstractmethod
    def scale_image(self, image: Image, scale_factor: int) -> Image:
        pass
    
    @abstractmethod
    def reduce_images(self, images: list[Image]) -> list[Image]:
        pass