#!/usr/bin/env python3

import os
import cv2
import shutil
import subprocess
import pandas as pd

from skimage.metrics import peak_signal_noise_ratio
from skimage.metrics import structural_similarity

def calculate_metrics_from_path(scaled_img_path, etalon_img_path):
    original = cv2.imread(scaled_img_path)
    comparison = cv2.imread(etalon_img_path)
    
    if original is None:
        raise ValueError(f"Cannot load original image: {scaled_img_path}")
    if comparison is None:
        raise ValueError(f"Cannot load comparison image: {etalon_img_path}")
    
    original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    comparison = cv2.cvtColor(comparison, cv2.COLOR_BGR2RGB)
    
    if original.shape != comparison.shape:
        comparison = cv2.resize(comparison, (original.shape[1], original.shape[0]))
    
    psnr_value = peak_signal_noise_ratio(original, comparison, data_range=255)
    ssim_value = structural_similarity(original, comparison, channel_axis=-1, data_range=255)
    
    return psnr_value, ssim_value


def get_image_metrics_urban_100(urban_100_dir, num):
    """Обрабатывает одно изображение и возвращает метрики для всех вариантов"""
    
    img_metrics = {
        "lanczos2": {},
        "lanczos3": {},
        "lanczos4": {}
    }
    
    for scale in [2, 4]:
        print(f"Processing image {num} with scale {scale}")
        
        test_scale = 2 if scale == 2 else 4
        images_dir = f"{urban_100_dir}/X{test_scale}/"
        
        hr_img_path = f"{images_dir}/HIGH/img_{num:03d}_SRF_{test_scale}_HR.png"
        lr_img_path = f"{images_dir}/LOW/img_{num:03d}_SRF_{test_scale}_LR.png"
        
        res = subprocess.run(["./measure/lanczos.exe", lr_img_path, str(scale)])
        os.remove(f"./img_{num:03d}_SRF_{test_scale}_LR_lanczos_time.json")
        
        for n in [2, 3, 4]:
            old_path = f"img_{num:03d}_SRF_{test_scale}_LR_lanczos{n}.png"
            new_path = f"./measure/lanczos_imgs/img_{num:03d}_SRF_{test_scale}_LR_lanczos{n}_x{scale}.png"
            shutil.move(old_path, new_path)
            
            psnr, ssim = calculate_metrics_from_path(new_path, hr_img_path)
            print(f"LANCZOS{n} PSNR: {psnr}, SSIM: {ssim}")
            
            key = f"lanczos{n}"
            img_metrics[key][f"psnr_x{scale}"] = round(psnr, 2)
            img_metrics[key][f"ssim_x{scale}"] = round(ssim, 4)
    
    return img_metrics


def get_avg_metrics(all_images_metrics):
    sums = {
        "lanczos2": {"psnr_x2": 0, "ssim_x2": 0, "psnr_x4": 0, "ssim_x4": 0},
        "lanczos3": {"psnr_x2": 0, "ssim_x2": 0, "psnr_x4": 0, "ssim_x4": 0},
        "lanczos4": {"psnr_x2": 0, "ssim_x2": 0, "psnr_x4": 0, "ssim_x4": 0}
    }
    
    num_images = len(all_images_metrics)
    
    for img_metrics in all_images_metrics:
        for lanczos_type in ["lanczos2", "lanczos3", "lanczos4"]:
            metrics = img_metrics[lanczos_type]
            for key in sums[lanczos_type].keys():
                if key in metrics:
                    sums[lanczos_type][key] += metrics[key]
    
    avg_metrics = {}
    for lanczos_type in ["lanczos2", "lanczos3", "lanczos4"]:
        avg_metrics[lanczos_type] = {}
        for key in sums[lanczos_type].keys():
            avg_metrics[lanczos_type][key] = round(sums[lanczos_type][key] / num_images, 4)
    
    return avg_metrics


def get_metrics(urban_100_dir, cnt):
    all_images_metrics = []
    
    for i in range(1, cnt + 1):
        print(f"\nProcessing image {i}/{cnt}...")
        img_metrics = get_image_metrics_urban_100(urban_100_dir, i)
        all_images_metrics.append(img_metrics)
    
    avg_metrics = get_avg_metrics(all_images_metrics)
    
    return avg_metrics


def save_metrics_to_csv(metrics, csv_path="metrics_results.csv"):
    rows = []
    for lanczos_type in ["lanczos2", "lanczos3", "lanczos4"]:
        row = {"filter": lanczos_type}
        row.update(metrics[lanczos_type])
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    df = df[["filter", "psnr_x2", "ssim_x2", "psnr_x4", "ssim_x4"]]
    
    print("РЕЗУЛЬТАТЫ:")
    print(df.to_string(index=False))
    
    df.to_csv(csv_path, index=False)
    print(f"\nМетрики сохранены в файл: {csv_path}")
    
    return df


def main():
    os.makedirs("./measure/lanczos_imgs", exist_ok=True)
    
    urban_100_dir = "./datasets/Urban 100"
    num_images = 100

    metrics = get_metrics(urban_100_dir, num_images)
    
    df = save_metrics_to_csv(metrics, "./measure/metrics/lanczos_metrics.csv")
    
    print(f"\n📊 Статистика:")
    print(f"   - Обработано изображений: {num_images}")
    print(f"   - Масштабы: x2, x4")
    print(f"   - Фильтры: Lanczos2, Lanczos3, Lanczos4")


if __name__ == "__main__":
    main()