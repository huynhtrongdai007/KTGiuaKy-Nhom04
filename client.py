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

class GameView(tk.Frame):
    """Màn hình chơi game (Bàn cờ)."""
    def __init__(self, master, on_move, on_chat, on_leave):
        super().__init__(master)
        self.on_move = on_move
        self.on_chat = on_chat
        self.on_leave = on_leave
        
        # Trái: Bàn cờ
        self.left_panel = tk.Frame(self)
        self.left_panel.pack(side="left", padx=10, pady=10)
        
        # Phải: Thông tin & Chat
        self.right_panel = tk.Frame(self, width=200)
        self.right_panel.pack(side="right", fill="y", padx=10, pady=10)
        
        # Thông tin phòng
        self.lbl_room = tk.Label(self.right_panel, text="Room: ???", font=("Arial", 12, "bold"))
        self.lbl_room.pack(pady=5)
        
        self.lbl_score = tk.Label(self.right_panel, text="Score: 0/0", font=("Arial", 10))
        self.lbl_score.pack(pady=2)

        self.lbl_status = tk.Label(self.right_panel, text="Waiting...", fg="gray")
        self.lbl_status.pack(pady=5)
        self.lbl_turn = tk.Label(self.right_panel, text="", font=("Arial", 14))
        self.lbl_turn.pack(pady=10)
        
        tk.Button(self.right_panel, text="Leave Room", command=on_leave, bg="#f44336", fg="white").pack(pady=5)

        # Khung Chat chuyên nghiệp
        chat_container = tk.Frame(self.right_panel, relief="flat", bg="#ffffff")
        chat_container.pack(fill="both", expand=True, pady=10)
        
        # Header Chat
        chat_header = tk.Frame(chat_container, bg="#2196F3", height=30)
        chat_header.pack(fill="x")
        tk.Label(chat_header, text="💬 CHAT", font=("Arial", 10, "bold"), bg="#2196F3", fg="white").pack(pady=5)
        
        # Chat log với scrollbar
        chat_frame = tk.Frame(chat_container)
        chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(chat_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.chat_log = tk.Text(chat_frame, height=12, width=28, state="disabled", 
                                wrap="word", yscrollcommand=scrollbar.set,
                                font=("Arial", 9), bg="white")
        self.chat_log.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.chat_log.yview)
        
        # Input frame
        input_frame = tk.Frame(chat_container, bg="white")
        input_frame.pack(fill="x", padx=5, pady=5)
        
        self.entry_chat = tk.Entry(input_frame, font=("Arial", 9))
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_chat.bind("<Return>", self.send_chat)
        
        tk.Button(input_frame, text="📤", command=self.send_chat, 
                  bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                  width=3, relief="flat").pack(side="right")

        # Cấu hình tags cho chat bubbles (kiểu Facebook Messenger)
        # Nền trắng cho chat log
        self.chat_log.config(bg="white")
        
        # Tin nhắn của tôi: Hồng phấn, canh phải, margin trái lớn để tạo bubble nhỏ
        self.chat_log.tag_config("own_bubble", background="#FFE4E9", 
                                lmargin1=100, lmargin2=100, rmargin=8,
                                spacing1=3, spacing3=3, justify="right")
        self.chat_log.tag_config("own_name", foreground="#D32F2F", font=("Arial", 8, "bold"),
                                justify="right", lmargin1=100, rmargin=8)
        
        # Tin nhắn đối thủ: Xanh cyan nhạt, sát lề trái, margin phải lớn để tạo bubble nhỏ
        self.chat_log.tag_config("opponent_bubble", background="#E0F7FA",
                                lmargin1=8, lmargin2=8, rmargin=100,
                                spacing1=3, spacing3=3, justify="left")
        self.chat_log.tag_config("opponent_name", foreground="#0277BD", font=("Arial", 8, "bold"),
                                justify="left", lmargin1=8, rmargin=100)

        # Canvas bàn cờ (điều chỉnh kích thước ô cho 20x20)
        self.cell_size = 31  # Giảm từ 42 xuống 31 để bàn cờ 20x20 vừa khung
        self.canvas_size = BOARD_SIZE * self.cell_size
        self.canvas = tk.Canvas(self.left_panel, width=self.canvas_size, height=self.canvas_size, bg="#ffe4b5")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.draw_grid()
        self.last_move_item = None

    def draw_grid(self):
        """Vẽ lưới ô vuông."""
        for i in range(BOARD_SIZE + 1):
            self.canvas.create_line(0, i*self.cell_size, self.canvas_size, i*self.cell_size)
            self.canvas.create_line(i*self.cell_size, 0, i*self.cell_size, self.canvas_size)

    def on_click(self, event):
        """Xử lý sự kiện click chuột trên bàn cờ."""
        c = event.x // self.cell_size
        r = event.y // self.cell_size
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            self.on_move(r, c)

    def send_chat(self, event=None):
        msg = self.entry_chat.get().strip()
        if msg:
            self.on_chat(msg)
            self.entry_chat.delete(0, tk.END)

    def add_chat(self, sender, msg, is_own=False):
        """Thêm tin nhắn vào khung chat với bubble styling."""
        self.chat_log.config(state="normal")
        
        # Chọn tag dựa trên người gửi
        name_tag = "own_name" if is_own else "opponent_name"
        bubble_tag = "own_bubble" if is_own else "opponent_bubble"
        
        if is_own:
            # Tin nhắn của tôi: căn phải
            self.chat_log.insert(tk.END, f"{sender}\n", name_tag)
            # Thêm padding vào tin nhắn để tạo bubble
            padded_msg = f" {msg} "
            self.chat_log.insert(tk.END, f"{padded_msg}\n", bubble_tag)
        else:
            # Tin nhắn đối thủ: sát lề trái
            self.chat_log.insert(tk.END, f"{sender}\n", name_tag)
            # Thêm padding vào tin nhắn
            padded_msg = f" {msg} "
            self.chat_log.insert(tk.END, f"{padded_msg}\n", bubble_tag)
        
        # Khoảng trắng giữa các bubble (tăng khoảng cách)
       # self.chat_log.insert(tk.END, "\n\n")
        
        self.chat_log.see(tk.END)
        self.chat_log.config(state="disabled")

    def highlight_win(self, win_cells):
        """Vẽ khung đỏ quanh các ô thắng."""
        for r, c in win_cells:
            x1 = c * self.cell_size
            y1 = r * self.cell_size
            self.canvas.create_rectangle(x1, y1, x1+self.cell_size, y1+self.cell_size, outline="red", width=3)

    def draw_move(self, r, c, symbol, is_last=True):
        """Vẽ quân cờ (X hoặc O) tại vị trí (r, c)."""
        x = c * self.cell_size + self.cell_size // 2
        y = r * self.cell_size + self.cell_size // 2
        color = "red" if symbol == "X" else "blue"
        
        self.canvas.create_text(x, y, text=symbol, fill=color, font=("Arial", 16, "bold"))
        
        if is_last:
            if self.last_move_item:
                self.canvas.delete(self.last_move_item)
            # Highlight nước đi cuối cùng (màu xanh lá)
            x1 = c * self.cell_size
            y1 = r * self.cell_size
            self.last_move_item = self.canvas.create_rectangle(x1, y1, x1+self.cell_size, y1+self.cell_size, outline="green", width=2)

    def reset_board(self):
        """Xóa bàn cờ để chơi ván mới."""
        self.canvas.delete("all")
        self.draw_grid()
        self.last_move_item = None
        self.chat_log.config(state="normal")
        self.chat_log.delete(1.0, tk.END)
        self.chat_log.config(state="disabled")

# --- BỘ ĐIỀU KHIỂN CHÍNH (MAIN CONTROLLER) ---

class CaroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caro Premium ProMax Ultra 4K Titan Super Unlimited Hyper Quantum Infinity Omega Supreme Legendary Edition AI")
        self.geometry("900x700")
        
        self.network = None
        self.username = ""
        self.msg_queue = queue.Queue()

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.views = {}
        
        # Init Views
        self.views["login"] = LoginView(self.container, self.handle_login)
        self.views["lobby"] = LobbyView(self.container, self.handle_create_room, self.handle_join_room, self.handle_refresh_lobby, self.handle_quick_play)
        self.views["game"] = GameView(self.container, self.handle_move, self.handle_chat, self.handle_leave_room)

        self.show_view("login")
        
        self.after(100, self.process_queue)

    def show_view(self, name):
        for view in self.views.values():
            view.pack_forget()
        self.views[name].pack(fill="both", expand=True)

    def process_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                self.handle_server_message(msg)
        except queue.Empty:
            pass
        self.after(50, self.process_queue)

    def on_network_message(self, msg):
        self.msg_queue.put(msg)

    def on_closing(self):
        if self.network:
            self.network.disconnect()
        self.destroy()
