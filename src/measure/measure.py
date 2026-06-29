#!/usr/bin/env python3

import os
import cv2
import requests
import argparse
import json
import shutil
import dotenv
from skimage.metrics import peak_signal_noise_ratio
from skimage.metrics import structural_similarity
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
from functools import partial

dotenv.load_dotenv()

API_URL = f"http://{os.getenv("API_HOST")}:{os.getenv("API_PORT")}"

def call_scale_api(image_path, scale, method):
    if method == "my_method":
        endpoint = "/api/v1/image/scale/method/"
        params = {"scale": scale}
    else:
        endpoint = "/api/v1/image/scale/interpolation/"
        params = {"scale": scale, "interpolation": method}
    
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
        response = requests.post(f"{API_URL}{endpoint}", params=params, files=files)
    
    return response

def get_methods_list():
    return ["nearest", "bilinear", "bicubic", "lanczos", "my_method"]

def get_scaled_image(image_path, scale, method, output_path=None):
    res = call_scale_api(image_path, scale, method)
    
    if res.status_code != 200:
        raise Exception(f"API don't work for method {method}: {res.status_code} - {res.text}")
    
    scaled_img_content = res.content
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(scaled_img_content)
        return output_path
    
    return scaled_img_content

def calculate_metrics_from_content(scaled_img_content, etalon_img_path):
    nparr = np.frombuffer(scaled_img_content, np.uint8)
    original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    comparison = cv2.imread(etalon_img_path)
    
    if original is None:
        raise ValueError(f"Cannot load original image from content")
    if comparison is None:
        raise ValueError(f"Cannot load comparison image: {etalon_img_path}")
    
    original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    comparison = cv2.cvtColor(comparison, cv2.COLOR_BGR2RGB)
    
    if original.shape != comparison.shape:
        comparison = cv2.resize(comparison, (original.shape[1], original.shape[0]))
    
    psnr_value = peak_signal_noise_ratio(original, comparison, data_range=255)
    ssim_value = structural_similarity(original, comparison, channel_axis=-1, data_range=255)
    
    return psnr_value, ssim_value

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
    img_metrics = []

    for i in range(11, 41, 1):
        scale = i / 10
        print(f"Processing image {num} with scale {scale}")

        test_scale = 2 if scale <= 2 else 4
        images_dir = f"{urban_100_dir}/X{test_scale}/"

        hr_img_path = f"{images_dir}/HIGH/img_{num:03d}_SRF_{test_scale}_HR.png"
        lr_img_path = f"{images_dir}/LOW/img_{num:03d}_SRF_{test_scale}_LR.png"

        scaled_img_content = get_scaled_image(lr_img_path, scale, "my_method")
        psnr, ssim = calculate_metrics_from_content(scaled_img_content, hr_img_path)
        print(f"PSNR: {psnr}, SSIM: {ssim}")

        img_metrics.append({
            "scale": scale,
            "psnr": psnr,
            "ssim": ssim
        })
    
    return {"image_num": num, "metrics": img_metrics}

def get_metrics_parallel(urban_100_dir, cnt, workers):
    print(f"Starting parallel processing with {workers} workers...")
    
    process_func = partial(get_image_metrics_urban_100, urban_100_dir)
    
    image_numbers = list(range(1, cnt + 1))
    
    with Pool(processes=workers) as pool:
        results = pool.map(process_func, image_numbers)
    
    return results

def get_metrics(urban_100_dir, cnt):
    images_metrics = []
    for i in range(1, cnt+1):
        print(f"Processing image {i}/{cnt}...")
        metrics = get_image_metrics_urban_100(urban_100_dir, i)
        images_metrics.append(metrics)
    return images_metrics

def get_avg_metrics(metrics):
    scale_metrics = {}
    
    for img_data in metrics:
        for metric in img_data['metrics']:
            scale = metric['scale']
            if scale not in scale_metrics:
                scale_metrics[scale] = {'psnr': [], 'ssim': []}
            scale_metrics[scale]['psnr'].append(metric['psnr'])
            scale_metrics[scale]['ssim'].append(metric['ssim'])
    
    avg_metrics = []
    for scale in sorted(scale_metrics.keys()):
        psnr_list = scale_metrics[scale]['psnr']
        ssim_list = scale_metrics[scale]['ssim']
        
        avg_metrics.append({
            "scale": scale,
            "psnr": round(sum(psnr_list) / len(psnr_list), 2),
            "ssim": round(sum(ssim_list) / len(ssim_list), 4),
        })
    
    return avg_metrics

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {filename}")

