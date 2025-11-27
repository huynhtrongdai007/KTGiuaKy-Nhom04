import socket
import threading
import sys
from common import *

class Room:
    """
    Lớp đại diện cho một phòng chơi.
    Quản lý danh sách người chơi, bàn cờ, lượt đi và logic thắng thua.
    """
    def __init__(self, room_id, name):
        self.room_id = room_id
        self.name = name
        self.players = [] # Danh sách ClientHandler
        self.board = [['.' for _ in range(BOARD_SIZE)] for __ in range(BOARD_SIZE)]
        self.turn = 0 # 0 hoặc 1 (Index trong mảng players)
        self.symbols = ['X', 'O']
        self.game_started = False
        
        # Theo dõi điểm số
        self.scores = {0: 0, 1: 0} # index -> điểm
        self.total_games = 0
        self.rematch_requests = set() # Tập hợp các người chơi muốn chơi lại

    def is_full(self):
        return len(self.players) >= 2

    def is_empty(self):
        return len(self.players) == 0

    def add_player(self, client):
        """Thêm người chơi vào phòng."""
        if self.is_full():
            return False
        self.players.append(client)
        client.room = self
        return True

    def remove_player(self, client):
        """Xóa người chơi khỏi phòng và xử lý logic liên quan."""
        if client in self.players:
            idx = self.players.index(client)
            self.players.remove(client)
            client.room = None
            
            # Thông báo cho người còn lại
            self.broadcast({
                "type": CMD_OPPONENT_LEFT
            })

            # Nếu đang chơi mà thoát -> Reset game
            if self.game_started:
                self.reset_game()
            
            # Xóa yêu cầu chơi lại
            self.rematch_requests.clear()
            return True
        return False

    def reset_game(self):
        """Làm mới bàn cờ để bắt đầu ván mới."""
        self.board = [['.' for _ in range(BOARD_SIZE)] for __ in range(BOARD_SIZE)]
        self.game_started = False
        self.turn = 0
        self.rematch_requests.clear()

    def broadcast(self, msg_dict, exclude=None):
        """Gửi tin nhắn cho tất cả người chơi trong phòng (trừ người gửi nếu cần)."""
        for p in self.players:
            if p != exclude:
                p.send(msg_dict)

    def start_game(self):
        """Bắt đầu ván chơi mới."""
        if len(self.players) == 2:
            self.reset_game()
            self.game_started = True
            self.total_games += 1
            
            # Gửi thông báo bắt đầu kèm điểm số
            for i in range(2):
                opp_idx = 1 - i
                self.players[i].send({
                    "type": CMD_GAME_START,
                    "symbol": self.symbols[i],
                    "opponent": self.players[opp_idx].username,
                    "my_score": self.scores[i],
                    "total_games": self.total_games - 1
                })
            
            self.broadcast_turn()

    def broadcast_turn(self):
        """Thông báo lượt đi hiện tại."""
        current_player = self.players[self.turn]
        self.broadcast({
            "type": CMD_TURN,
            "symbol": self.symbols[self.turn],
            "username": current_player.username
        })

    def handle_move(self, client, r, c):
        """Xử lý nước đi của người chơi."""
        if not self.game_started:
            return
        
        # Kiểm tra đúng lượt
        idx = self.players.index(client)
        if idx != self.turn:
            return # Không phải lượt
        
        # Kiểm tra tọa độ hợp lệ
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            return
        if self.board[r][c] != '.':
            return

        # Ghi nhận nước đi
        sym = self.symbols[idx]
        self.board[r][c] = sym
        
        # Gửi nước đi hợp lệ cho cả 2 bên
        self.broadcast({
            "type": CMD_VALID_MOVE,
            "r": r, "c": c, "symbol": sym
        })

        # Kiểm tra thắng
        is_win, win_cells = self.check_win(r, c, sym)
        if is_win:
            self.scores[idx] += 1 # Cộng điểm
            self.broadcast({
                "type": CMD_WIN,
                "symbol": sym,
                "username": client.username,
                "r": r, "c": c,
                "win_cells": win_cells
            })
            self.game_started = False
            return

        # Kiểm tra hòa (đầy bàn cờ)
        if all(self.board[i][j] != '.' for i in range(BOARD_SIZE) for j in range(BOARD_SIZE)):
            self.broadcast({"type": CMD_DRAW})
            self.game_started = False
            return

        # Đổi lượt
        self.turn = 1 - self.turn
        self.broadcast_turn()

    def check_win(self, r, c, symbol):
        """
        Kiểm tra xem nước đi tại (r, c) có tạo thành 5 quân liên tiếp không.
        Trả về: (True/False, Danh sách các ô thắng)
        """
        dirs = [(1,0),(0,1),(1,1),(1,-1)] # Ngang, Dọc, Chéo chính, Chéo phụ
        for dr,dc in dirs:
            cells = [(r,c)]
            # Kiểm tra hướng dương
            rr,cc = r+dr, c+dc
            while 0<=rr<BOARD_SIZE and 0<=cc<BOARD_SIZE and self.board[rr][cc]==symbol:
                cells.append((rr,cc))
                rr += dr; cc += dc
            # Kiểm tra hướng âm
            rr,cc = r-dr, c-dc
            while 0<=rr<BOARD_SIZE and 0<=cc<BOARD_SIZE and self.board[rr][cc]==symbol:
                cells.append((rr,cc))
                rr -= dr; cc -= dc
            
            if len(cells) >= WIN_COUNT:
                return True, cells
        return False, None
        
    def handle_rematch(self, client):
        """Xử lý yêu cầu chơi lại."""
        if client not in self.players:
            return
        idx = self.players.index(client)
        self.rematch_requests.add(idx)
        
        # Nếu cả 2 đều đồng ý -> Bắt đầu game mới
        if len(self.rematch_requests) == 2:
            self.start_game()

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
        # Lazy cleanup: Delete empty rooms before sending
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
                "status": "Playing" if r.game_started else "Waiting"
            })
        
        # Broadcast to ALL connected clients (in lobby or not, simpler)
        # Or better: Broadcast to all clients who are NOT in a room (i.e., in Lobby)
        for client in self.server.clients:
            if client.room is None:
                client.send({"type": CMD_ROOM_LIST, "rooms": rooms_data})

    def process_request(self, req):
        cmd = req.get("type")
        
        if cmd == CMD_LOGIN:
            self.username = req.get("username", self.username)
            self.send({"type": CMD_LOGIN_OK, "username": self.username})
            # Gửi luôn danh sách phòng
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
                self.send({"type": CMD_JOIN_OK, "room_id": room_id, "room_name": room_name})
                self.broadcast_room_list() # Update lobby
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
                self.send({"type": CMD_JOIN_OK, "room_id": room.room_id, "room_name": room.name})
                self.broadcast_room_list() # Update lobby
                # Nếu đủ 2 người -> Start game
                if len(room.players) == 2:
                    room.start_game()
                    self.broadcast_room_list() # Update status to Playing
            else:
                self.send({"type": CMD_ERROR, "msg": "Room is full"})

        elif cmd == CMD_LEAVE_ROOM:
            if self.room:
                room = self.room
                room.remove_player(self)
                if room.is_empty():
                    if room.room_id in self.server.rooms:
                        del self.server.rooms[room.room_id]
                self.broadcast_room_list() # Update lobby

        elif cmd == CMD_MOVE:
            if self.room:
                self.room.handle_move(self, req.get("r"), req.get("c"))

        elif cmd == CMD_CHAT:
            if self.room:
                msg = req.get("msg")
                self.room.broadcast({
                    "type": CMD_CHAT,
                    "username": self.username,
                    "msg": msg
                })
        
        elif cmd == CMD_PLAY_AGAIN:
            if self.room:
                self.room.handle_rematch(self)

        elif cmd == CMD_QUICK_PLAY:
            # Find a room with 1 player and not started
            found_room = None
            for r in self.server.rooms.values():
                if len(r.players) == 1 and not r.game_started:
                    found_room = r
                    break
            
            if found_room:
                # Join existing
                if found_room.add_player(self):
                    self.send({"type": CMD_JOIN_OK, "room_id": found_room.room_id, "room_name": found_room.name})
                    self.broadcast_room_list() # Update lobby
                    if len(found_room.players) == 2:
                        found_room.start_game()
                        self.broadcast_room_list() # Update status
                else:
                    self.send({"type": CMD_ERROR, "msg": "Failed to join found room"})
            else:
                # Create new
                import random
                room_name = f"Quick Room #{random.randint(1000, 9999)}"
                room_id = self.server.create_room(room_name)
                room = self.server.get_room(room_id)
                if room.add_player(self):
                    self.send({"type": CMD_JOIN_OK, "room_id": room_id, "room_name": room_name})
                    self.broadcast_room_list() # Update lobby
                else:
                    self.send({"type": CMD_ERROR, "msg": "Failed to create quick room"})

    def send_room_list(self):
        # Lazy cleanup: Delete empty rooms before sending
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
                "status": "Playing" if r.game_started else "Waiting"
            })
        self.send({"type": CMD_ROOM_LIST, "rooms": rooms_data})

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rooms = {} # id -> Room
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
            # Nếu phòng trống thì xóa
            if room.is_empty():
                if room.room_id in self.rooms:
                    del self.rooms[room.room_id]
        
        # Update lobby for everyone else
        # We need a way to call broadcast_room_list from here.
        # Since disconnect is in Server class, we need to move broadcast logic or duplicate it.
        # Better: create a helper method in Server or just do it here.
        
        # Lazy cleanup + Broadcast logic (duplicated for now to avoid circular dependency issues with ClientHandler method)
        # Actually, we can just iterate clients here.
        
        rooms_data = []
        # Cleanup empty rooms first
        empty_ids = [rid for rid, r in self.rooms.items() if r.is_empty()]
        for rid in empty_ids:
            del self.rooms[rid]

        for r in self.rooms.values():
            rooms_data.append({
                "id": r.room_id,
                "name": r.name,
                "count": len(r.players),
                "status": "Playing" if r.game_started else "Waiting"
            })
            
        for c in self.clients:
            if c.room is None:
                try:
                    c.send({"type": CMD_ROOM_LIST, "rooms": rooms_data})
                except:
                    pass

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    server = Server(host, port)
    server.start()