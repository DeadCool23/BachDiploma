from PIL import Image
from abc import ABC, abstractmethod

class AbstractScaleService(ABC):
    @abstractmethod
    def scale_by_factor(self, image: Image.Image, scale_factor: int | float) -> Image.Image:
        pass

    @abstractmethod
    def scale_to_size(self, image: Image.Image, size: tuple[int, int]) -> Image.Image:
        pass