def cmd_metrics(args):
    print(f"Starting metrics calculation for {args.cnt} images...")
    metrics_dir = "./measure/metrics"
    os.makedirs(metrics_dir, exist_ok=True)
    
    if args.workers > 1:
        metrics = get_metrics_parallel(args.dir, args.cnt, args.workers)
    else:
        metrics = get_metrics(args.dir, args.cnt)
    
    save_json(metrics, f"{metrics_dir}/metrics.json")
    
    avg_metrics = get_avg_metrics(metrics)
    save_json(avg_metrics, f"{metrics_dir}/avg_metrics.json")
    
    print("\n=== Average Metrics Summary ===")
    for metric in avg_metrics:
        print(f"Scale {metric['scale']}: PSNR = {metric['psnr']}, "
              f"SSIM = {metric['ssim']}")

def cmd_imetrics(args):
    psnr, ssim = calculate_metrics_from_path(args.image, args.etalon_image)
    print(f"PSNR: {psnr} SSIM: {ssim}")

def cmd_compare(args):
    compare_dir = "./measure/compare"
    os.makedirs(compare_dir, exist_ok=True)
    
    image_name = os.path.splitext(os.path.basename(args.scale_image))[0]
    
    
    src_img_name = f"source_{os.path.basename(args.scale_image)}"
    etalon_img_name = f"etalon_{os.path.basename(args.etalon_image)}"
    
    src_img_path = os.path.join(compare_dir, src_img_name)
    etalon_img_path = os.path.join(compare_dir, etalon_img_name)
    
    shutil.copy2(args.scale_image, src_img_path)
    shutil.copy2(args.etalon_image, etalon_img_path)
    
    print(f"Copied source image to: {src_img_path}")
    print(f"Copied etalon image to: {etalon_img_path}")
    
    methods = get_methods_list()
    
    metrics_results = []
    
    for method in methods:
        print(f"\nProcessing method: {method}")
        
        scaled_img_name = f"{method}_{image_name}_scale_{args.scale}.png"
        scaled_img_path = os.path.join(compare_dir, scaled_img_name)
        
        try:
            get_scaled_image(args.scale_image, args.scale, method, scaled_img_path)
            print(f"Scaled image saved to: {scaled_img_path}")
            
            psnr, ssim = calculate_metrics_from_path(scaled_img_path, args.etalon_image)
            print(f"PSNR: {psnr:.4f}, SSIM: {ssim:.4f}")
            
            metrics_results.append({
                "method": method,
                "scaled_image_path": os.path.relpath(scaled_img_path, compare_dir),
                "psnr": round(psnr, 4),
                "ssim": round(ssim, 4)
            })
            
        except Exception as e:
            print(f"Error processing method {method}: {e}")
            metrics_results.append({
                "method": method,
                "error": str(e),
                "psnr": None,
                "ssim": None
            })
    
    comparison_data = {
        "scale": args.scale,
        "src_img": src_img_name,
        "etalon_img": etalon_img_name,
        "metrics": metrics_results
    }
    
    json_filename = f"{image_name}_comparison.json"
    json_path = os.path.join(compare_dir, json_filename)
    save_json(comparison_data, json_path)
    
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"Image: {image_name}")
    print(f"Scale factor: {args.scale}")
    print("\nResults:")
    print("-"*60)
    
    valid_results = [r for r in metrics_results if r.get('psnr') is not None]
    valid_results.sort(key=lambda x: x['psnr'], reverse=True)
    
    for i, result in enumerate(valid_results, 1):
        print(f"{i}. {result['method']:10s} - PSNR: {result['psnr']:.4f}, SSIM: {result['ssim']:.4f}")
    
    if len(valid_results) < len(metrics_results):
        print(f"\nFailed methods: {[r['method'] for r in metrics_results if r.get('psnr') is None]}")
    
    print(f"\nAll results saved to: {json_path}")
    print("="*60)

