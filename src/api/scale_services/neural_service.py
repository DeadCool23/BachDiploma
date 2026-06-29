import os

from scale_services import AbstractScaleService

import torch
import torch.nn as nn

from PIL import Image

import logging
    
class NeuralScaleService(AbstractScaleService):
    def __init__(
            self,
            model: type[nn.Module], 
            args: dict[str, any], 
            trained_models_dir: str, 
            model_filename_pattern: str, 
            available_scales: list[int | float],
            is_pattern_format: bool = True,
            artifacts_fix_funcs: list[callable, dict[str, any]] = []):
        self.__find_device()
        self.args = args
        self.model = model
        self.trained_models_dir = trained_models_dir
        self.model_filename_pattern = model_filename_pattern
        self.is_pattern_format = is_pattern_format
        self.available_scales = available_scales
        self.artifacts_fix_funcs = artifacts_fix_funcs
    
    def __find_device(self):
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            logging.log(logging.INFO, "Device: MPS (GPU на Apple Silicon)")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            logging.log(logging.INFO, "Device: CUDA (NVIDIA GPU)")
        else:
            device = torch.device("cpu")
            logging.log(logging.INFO, "Device: CPU")
        
        self.device = device
    
    def get_device(self):
        return self.device
    
    def scale_by_factor(self, image: Image.Image, scale_factor: int) -> Image.Image:
        if scale_factor not in self.available_scales:
            error_str = f"Scale factor {scale_factor} is not supported. Available scales: {self.available_scales}"
            logging.log(logging.ERROR, error_str)
            raise ValueError(error_str)
        
        logging.log(logging.INFO, f"Processing image with scale factor {scale_factor} using model {self.model.__name__}")
        self.args.scale = scale_factor
        model = self.model(self.args).to(self.device)

        model_path = os.path.join(
            self.trained_models_dir, 
            self.model_filename_pattern.format(scale_factor) if self.is_pattern_format else self.model_filename_pattern
            )
        logging.log(logging.INFO, f"Loading model from {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)
    
        if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            model.load_state_dict(checkpoint['state_dict'], strict=False)
        else:
            model.load_state_dict(checkpoint, strict=False)
        
        model.eval()

        # transform = transforms.Compose([
        #     transforms.ToTensor(),
        # ])
        
        # input_tensor = transform(image).unsqueeze(0).to(self.device)
        # logging.log(logging.INFO, f"Input shape: {input_tensor.shape}")
        
        import numpy as np
        image_np = np.array(image)
        image_tensor = torch.from_numpy(image_np).permute(2, 0, 1).float()
        input_tensor = image_tensor.unsqueeze(0).to(self.device)
        
        logging.log(logging.INFO, f"Input shape: {input_tensor.shape}, range: [{input_tensor.min():.1f}, {input_tensor.max():.1f}]")

        with torch.no_grad():
            output_tensor = model(input_tensor)
        
        output_tensor = output_tensor.squeeze(0).cpu()
    
        output_tensor = torch.clamp(output_tensor, 0, 255)
        
        output_np = output_tensor.permute(1, 2, 0).numpy().astype(np.uint8)
        output_image = Image.fromarray(output_np)
        
        logging.log(logging.INFO, f"Output shape: {output_image.size}, range: [{np.array(output_image).min()}, {np.array(output_image).max()}]")

        corrected_image = self.__fix_artifacts(image, output_image)
        logging.log(logging.INFO, f"Finished fixing artifacts by {len(self.artifacts_fix_funcs)} functions")

        return corrected_image

    def scale_to_size(self, image: Image.Image, size: tuple[int, int]) -> Image.Image:
        img_size = image.size
        scale_factors = size[0] / img_size[0], size[1] / img_size[1]

        if scale_factors[0] != scale_factors[1]:
            error_str = f"Non-uniform scaling is not supported. Calculated scale factors: {scale_factors}"
            logging.log(logging.ERROR, error_str)
            raise ValueError(error_str)
        
        scale_factor = int(scale_factors[0])
        logging.log(logging.INFO, f"Calculated scale factor: {scale_factor} for target size {size} and original size {img_size}")
        return self.scale_by_factor(image, int(scale_factor))
    
    def __fix_artifacts(self, original_image: Image.Image, img_with_artifacts: Image.Image) -> Image.Image:
        corrected_image = img_with_artifacts
        for func, params in self.artifacts_fix_funcs:
            real_params = params.copy()
            real_params['img_with_artifacts'] = corrected_image
            if 'original_image' in real_params:
                real_params['original_image'] = original_image
            corrected_image = func(**real_params)
            logging.log(logging.INFO, f"Applied artifact fix function: {func.__name__}")
        
        return corrected_image
