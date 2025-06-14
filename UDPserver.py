import socket
import threading
import random
import os
import base64

class UDPServer:
    def __init__(self, port):
        self.server_port = port
        self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.welcome_socket.bind(('', self.server_port))
        print(f"Server started on port {self.server_port}")

    def handle_client(self, filename, file_size, client_address):
        try:
            client_port = random.randint(50000, 51000)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.bind(('', client_port))

            ok_msg = f"OK {filename} SIZE {file_size} PORT {client_port}"
            self.welcome_socket.sendto(ok_msg.encode('utf-8'), client_address)
            print(f"Sent to {client_address}: {ok_msg}")

            with open(filename, 'rb') as file:
                while True:
                    data, client_addr = client_socket.recvfrom(65536)
                    request = data.decode('utf-8').strip()
                    print(f"Received request: {request}")

                    if request.startswith("FILE") and "CLOSE" in request:
                        close_msg = f"FILE {filename} CLOSE_OK"
                        client_socket.sendto(close_msg.encode('utf-8'), client_addr)
                        break

                    parts = request.split()
                    if len(parts) >= 7 and parts[2] == "GET":
                        start = int(parts[4])
                        end = int(parts[6])
                        file.seek(start)
                        block = file.read(end - start + 1)
                        base64_data = base64.b64encode(block).decode('utf-8')
                        response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                        client_socket.sendto(response.encode('utf-8'), client_addr)
                        print(f"Sent block {start}-{end}")

        except Exception as e:
            print(f"Error in client handler: {e}")
        finally:
            client_socket.close()

    def start(self):
        while True:
            data, client_address = self.welcome_socket.recvfrom(1024)
            request = data.decode('utf-8').strip()
            print(f"Received from {client_address}: {request}")

            if request.startswith("DOWNLOAD"):
                filename = request[9:].strip()
                if not os.path.exists(filename):
                    error_msg = f"ERR {filename} NOT_FOUND"
                    self.welcome_socket.sendto(error_msg.encode('utf-8'), client_address)
                else:
                    file_size = os.path.getsize(filename)
                    threading.Thread(
                        target=self.handle_client,
                        args=(filename, file_size, client_address)
                    ).start()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python UDPserver.py <port>")
        sys.exit(1)
    server = UDPServer(int(sys.argv[1]))
    server.start()