def cmd_plot(args):
    if not os.path.exists("./measure/metrics/avg_metrics.json"):
        print("Ошибка: Файл avg_metrics.json не найден. Сначала выполните команду 'metrics'")
        return

    with open("./measure/metrics/avg_metrics.json", "r") as f:
        metrics = json.load(f)
    
    scales = [m['scale'] for m in metrics]
    psnr_values = [m['psnr'] for m in metrics]
    ssim_values = [m['ssim'] for m in metrics]

    if args.int:
        scales_smooth = np.linspace(min(scales), max(scales), 1000)
        
        from scipy.interpolate import UnivariateSpline

        s = np.var(scales) * len(scales) * 0.5
        spline_psnr = UnivariateSpline(scales, psnr_values, k=3, s=s)
        spline_ssim = UnivariateSpline(scales, ssim_values, k=3, s=s)
        psnr_plot = spline_psnr(scales_smooth)
        ssim_plot = spline_ssim(scales_smooth)
    else:
        scales_smooth = scales
        psnr_plot = psnr_values
        ssim_plot = ssim_values
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    axes[0].plot(scales_smooth, psnr_plot, 'b-', linewidth=2)
    axes[0].plot(scales, psnr_values, 'b', linewidth=0, marker='o', markersize=4)
    axes[0].set_title("PSNR в зависимости от коэффициента масштабирования", fontsize=12)
    axes[0].set_ylabel("PSNR (dB)", fontsize=10)
    axes[0].set_xlabel("Коэффициент масштабирования", fontsize=10)
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(scales_smooth, ssim_plot, 'r-', linewidth=2)
    axes[1].plot(scales, ssim_values, 'r', linewidth=0, marker='o', markersize=4)
    axes[1].set_title("SSIM в зависимости от коэффициента масштабирования", fontsize=12)
    axes[1].set_ylabel("SSIM", fontsize=10)
    axes[1].set_xlabel("Коэффициент масштабирования", fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim(0, 1)
    
    plt.suptitle("Метрики изображений в зависимости от коэффициента масштабирования", fontsize=14, fontweight='bold')
    plt.tight_layout()
    if args.save:
        plt.savefig("./measure/mes_plot.png", dpi=150, bbox_inches='tight')
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="Image Scaling Metrics and Comparison Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)
    
    dmetrics_parser = subparsers.add_parser('dataset-metrics', help='Calculate metrics on Urban100 dataset')
    dmetrics_parser.add_argument("--dir", "-d", type=str, required=True, help="Dir with Urban100 dataset")
    dmetrics_parser.add_argument("--cnt", "-c", type=int, default=5, help="Count of check image")
    dmetrics_parser.add_argument("--workers", "-w", type=int, default=1, 
                                help="Number of parallel workers (default: 1, use -1 for all CPU cores)")

    plot_parser = subparsers.add_parser('plot', help='Plot metrics for Urban100 dataset')
    plot_parser.add_argument("--save", "-s", action='store_true', help="Save the plot instead of showing it")
    plot_parser.add_argument("--int", "-i", action='store_true', help="Plot interpolation")

    compare_parser = subparsers.add_parser('compare', help='Compare methods')
    compare_parser.add_argument("--scale", "-s", type=float, default=2.0, 
                                help="Scale factor (default: 2.0)")
    compare_parser.add_argument("--scale-image", "-i", type=str, default=1, 
                                help="Image to scale path")
    compare_parser.add_argument("--etalon-image", "-e", type=str, default=1, 
                                help="Etalon image path")
    
    imetrics_parser = subparsers.add_parser('image-metrics', help='Calculate metrics for image with etalon')
    imetrics_parser.add_argument("--image", "-i", type=str, default=1, 
                                help="Image to scale path")
    imetrics_parser.add_argument("--etalon-image", "-e", type=str, default=1, 
                                help="Etalon image path")

    args = parser.parse_args()
    
    if hasattr(args, 'workers') and args.workers == -1:
        args.workers = cpu_count()
        print(f"Using all available CPU cores: {args.workers} workers")
    
    if args.command == 'dataset-metrics':
        cmd_metrics(args)
    elif args.command == 'image-metrics':
        cmd_imetrics(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'plot':
        cmd_plot(args)
    else:
        print(f"Unknown command: {args.command}")

if __name__ == '__main__':
    main()