import tkinter as tk
from tkinter import messagebox, simpledialog
import queue
import sys
from common import *
from network import NetworkClient
import tkinter.ttk as ttk

# --- CÁC MÀN HÌNH GIAO DIỆN (UI VIEWS) ---

class LoginView(tk.Frame):
    """Màn hình đăng nhập."""
    def __init__(self, master, on_login):
        super().__init__(master)
        self.on_login = on_login
        
        tk.Label(self, text="CARO GAME", font=("Helvetica", 24, "bold")).pack(pady=30)
        
        frame = tk.Frame(self)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Server IP:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_ip = tk.Entry(frame)
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Username:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_name = tk.Entry(frame)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(self, text="CONNECT", command=self.do_login, bg="#4CAF50", fg="white", width=15).pack(pady=20)

    def do_login(self):
        ip = self.entry_ip.get().strip()
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Username cannot be empty")
            return
        self.on_login(ip, name)
