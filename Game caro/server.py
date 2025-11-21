# server.py
# Chạy: python server.py [HOST] [PORT]
# Mặc định HOST=0.0.0.0, PORT=8765

import socket
import threading
import sys

HOST = '0.0.0.0'
PORT = 8765
if len(sys.argv) >= 2:
    HOST = sys.argv[1]
if len(sys.argv) >= 3:
    PORT = int(sys.argv[2])

BOARD_SIZE = 20
WIN_COUNT = 5

def check_win(board, r, c, symbol):
    # kiểm tra 5 liên tiếp theo 4 hướng
    dirs = [(1,0),(0,1),(1,1),(1,-1)]
    for dr,dc in dirs:
        cnt = 1
        # dương
        rr,cc = r+dr, c+dc
        while 0<=rr<BOARD_SIZE and 0<=cc<BOARD_SIZE and board[rr][cc]==symbol:
            cnt += 1
            rr += dr; cc += dc
        # âm
        rr,cc = r-dr, c-dc
        while 0<=rr<BOARD_SIZE and 0<=cc<BOARD_SIZE and board[rr][cc]==symbol:
            cnt += 1
            rr -= dr; cc -= dc
        if cnt >= WIN_COUNT:
            return True
    return False

class GameThread(threading.Thread):
    def __init__(self, p1_sock, p2_sock, addr1, addr2):
        super().__init__(daemon=True)
        self.socks = [p1_sock, p2_sock]
        self.addrs = [addr1, addr2]
        self.board = [['.' for _ in range(BOARD_SIZE)] for __ in range(BOARD_SIZE)]
        self.symbols = ['X','O']  # p0 -> X, p1 -> O
        self.turn = 0  # index of current player
        self.running = True

    def send(self, idx, msg):
        try:
            self.socks[idx].sendall((msg+"\n").encode())
        except:
            pass

    def broadcast(self, msg):
        for s in self.socks:
            try:
                s.sendall((msg+"\n").encode())
            except:
                pass

    def run(self):
        # gửi START
        try:
            self.send(0, f"START {self.symbols[0]}")
            self.send(1, f"START {self.symbols[1]}")
            # thông báo lượt (X đi trước)
            self.send(self.turn, f"TURN {self.symbols[self.turn]}")
            self.send(1-self.turn, f"WAIT")
        except Exception as e:
            self.stop()
            return

        # tạo thread lắng nghe từng socket
        threads = []
        for idx in (0,1):
            t = threading.Thread(target=self.handle_client, args=(idx,), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        self.stop()

        def handle_client(self, idx):
        s = self.socks[idx]
        f = s.makefile('r', encoding='utf-8')
        try:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # chỉ xử lý MOVE r c
                parts = line.split()
                if parts[0] == "MOVE" and len(parts) == 3:
                    try:
                        r = int(parts[1]); c = int(parts[2])
                    except:
                        self.send(idx, "INVALID bad_coords")
                        continue
                    # kiểm tra lượt
                    if idx != self.turn:
                        self.send(idx, "INVALID not_your_turn")
                        continue
                    # kiểm tra tọa độ
                    if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                        self.send(idx, "INVALID out_of_range")
                        continue
                    if self.board[r][c] != '.':
                        self.send(idx, "INVALID occupied")
                        continue
                    # ghi nước
                    sym = self.symbols[idx]
                    self.board[r][c] = sym
                    # gửi VALID tới cả hai (còn client sẽ tự cập nhật)
                    self.broadcast(f"VALID {r} {c} {sym}")
                    # kiểm tra thắng
                    if check_win(self.board, r, c, sym):
                        self.broadcast(f"WIN {sym}")
                        self.running = False
                        break
                    # kiểm tra hòa (board full)
                    full = all(self.board[i][j] != '.' for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))
                    if full:
                        self.broadcast("DRAW")
                        self.running = False
                        break
                    # đổi lượt
                    self.turn = 1 - self.turn
                    self.send(self.turn, f"TURN {self.symbols[self.turn]}")
                    self.send(1-self.turn, "WAIT")
                else:
                    self.send(idx, "INVALID unknown_command")
        except Exception as e:
            # client rời
            pass
        finally:
            # thông báo đối phương
            try:
                other = 1-idx
                self.send(other, "OPPONENT_LEFT")
            except:
                pass
            self.running = False

    def stop(self):
        for s in self.socks:
            try:
                s.close()
            except:
                pass

def pairer(server_sock):
    print("Server ready. Chờ 2 client kết nối để bắt đầu ván...")
    while True:
        p1, a1 = server_sock.accept()
        print("Client 1 từ", a1)
        # chờ client thứ 2
        p2, a2 = server_sock.accept()
        print("Client 2 từ", a2)
        game = GameThread(p1, p2, a1, a2)
        game.start()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")
        try:
            pairer(s)
        except KeyboardInterrupt:
            print("Shutting down server.")

if __name__ == "__main__":
    main()