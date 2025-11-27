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

class LobbyView(tk.Frame):
    """Màn hình sảnh chờ (Lobby)."""
    def __init__(self, master, on_create, on_join, on_refresh, on_quick_play):
        super().__init__(master)
        self.on_create = on_create
        self.on_join = on_join
        self.on_refresh = on_refresh
        self.on_quick_play = on_quick_play
        
        # Header
        header_frame = tk.Frame(self, bg="#2196F3", height=60)
        header_frame.pack(fill="x")
        
        # Button packed to the right
        tk.Button(header_frame, text="↻ Refresh", command=on_refresh, font=("Arial", 10, "bold"), bg="white", fg="#2196F3", relief="flat").pack(side="right", padx=20, pady=15)
        
        # Label packed to fill remaining space (effectively centering it)
        tk.Label(header_frame, text="SẢNH CHỜ", font=("Helvetica", 24, "bold"), bg="#2196F3", fg="white").pack(side="left", expand=True, fill="x", pady=10)

        # Khu vực nội dung chính
        content_frame = tk.Frame(self, padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)

        # Danh sách phòng (Treeview)
        columns = ("id", "name", "players", "status")
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=15)
        
        # Tiêu đề cột
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Tên Phòng")
        self.tree.heading("players", text="Số người")
        self.tree.heading("status", text="Trạng thái")
        
        # Độ rộng cột
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("players", width=100, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        
        # Thanh cuộn
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Các nút chức năng
        btn_frame = tk.Frame(self, pady=20)
        btn_frame.pack(fill="x", padx=20)
        
        # Style cho nút
        style = ttk.Style()
        style.configure("Action.TButton", font=("Arial", 12, "bold"), padding=10)
        
        tk.Button(btn_frame, text="✚ Create Room", command=self.prompt_create, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="⚡ Quick Play", command=self.on_quick_play, bg="#9C27B0", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="➜ Join Selected", command=self.do_join, bg="#FF9800", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="right", padx=10)

        self.rooms_data = []

    def update_list(self, rooms):
        self.rooms_data = rooms
        # Xóa danh sách cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Thêm danh sách mới
        for r in rooms:
            status = r['status']
            players = f"{r['count']}/2"
            self.tree.insert("", "end", values=(r['id'], r['name'], players, status))

    def prompt_create(self):
        name = simpledialog.askstring("Create Room", "Enter room name:")
        if name:
            self.on_create(name)

    def do_join(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a room to join")
            return
        
        item = self.tree.item(sel[0])
        room_id = item['values'][0]
        self.on_join(room_id)
