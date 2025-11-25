import socket
import threading
import sys
from common import *

class ClientHandler(threading.Thread):
    def __init__(self, sock, addr, server):
        super().__init__(daemon=True)
        self.sock = sock
        self.addr = addr
        self.server = server
        self.username = f"Guest_{addr[1]}"
        self.running = True

    def send(self, data):
        try:
            send_json(self.sock, data)
        except:
            pass

    def run(self):
        try:
            while self.running:
                req = recv_json(self.sock)
                if not req:
                    break
                cmd = req.get("type")
                if cmd == CMD_LOGIN:
                    self.username = req.get("username", self.username)
                    self.send({"type": CMD_LOGIN_OK, "username": self.username})
        except Exception as e:
            print(e)
        finally:
            self.server.disconnect(self)
            self.sock.close()

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        print(f"Server started on {self.host}:{self.port}")
        while True:
            conn, addr = self.sock.accept()
            print("New client:", addr)
            client = ClientHandler(conn, addr, self)
            self.clients.append(client)
            client.start()

    def disconnect(self, client):
        if client in self.clients:
            self.clients.remove(client)

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    Server(host, port).start()
