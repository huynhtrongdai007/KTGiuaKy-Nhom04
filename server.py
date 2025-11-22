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