import socket
import threading
import random
import os
import base64
import time


class UDPServer:
    def __init__(self, port):
        self.server_port = port
        self.welcome_socket = None
        self.running = False
        self.start_server()

    def start_server(self):
        try:
            # Create UDP socket for welcoming client requests (Lecture 5: Socket Programming)
            self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allow address reuse to prevent "address in use" errors (help for A4: Socket Configuration)
            self.welcome_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind socket to all interfaces on specified port (Lecture 5: Socket Binding)
            self.welcome_socket.bind(('', self.server_port))
            self.running = True
            print(f"[SERVER] Started on port {self.server_port}")
        except OSError as e:
            print(f"[ERROR] Failed to start server: {e}")
            print(f"[TIP] Try another port or wait 1-2 minutes for OS to release the port")
            self.cleanup()
            raise

    def cleanup(self):
        if self.welcome_socket:
            # Close socket to release resources (Resource management best practice)
            self.welcome_socket.close()
        self.running = False

    def handle_client(self, filename, file_size, client_address):
        client_socket = None
        try:
            # Allocate random port for client data transfer (50000-51000) (help for A4: Port Allocation)
            client_port = random.randint(50000, 51000)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.bind(('', client_port))

            # Send OK response with file size and data port (Protocol specification from assignment)
            ok_msg = f"OK {filename} SIZE {file_size} PORT {client_port}"
            self.welcome_socket.sendto(ok_msg.encode('utf-8'), client_address)
            print(f"[SERVER] Sent to {client_address}: {ok_msg}")

            with open(filename, 'rb') as file:
                while self.running:
                    try:
                        # Receive client request on data port (Lecture 7: UDP Data Reception)
                        data, addr = client_socket.recvfrom(65536)
                        request = data.decode('utf-8').strip()
                        print(f"[SERVER] Received: {request} from {addr}")

                        # Handle CLOSE request to terminate connection (Protocol specification)
                        if request == f"FILE {filename} CLOSE":
                            client_socket.sendto(
                                f"FILE {filename} CLOSE_OK".encode('utf-8'),
                                addr
                            )
                            break

                        # Process block data request (Protocol specification)
                        if request.startswith(f"FILE {filename} GET START"):
                            parts = request.split()
                            start = int(parts[4])
                            end = int(parts[6])
                            file.seek(start)
                            block = file.read(end - start + 1)

                            # Encode binary data to Base64 for text-based protocol (help for A4: Base64 Encoding)
                            base64_data = base64.b64encode(block).decode('utf-8')
                            response = (
                                f"FILE {filename} OK START {start} END {end} "
                                f"DATA {base64_data}"
                            )
                            client_socket.sendto(response.encode('utf-8'), addr)
                            print(f"[SERVER] Sent block {start}-{end} to {addr}")

                    except Exception as e:
                        print(f"[ERROR] Client handler: {e}")
                        break

        except Exception as e:
            print(f"[ERROR] Client thread failed: {e}")
        finally:
            if client_socket:
                client_socket.close()
            print(f"[SERVER] Closed connection for {filename}")

    def run(self):
        try:
            while self.running:
                # Receive initial DOWNLOAD request on welcome socket (Lecture 7: UDP Protocol)
                data, addr = self.welcome_socket.recvfrom(1024)
                request = data.decode('utf-8').strip()
                print(f"[SERVER] New request from {addr}: {request}")

                # Process DOWNLOAD request (Protocol specification)
                if request.startswith("DOWNLOAD"):
                    filename = request[9:].strip()
                    if not os.path.exists(filename):
                        # Send error response for non-existent file (Protocol specification)
                        err_msg = f"ERR {filename} NOT_FOUND"
                        self.welcome_socket.sendto(err_msg.encode('utf-8'), addr)
                        print(f"[SERVER] File not found: {filename}")
                    else:
                        file_size = os.path.getsize(filename)
                        # Create new thread for client (Lecture 5: Multithreading)
                        threading.Thread(
                            target=self.handle_client,
                            args=(filename, file_size, addr),
                            daemon=True
                        ).start()

        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")
        except Exception as e:
            print(f"[CRITICAL] Server error: {e}")
        finally:
            self.cleanup()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python UDPserver.py <port>")
        sys.exit(1)

    try:
        server = UDPServer(int(sys.argv[1]))
        server.run()
    except OSError:
        print("[FATAL] Failed to initialize server")
        sys.exit(1)
