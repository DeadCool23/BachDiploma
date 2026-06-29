import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image
from threading import Thread
from utils.api import call_reduce_api
from utils.image_utils import load_images_from_zip
from ui.preview import show_single_image, show_images_grid
from config import API_URL

class ReduceTab:
    def __init__(self, parent):
        self.parent = parent
        self.api_url = API_URL
        self.reduce_images_list = []
        self.result_zip = None
        
        self.setup_ui()
    
    def setup_ui(self):
        main_container = ttk.Frame(self.parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_panel = ttk.LabelFrame(main_container, text="Выбранные изображения")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        left_panel.configure(labelanchor='n')
        
        list_container = ttk.Frame(left_panel)
        list_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.reduce_listbox = tk.Listbox(list_container, height=12)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.reduce_listbox.yview)
        self.reduce_listbox.configure(yscrollcommand=scrollbar.set)
        self.reduce_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Первый ряд кнопок
        btn_row1 = ttk.Frame(left_panel)
        btn_row1.pack(fill='x', padx=5, pady=2)
        
        btn_row1.grid_columnconfigure(0, weight=1)
        btn_row1.grid_columnconfigure(1, weight=1)
        btn_row1.grid_columnconfigure(2, weight=1)
        
        ttk.Button(btn_row1, text="Добавить", 
                  command=self.add_images).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(btn_row1, text="Удалить", 
                  command=self.remove_image).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(btn_row1, text="Очистить", 
                  command=self.clear_images).grid(row=0, column=2, padx=2, pady=2, sticky='ew')
        
        btn_row2 = ttk.Frame(left_panel)
        btn_row2.pack(fill='x', padx=5, pady=2)
        
        btn_row2.grid_columnconfigure(0, weight=1)
        btn_row2.grid_columnconfigure(1, weight=1)
        
        ttk.Button(btn_row2, text="Просмотр выбранного", 
                  command=self.preview_selected).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(btn_row2, text="Просмотр всех", 
                  command=self.preview_all).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        
        right_panel = ttk.LabelFrame(main_container, text="Результат сведения")
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        right_panel.configure(labelanchor='n')
        
        reduce_btn_container = ttk.Frame(right_panel)
        reduce_btn_container.pack(fill='x', pady=20)
        
        self.reduce_btn = ttk.Button(reduce_btn_container, text="СВЕДЕНИЕ", 
                                     command=self.reduce_images)
        self.reduce_btn.pack(fill='x', padx=20, ipady=10)
        
        result_buttons_container = ttk.Frame(right_panel)
        result_buttons_container.pack(fill='x', pady=20)
        
        self.preview_result_btn = ttk.Button(result_buttons_container, text="Просмотр результата", 
                                             command=self.preview_result, state='disabled')
        self.preview_result_btn.pack(fill='x', padx=20, pady=5)

        self.download_zip_btn = ttk.Button(result_buttons_container, text="Скачать архив", 
                                           command=self.download_zip, state='disabled')
        self.download_zip_btn.pack(fill='x', padx=20, pady=5)
        
        
        right_panel.pack_propagate(False)
    
    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        for file in files:
            if file not in self.reduce_images_list:
                self.reduce_images_list.append(file)
                self.reduce_listbox.insert(tk.END, os.path.basename(file))
    
    def remove_image(self):
        selection = self.reduce_listbox.curselection()
        if selection:
            index = selection[0]
            self.reduce_listbox.delete(index)
            del self.reduce_images_list[index]
    
    def clear_images(self):
        self.reduce_listbox.delete(0, tk.END)
        self.reduce_images_list.clear()
    
    def preview_selected(self):
        selection = self.reduce_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите изображение для просмотра")
            return
        
        index = selection[0]
        image_path = self.reduce_images_list[index]
        
        try:
            show_single_image(image_path, f"{os.path.basename(image_path)}", is_bytes=False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение: {str(e)}")
    
    def preview_all(self):
        if not self.reduce_images_list:
            messagebox.showwarning("Внимание", "Нет загруженных изображений")
            return
        
        try:
            images = [(os.path.basename(path), Image.open(path)) for path in self.reduce_images_list]
            show_images_grid(images, f"Все изображения ({len(images)} шт.)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображения: {str(e)}")
    
    def preview_result(self):
        if not self.result_zip:
            messagebox.showwarning("Внимание", "Сначала выполните сведение")
            return
        
        try:
            images = load_images_from_zip(self.result_zip)
            if images:
                show_images_grid(images, f"Результат сведения ({len(images)} изображений)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть результат: {str(e)}")
    
    def reduce_images(self):
        if len(self.reduce_images_list) < 2:
            messagebox.showerror("Ошибка", "Необходимо выбрать минимум 2 изображения")
            return
        
        self.reduce_btn.config(state='disabled', text="ЗАГРУЗКА...")
        
        def process():
            try:
                response = call_reduce_api(self.api_url, self.reduce_images_list)
                
                if response.status_code == 200:
                    self.result_zip = response.content
                    self.parent.after(0, lambda: self.download_zip_btn.config(state='normal'))
                    self.parent.after(0, lambda: self.preview_result_btn.config(state='normal'))
                    self.parent.after(0, lambda: messagebox.showinfo("Успех", "Изображения успешно сведены"))
                else:
                    error_detail = ""
                    try:
                        error_detail = response.json().get('detail', '')
                    except:
                        pass
                    translations = {
                        "All images must have the same aspect ratio": "Все изображения должны иметь одинаковое соотношение сторон",
                        "Invalid token": "Недействительный токен",
                        "Unauthorized": "Неавторизованный доступ",
                        "Not found": "Не найдено",
                        "Internal server error": "Внутренняя ошибка сервера",
                    }
                    
                    error_message_ru = translations.get(error_detail, error_detail)
                    self.parent.after(0, lambda: messagebox.showerror("Ошибка", error_message_ru))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось соединиться с сервером: {str(e)}"))
            finally:
                self.parent.after(0, lambda: self.reduce_btn.config(state='normal', text="СВЕДЕНИЕ"))
        
        Thread(target=process, daemon=True).start()
    
    def download_zip(self):
        if self.result_zip:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                title="Сохранить архив"
            )
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(self.result_zip)
                messagebox.showinfo("Успех", "Архив сохранен")