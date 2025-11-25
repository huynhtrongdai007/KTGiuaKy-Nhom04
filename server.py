import socket
import threading
import sys
from common import *

class Room:
    def __init__(self, room_id, name):
        self.room_id = room_id
        self.name = name
        self.players = [] # Danh sách ClientHandler
        self.game_started = False

    def is_full(self):
        return len(self.players) >= 2

    def is_empty(self):
        return len(self.players) == 0

    def add_player(self, client):
        if self.is_full():
            return False
        self.players.append(client)
        client.room = self
        return True

    def remove_player(self, client):
        if client in self.players:
            self.players.remove(client)
            client.room = None
            return True
        return False

    def broadcast(self, msg_dict, exclude=None):
        for p in self.players:
            if p != exclude:
                p.send(msg_dict)

class ClientHandler(threading.Thread):
    def __init__(self, sock, addr, server):
        super().__init__(daemon=True)
        self.sock = sock
        self.addr = addr
        self.server = server
        self.username = f"Guest_{addr[1]}"
        self.room = None
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
                self.process_request(req)
        except Exception as e:
            print(f"Error client {self.addr}: {e}")
        finally:
            self.server.disconnect(self)
            try:
                self.sock.close()
            except:
                pass

    def broadcast_room_list(self):
        empty_ids = []
        for rid, r in self.server.rooms.items():
            if r.is_empty():
                empty_ids.append(rid)
        
        for rid in empty_ids:
            del self.server.rooms[rid]

        rooms_data = []
        for r in self.server.rooms.values():
            rooms_data.append({
                "id": r.room_id,
                "name": r.name,
                "count": len(r.players),
                "status": "Waiting"
            })
        
        for client in self.server.clients:
            if client.room is None:
                client.send({"type": CMD_ROOM_LIST, "rooms": rooms_data})

    def process_request(self, req):
        cmd = req.get("type")
        
        if cmd == CMD_LOGIN:
            self.username = req.get("username", self.username)
            self.send({"type": CMD_LOGIN_OK, "username": self.username})
            self.broadcast_room_list()

        elif cmd == CMD_LIST_ROOMS:
            self.broadcast_room_list()

        elif cmd == CMD_CREATE_ROOM:
            room_name = req.get("name", f"Room of {self.username}")
            if self.room:
                self.send({"type": CMD_ERROR, "msg": "You are already in a room"})
                return
            
            room_id = self.server.create_room(room_name)
            room = self.server.get_room(room_id)
            if room.add_player(self):
                self.send({"type": CMD_JOIN_OK,
                           "room_id": room_id,
                           "room_name": room_name})
                self.broadcast_room_list()
            else:
                self.send({"type": CMD_ERROR, "msg": "Failed to join created room"})

        elif cmd == CMD_JOIN_ROOM:
            room_id = req.get("room_id")
            room = self.server.get_room(room_id)
            if not room:
                self.send({"type": CMD_ERROR, "msg": "Room not found"})
                return
            
            if self.room:
                self.send({"type": CMD_ERROR, "msg": "You are already in a room"})
                return

            if room.add_player(self):
                self.send({"type": CMD_JOIN_OK,
                           "room_id": room.room_id,
                           "room_name": room.name})
                self.broadcast_room_list()
            else:
                self.send({"type": CMD_ERROR, "msg": "Room is full"})

        elif cmd == CMD_LEAVE_ROOM:
            if self.room:
                room = self.room
                room.remove_player(self)
                if room.is_empty():
                    if room.room_id in self.server.rooms:
                        del self.server.rooms[room.room_id]
                self.broadcast_room_list()

        elif cmd == CMD_CHAT:
            if self.room:
                msg = req.get("msg")
                self.room.broadcast({
                    "type": CMD_CHAT,
                    "username": self.username,
                    "msg": msg
                })

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rooms = {}
        self.room_counter = 1
        self.clients = []

    def start(self):
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen()
            print(f"Server running on {self.host}:{self.port}")
            while True:
                conn, addr = self.sock.accept()
                print(f"New connection: {addr}")
                client = ClientHandler(conn, addr, self)
                self.clients.append(client)
                client.start()
        except KeyboardInterrupt:
            print("Server stopping...")
        finally:
            self.sock.close()

    def create_room(self, name):
        rid = self.room_counter
        self.room_counter += 1
        room = Room(rid, name)
        self.rooms[rid] = room
        return rid

    def get_room(self, rid):
        return self.rooms.get(rid)

    def disconnect(self, client):
        if client in self.clients:
            self.clients.remove(client)
        if client.room:
            room = client.room
            room.remove_player(client)
            if room.is_empty():
                if room.room_id in self.rooms:
                    del self.rooms[room.room_id]

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    server = Server(host, port)
    server.start()