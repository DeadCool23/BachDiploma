import numpy as np
from PIL import Image

def fix_by_histogram(img_with_artifacts: Image.Image, original_image: Image.Image) -> Image.Image:
    orig_array = np.array(original_image, dtype=np.float32)
    out_array = np.array(img_with_artifacts, dtype=np.float32)
    
    for i in range(3):
        orig_hist, _ = np.histogram(orig_array[:, :, i].ravel(), bins=256, range=(0, 255))
        out_hist, _ = np.histogram(out_array[:, :, i].ravel(), bins=256, range=(0, 255))
        
        orig_cdf = orig_hist.cumsum() / orig_hist.sum()
        out_cdf = out_hist.cumsum() / out_hist.sum()
        
        lut = np.interp(out_cdf, orig_cdf, np.arange(256))
        
        out_array[:, :, i] = np.interp(out_array[:, :, i].ravel(), np.arange(256), lut).reshape(out_array[:, :, i].shape)
    
    img_with_artifacts = Image.fromarray(out_array.astype(np.uint8))
    
    return img_with_artifacts