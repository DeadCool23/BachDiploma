import tkinter as tk
from tkinter import ttk
from ui.reduce_tab import ReduceTab
from ui.scale_tab import ScaleTab
from utils.theme import set_plt_colors
from config import WINDOW_SIZE

class ImgScalerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка изображений")
        self.root.geometry(WINDOW_SIZE)
        root.resizable(False, False)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.reduce_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reduce_frame, text="Сведение изображений")
        self.reduce_tab = ReduceTab(self.reduce_frame)
        
        self.scale_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scale_frame, text="Масштабирование")
        self.scale_tab = ScaleTab(self.scale_frame)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        tab_sizes = {
            0: "950x500",
            1: "800x320"
        }
        selected_tab = self.notebook.index(self.notebook.select())
        self.root.geometry(tab_sizes.get(selected_tab, WINDOW_SIZE))

if __name__ == "__main__":
    set_plt_colors()
    root = tk.Tk()
    app = ImgScalerUI(root)
    root.mainloop()