use image::ImageReader;
use fast_image_resize::{Resizer, ResizeOptions, FilterType, Filter, ResizeAlg, PixelType};
use fast_image_resize::images::Image as FirImage;
use std::env;
use std::path::Path;
use std::time::Instant;
use std::f64::consts::PI;

#[inline]
fn sinc_filter(x: f64) -> f64 {
    if x == 0.0 {
        1.0
    } else {
        let pix = x * PI;
        pix.sin() / pix
    }
}

#[inline]
fn lanczos2_filter(x: f64) -> f64 {
    if (-2.0..2.0).contains(&x) {
        sinc_filter(x) * sinc_filter(x / 2.0)
    } else {
        0.0
    }
}

#[inline]
#[allow(dead_code)]
fn lanczos3_filter(x: f64) -> f64 {
    if (-3.0..3.0).contains(&x) {
        sinc_filter(x) * sinc_filter(x / 3.0)
    } else {
        0.0
    }
}

#[inline]
fn lanczos4_filter(x: f64) -> f64 {
    if (-4.0..4.0).contains(&x) {
        sinc_filter(x) * sinc_filter(x / 4.0)
    } else {
        0.0
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 3 {
        eprintln!("Использование: {} <путь к изображению> <коэффицент масштабирования>", args[0]);
        std::process::exit(1);
    }
    
    let input_path = &args[1];
    let scale_factor = args[2].parse::<u32>().unwrap();
    let mut results = std::collections::HashMap::new();
    
    let input_stem = Path::new(input_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("output");
    
    let output_l2 = format!("{}_lanczos2.png", input_stem);
    let output_l3 = format!("{}_lanczos3.png", input_stem);
    let output_l4 = format!("{}_lanczos4.png", input_stem);
    
    println!("Загружаем изображение: {}", input_path);
    
    let dynamic_img = ImageReader::open(input_path)?
        .decode()?;
    
    let (width, height) = (dynamic_img.width(), dynamic_img.height());
    let rgb8 = dynamic_img.to_rgb8();
    let pixels = rgb8.as_raw();
    
    println!("Исходный размер: {}x{}", width, height);
    
    let src_image = FirImage::from_vec_u8(
        width, 
        height, 
        pixels.clone(), 
        PixelType::U8x3
    )?;
    
    let new_width = width * scale_factor;
    let new_height = height * scale_factor;
    
    println!("Новый размер: {}x{} (x{})", new_width, new_height, scale_factor);
    
    let lanczos2_filter_type = FilterType::Custom(
        Filter::new("Lanczos2", lanczos2_filter, 2.0).unwrap()
    );
    let lanczos3_filter_type = FilterType::Lanczos3;
    let lanczos4_filter_type = FilterType::Custom(
        Filter::new("Lanczos4", lanczos4_filter, 4.0).unwrap()
    );
    
    let alg_lanczos2 = ResizeAlg::Convolution(lanczos2_filter_type);
    let alg_lanczos3 = ResizeAlg::Convolution(lanczos3_filter_type);
    let alg_lanczos4 = ResizeAlg::Convolution(lanczos4_filter_type);
    
    let mut resizer = Resizer::new();
    let options2 = ResizeOptions::new().resize_alg(alg_lanczos2);
    let options3 = ResizeOptions::new().resize_alg(alg_lanczos3);
    let options4 = ResizeOptions::new().resize_alg(alg_lanczos4);
    
    let mut dst_image_l2 = FirImage::new(new_width, new_height, PixelType::U8x3);
    let mut dst_image_l3 = FirImage::new(new_width, new_height, PixelType::U8x3);
    let mut dst_image_l4 = FirImage::new(new_width, new_height, PixelType::U8x3);
    
    println!("Выполняется ресайз с Lanczos4...");
    let start = Instant::now();
    resizer.resize(&src_image, &mut dst_image_l4, &options4)?;
    let duration_l4 = start.elapsed();
    println!("Время выполнения Lanczos4: {:?}", duration_l4);
    
    println!("Выполняется ресайз с Lanczos3...");
    let start = Instant::now();
    resizer.resize(&src_image, &mut dst_image_l3, &options3)?;
    let duration_l3 = start.elapsed();
    println!("Время выполнения Lanczos3: {:?}", duration_l3);
    
    println!("Выполняется ресайз с Lanczos2...");
    let start = Instant::now();
    resizer.resize(&src_image, &mut dst_image_l2, &options2)?;
    let duration_l2 = start.elapsed();
    println!("Время выполнения Lanczos2: {:?}", duration_l2);


    results.insert("lanczos2", duration_l2.as_secs_f64());
    results.insert("lanczos3", duration_l3.as_secs_f64());
    results.insert("lanczos4", duration_l4.as_secs_f64());
    
    let json_path = format!("{}_lanczos_time.json", input_stem);
    let json_content = serde_json::to_string_pretty(&results)?;
    std::fs::write(&json_path, json_content)?;
    println!("\nВремя выполнения сохранено в: {}", json_path);
    
    let save_image = |dst: &FirImage, path: &str| -> Result<(), Box<dyn std::error::Error>> {
        let (w, h) = (dst.width(), dst.height());
        let pixels = dst.buffer();
        
        match dst.pixel_type() {
            PixelType::U8x3 => {
                let img = image::RgbImage::from_raw(w, h, pixels.to_vec())
                    .ok_or("Не удалось создать RGB изображение")?;
                img.save(path)?;
                println!("Сохранено: {}", path);
            }
            _ => {
                return Err("Неподдерживаемый формат пикселей".into());
            }
        }
        Ok(())
    };
    
    save_image(&dst_image_l2, &output_l2)?;
    save_image(&dst_image_l3, &output_l3)?;
    save_image(&dst_image_l4, &output_l4)?;
    
    println!("\nГотово! Файлы сохранены:");
    println!("  - Lanczos2 (a=2): {}", output_l2);
    println!("  - Lanczos3 (a=3): {}", output_l3);
    println!("  - Lanczos4 (a=4): {}", output_l4);
    
    Ok(())
}