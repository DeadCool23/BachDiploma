from PIL import Image
import io
import zipfile

def load_images_from_zip(zip_data):
    images = []
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        image_files = [f for f in zip_file.namelist() 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        
        for img_name in image_files:
            with zip_file.open(img_name) as img_file:
                img_data = img_file.read()
                img = Image.open(io.BytesIO(img_data))
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                images.append((img_name, img))
    return images

def get_method_names():
    return {
        "nearest": "Ближайший сосед",
        "bilinear": "Билинейный",
        "bicubic": "Бикубический",
        "lanczos": "Ланцош",
        "dev_method": "Разработанный метод"
    }

def get_methods_list():
    return ["nearest", "bilinear", "bicubic", "lanczos", "dev_method"]