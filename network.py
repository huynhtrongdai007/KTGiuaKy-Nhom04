import socket
import threading
from common import * 

class NetworkClient:
    """
    Lớp quản lý kết nối mạng phía Client.
    Chịu trách nhiệm gửi/nhận tin nhắn JSON và xử lý luồng nhận tin riêng biệt.
    """
    def __init__(self, host, port, on_message_callback):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.on_message = on_message_callback # Hàm callback để xử lý tin nhắn nhận được
        self.recv_thread = None
        self.running = False

    def connect(self):
        """
        Mở kết nối đến Server.
        Trả về True nếu thành công, False nếu thất bại.
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Chạy luồng nhận tin riêng (chưa có logic) để không chặn giao diện (UI)
            self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.recv_thread.start()
            return True
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        """
        Ngắt kết nối an toàn.
        """
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass

    def send(self, data):
        """
        Gửi dữ liệu (Dictionary) lên Server.
        """
        if not self.connected:
            return
        try:
            # Dùng hàm giả định từ common.py
            send_json(self.sock, data) 
        except Exception as e:
            print(f"Lỗi gửi tin: {e}")
            self.disconnect()
    