import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import io
from threading import Thread
from utils.api import call_scale_api, get_filename_from_response
from utils.image_utils import get_method_names, get_methods_list
from ui.preview import show_single_image, show_comparison
from config import API_URL

class ScaleTab:
    def __init__(self, parent):
        self.parent = parent
        self.api_url = API_URL
        self.current_image_path = None
        self.scaled_image_data = None
        self.scaled_image_filename = None
        
        self.setup_ui()
    
    def setup_ui(self):
        main_container = ttk.Frame(self.parent)
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        top_row = ttk.Frame(main_container)
        top_row.pack(fill='x', pady=(0, 15))
        
        source_frame = ttk.LabelFrame(top_row, text="Исходное изображение")
        source_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        source_frame.configure(labelanchor='n')
        
        file_row = ttk.Frame(source_frame)
        file_row.pack(fill='x', padx=10, pady=(10, 5))
        
        ttk.Label(file_row, text="Файл:").pack(side='left')
        self.scale_image_label = ttk.Label(file_row, text="не выбран", foreground='gray')
        self.scale_image_label.pack(side='left', padx=5)
        
        buttons_row = ttk.Frame(source_frame)
        buttons_row.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(buttons_row, text="Загрузить", 
                  command=self.load_image).pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(buttons_row, text="Просмотр", 
                  command=self.preview_original).pack(side='left', expand=True, fill='x', padx=2)
        
        params_frame = ttk.LabelFrame(top_row, text="Параметры масштабирования")
        params_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        params_frame.configure(labelanchor='n')
        
        scale_row = ttk.Frame(params_frame)
        scale_row.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(scale_row, text="Коэффициент:", width=15).pack(side='left')
        self.scale_factor = tk.DoubleVar(value=2.0)
        scale_spinbox = ttk.Spinbox(scale_row, from_=0.1, to=20.0, increment=0.1, 
                                     textvariable=self.scale_factor, width=10)
        scale_spinbox.pack(side='left', padx=10)
        
        method_row = ttk.Frame(params_frame)
        method_row.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(method_row, text="Метод:", width=15).pack(side='left')
        self.scale_method = tk.StringVar(value="dev_method")
        method_combo = ttk.Combobox(method_row, textvariable=self.scale_method, 
                                     values=get_methods_list(), width=10, state='readonly')
        method_combo.pack(side='left', padx=10)
        
        bottom_row = ttk.Frame(main_container)
        bottom_row.pack(fill='both', expand=True)
        
        actions_frame = ttk.LabelFrame(bottom_row, text="Действия")
        actions_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        actions_frame.configure(labelanchor='n')
        
        self.scale_btn = ttk.Button(actions_frame, text="МАСШТАБИРОВАТЬ", 
                                    command=self.scale_image, width=30)
        self.scale_btn.pack(pady=5, padx=10)
        
        self.compare_btn = ttk.Button(actions_frame, text="СРАВНИТЬ МЕТОДЫ", 
                                      command=self.compare_methods, width=30)
        self.compare_btn.pack(pady=5, padx=10)
        
        result_frame = ttk.LabelFrame(bottom_row, text="Полученное изображение")
        result_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        result_frame.configure(labelanchor='n')
        
        result_buttons_container = ttk.Frame(result_frame)
        result_buttons_container.pack(expand=False, anchor='n')
        
        self.preview_result_btn = ttk.Button(result_buttons_container, text="Просмотр полученного изображения", 
                                             command=self.preview_result, state='disabled', width=30)
        self.preview_result_btn.pack(pady=5)
        
        self.download_img_btn = ttk.Button(result_buttons_container, text="Скачать изображение", 
                                           command=self.download_image, state='disabled', width=25)
        self.download_img_btn.pack(pady=5)
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.current_image_path = file_path
            self.scale_image_label.config(text=os.path.basename(file_path))
    
    def preview_original(self):
        if self.current_image_path:
            try:
                show_single_image(self.current_image_path, 
                                f"Исходное изображение\n{os.path.basename(self.current_image_path)}", 
                                is_bytes=False)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть изображение: {str(e)}")
        else:
            messagebox.showwarning("Внимание", "Сначала выберите изображение")
    
    def preview_result(self):
        if self.scaled_image_data:
            try:
                scale = self.scale_factor.get()
                method = self.scale_method.get()
                method_names = get_method_names()
                
                show_single_image(io.BytesIO(self.scaled_image_data),
                                f"Масштабировано (x{scale}, {method_names.get(method, method)})",
                                is_bytes=True)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть изображение: {str(e)}")
        else:
            messagebox.showwarning("Внимание", "Сначала выполните масштабирование")
    
    def scale_image(self):
        if not self.current_image_path:
            messagebox.showerror("Ошибка", "Выберите изображение")
            return
        
        self.scale_btn.config(state='disabled', text="Загрузка...")
        self.compare_btn.config(state='disabled')
        
        def process():
            try:
                scale = self.scale_factor.get()
                method = self.scale_method.get()
                
                response = call_scale_api(self.api_url, self.current_image_path, scale, method)
                
                if response.status_code == 200:
                    self.scaled_image_data = response.content
                    self.scaled_image_filename = get_filename_from_response(
                        response, scale, method, self.current_image_path
                    )
                    
                    self.parent.after(0, lambda: self.download_img_btn.config(state='normal'))
                    self.parent.after(0, lambda: self.preview_result_btn.config(state='normal'))
                    self.parent.after(0, lambda: messagebox.showinfo("Успех", "Изображение успешно масштабировано"))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось соединиться с сервером: {str(e)}"))
            finally:
                self.parent.after(0, lambda: self.scale_btn.config(state='normal', text="МАСШТАБИРОВАТЬ"))
                self.parent.after(0, lambda: self.compare_btn.config(state='normal'))
        
        Thread(target=process, daemon=True).start()
    
    def compare_methods(self):
        if not self.current_image_path:
            messagebox.showwarning("Внимание", "Сначала выберите изображение")
            return
        
        scale = self.scale_factor.get()
        
        self.compare_btn.config(state='disabled', text="Загрузка...")
        self.scale_btn.config(state='disabled')
        
        def load_images():
            from utils.api import call_scale_api
            from utils.image_utils import get_method_names, get_methods_list
            from PIL import Image
            import io
            
            methods = get_methods_list()
            method_names = get_method_names()
            results = []
            
            try:
                original_img = Image.open(self.current_image_path)
                
                for method in methods:
                    response = call_scale_api(self.api_url, self.current_image_path, scale, method)
                    
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        results.append((method, method_names[method], img))
                    else:
                        results.append((method, method_names[method], None))
                
                self.parent.after(0, lambda: show_comparison(original_img, results, scale))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось выполнить сравнение: {str(e)}"))
            finally:
                self.parent.after(0, lambda: self.compare_btn.config(state='normal', text="СРАВНИТЬ МЕТОДЫ"))
                self.parent.after(0, lambda: self.scale_btn.config(state='normal'))
        
        Thread(target=load_images, daemon=True).start()
    
    def download_image(self):
        if self.scaled_image_data:
            import re
            clean_filename = re.sub(r'[<>:"/\\|?*]', '_', self.scaled_image_filename) if self.scaled_image_filename else "scaled_image.jpg"
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                initialfile=clean_filename,
                filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")],
                title="Сохранить изображение"
            )
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(self.scaled_image_data)
                messagebox.showinfo("Успех", "Изображение сохранено")