import socket
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import queue

if len(sys.argv) < 3:
    print("Usage: python client.py HOST PORT")
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

BOARD_SIZE = 20  
recv_q = queue.Queue()

def recv_thread(sock):
    f = sock.makefile('r', encoding='utf-8')
    try:
        for line in f:
            recv_q.put(line.strip())
    except:
       
        recv_q.put("OPPONENT_LEFT")
    finally:
        try:
            sock.close()
        except:
            pass



class CaroClient:
    def __init__(self, master, sock):
        self.master = master
        self.sock = sock

        self.symbol = None        
        self.my_turn = False
        self.game_over = False
        self.last_move = None    

        master.title("Caro - Client")

     
        self.status = tk.Label(master, text="Đang chờ START...", font=("Arial", 12))
        self.status.pack(pady=5)

        self.frame = tk.Frame(master)
        self.frame.pack()

  
        self.buttons = []
        for r in range(BOARD_SIZE):
            row = []
            for c in range(BOARD_SIZE):
                b = tk.Button(
                    self.frame,
                    text=" ",
                    width=2,
                    height=1,
                    command=lambda rr=r, cc=c: self.on_click(rr, cc)
                )
                b.grid(row=r, column=c)
                row.append(b)
            self.buttons.append(row)

   
        self.default_bg = self.buttons[0][0].cget("bg")

       
        self.board = [['.' for _ in range(BOARD_SIZE)] for __ in range(BOARD_SIZE)]


        self.master.after(100, self.process_incoming)


    def on_click(self, r, c):
        if self.game_over:
            return
        if not self.symbol:
            return
        if not self.my_turn:
            return
        if self.board[r][c] != '.':
            return

 
        try:
            msg = f"MOVE {r} {c}\n"
            self.sock.sendall(msg.encode())
        except:
            messagebox.showerror("Lỗi", "Không gửi được đến server.")
            self.end_game()

 
    def process_incoming(self):
        while not recv_q.empty():
            line = recv_q.get()
            if not line:
                continue
            parts = line.split()
            cmd = parts[0]

            if cmd == "START":
             
                self.symbol = parts[1]
                self.status.config(text=f"Bạn là '{self.symbol}'. Đang chờ lượt...")

            elif cmd == "TURN":
               
                sym = parts[1]
                self.my_turn = (sym == self.symbol)
                if self.my_turn:
                    self.status.config(text=f"Bạn là '{self.symbol}' - ĐẾN LƯỢT BẠN")
                else:
                    self.status.config(text=f"Bạn là '{self.symbol}' - Đang chờ đối phương")

            elif cmd == "WAIT":
                self.my_turn = False
                self.status.config(text=f"Bạn là '{self.symbol}' - Đang chờ đối phương")

            elif cmd == "VALID":
                # VALID r c S
                r = int(parts[1])
                c = int(parts[2])
                s = parts[3]
                self.board[r][c] = s
                self.update_button(r, c, s)

            elif cmd == "WIN":
                winner = parts[1]
                if winner == self.symbol:
                    messagebox.showinfo("Kết quả", "Bạn thắng!")
                    self.status.config(text="Bạn thắng! Ván đã kết thúc.")
                else:
                    messagebox.showinfo("Kết quả", "Bạn thua.")
                    self.status.config(text="Bạn thua. Ván đã kết thúc.")
                self.end_game()

            elif cmd == "DRAW":
                messagebox.showinfo("Kết quả", "Hòa.")
                self.status.config(text="Hòa. Ván đã kết thúc.")
                self.end_game()

            elif cmd == "INVALID":
                reason = " ".join(parts[1:]) if len(parts) > 1 else ""
         
                print("INVALID từ server:", reason)
               

            elif cmd == "OPPONENT_LEFT":
                if not self.game_over:
                    messagebox.showwarning("Thông báo", "Đối thủ đã rời. Ván kết thúc.")
                    self.status.config(text="Đối thủ đã rời. Ván kết thúc.")
                    self.end_game()

            else:
                print("Unknown msg:", line)

      
        self.master.after(100, self.process_incoming)


    def update_button(self, r, c, s):
    
        if self.last_move is not None:
            lr, lc = self.last_move
            old_btn = self.buttons[lr][lc]
            old_btn.config(bg=self.default_bg)

        b = self.buttons[r][c]

      
        if s == 'X':
            fg_color = "red"
        else:  
            fg_color = "blue"

        b.config(
            text=s,
            state="disabled",
            fg=fg_color,
            font=("Arial", 10, "bold"),
            bg="#ffe4b5" 
        )

        self.last_move = (r, c)

   
    def disable_all(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                self.buttons[r][c].config(state="disabled")

    def end_game(self):
        self.game_over = True
        self.my_turn = False
        self.disable_all()
        try:
            self.sock.close()
        except:
            pass



def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except Exception as e:
        print("Không thể kết nối server:", e)
        sys.exit(1)

    t = threading.Thread(target=recv_thread, args=(sock,), daemon=True)
    t.start()

    root = tk.Tk()
    app = CaroClient(root, sock)
    root.mainloop()


if __name__ == "__main__":
    main()
