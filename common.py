import json
import struct

# Hằng số chung
BOARD_SIZE = 20  # Tăng từ 15 lên 20
WIN_COUNT = 5    # Số quân liên tiếp để thắng
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765

# --- GIAO THỨC MẠNG (PROTOCOL) ---
# Định nghĩa các mã lệnh (Command) để Client và Server hiểu nhau
CMD_LOGIN = "LOGIN"             # Đăng nhập
CMD_LOGIN_OK = "LOGIN_OK"       # Đăng nhập thành công
CMD_LIST_ROOMS = "LIST_ROOMS"   # Yêu cầu danh sách phòng
CMD_ROOM_LIST = "ROOM_LIST"     # Trả về danh sách phòng
CMD_CREATE_ROOM = "CREATE_ROOM" # Tạo phòng mới
CMD_JOIN_ROOM = "JOIN_ROOM"     # Vào phòng
CMD_JOIN_OK = "JOIN_OK"         # Vào phòng thành công
CMD_GAME_START = "GAME_START"   # Bắt đầu game
CMD_MOVE = "MOVE"               # Gửi nước đi
CMD_VALID_MOVE = "VALID_MOVE"   # Nước đi hợp lệ (để vẽ lên bàn cờ)
CMD_WIN = "WIN"                 # Thắng
CMD_DRAW = "DRAW"               # Hòa
CMD_TURN = "TURN"               # Đến lượt ai
CMD_CHAT = "CHAT"               # Chat trong phòng
CMD_OPPONENT_LEFT = "OPPONENT_LEFT" # Đối thủ thoát
CMD_ERROR = "ERROR"             # Lỗi chung
CMD_LEAVE_ROOM = "LEAVE_ROOM"   # Rời phòng
CMD_PLAY_AGAIN = "PLAY_AGAIN"   # Yêu cầu chơi lại
CMD_UPDATE_SCORE = "UPDATE_SCORE" # Cập nhật điểm số
CMD_QUICK_PLAY = "QUICK_PLAY"   # Chơi nhanh (Tìm phòng ngẫu nhiên)

# --- HÀM HỖ TRỢ MẠNG (NETWORK HELPERS) ---

def send_json(sock, data):
    """
    Gửi dữ liệu JSON qua socket.
    Cấu trúc gói tin: [4 bytes độ dài] + [Dữ liệu JSON]
    """
    try:
        msg = json.dumps(data).encode('utf-8')
        # Đóng gói độ dài tin nhắn vào 4 byte đầu tiên (Big Endian)
        sock.sendall(struct.pack('>I', len(msg)) + msg)
    except Exception as e:
        print(f"Lỗi gửi JSON: {e}")

def recvall(sock, n):
    """
    Hàm hỗ trợ nhận đủ n bytes dữ liệu từ socket.
    Đảm bảo không bị mất dữ liệu do phân mảnh gói tin TCP.
    """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def recv_json(sock):
    """
    Nhận và giải mã dữ liệu JSON từ socket.
    1. Đọc 4 byte đầu để biết độ dài tin nhắn.
    2. Đọc tiếp đúng độ dài đó.
    3. Giải mã JSON thành Dictionary.
    """
    try:
        # Bước 1: Đọc độ dài
        raw_len = recvall(sock, 4)
        if not raw_len: return None
        msg_len = struct.unpack('>I', raw_len)[0]
        
        # Bước 2: Đọc nội dung
        raw_msg = recvall(sock, msg_len)
        if not raw_msg: return None
        
        # Bước 3: Giải mã
        return json.loads(raw_msg.decode('utf-8'))
    except Exception as e:
        return None
