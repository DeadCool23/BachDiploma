import matplotlib.pyplot as plt
from PIL import Image

def show_single_image(image_path_or_data, title, is_bytes=False):
    try:
        if is_bytes:
            img = Image.open(image_path_or_data)
        else:
            img = Image.open(image_path_or_data)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(img)
        plt.title(f"{title}\n{img.width}x{img.height}")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        raise e

def show_images_grid(images, title):
    n_images = len(images)
    n_cols = min(3, n_images)
    n_rows = (n_images + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
    if n_images == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, (img_name, img) in enumerate(images):
        axes[idx].imshow(img)
        axes[idx].set_title(f"{img_name}\n{img.width}x{img.height}")
    
    plt.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.show()

def show_comparison(original_img, results, scale):
    n_methods = len(results)
    n_cols = 3
    n_rows = (n_methods + 1 + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
    axes = axes.flatten()
    
    axes[0].imshow(original_img)
    axes[0].set_title(f"Оригинал\n{original_img.width}x{original_img.height}")
    
    for idx, (method_key, method_name, img) in enumerate(results, start=1):
        if img:
            axes[idx].imshow(img)
            axes[idx].set_title(f"{method_name}\n{img.width}x{img.height}")
        else:
            axes[idx].text(0.5, 0.5, f"Ошибка загрузки\n{method_name}", 
                          ha='center', va='center', transform=axes[idx].transAxes)
    
    plt.suptitle(f"Сравнение методов масштабирования (коэффициент x{scale})", fontsize=14)
    plt.tight_layout()
    plt.show()