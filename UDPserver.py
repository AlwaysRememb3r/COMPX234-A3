
import socket
import threading
import random
import os
import base64
import time

class UDPServer:
    def __init__(self, port):
        # Initialize server with specified port
        self.server_port = port
        # Create UDP socket for welcoming client requests (Lecture 5: Socket Programming)
        self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind socket to all interfaces on the specified port (Lecture 5: Socket Binding)
        self.welcome_socket.bind(('', self.server_port))
        print(f"Server started on port {self.server_port}")

    def start(self):
        # Main server loop to continuously listen for client requests
        while True:
            try:
                # Receive client request (buffer size 1024) (Lecture 7: UDP Protocol)
                data, client_address = self.welcome_socket.recvfrom(1024)
                # Decode and strip the request message
                client_request = data.decode().strip()
                print(f"Received from {client_address}: {client_request}")

                # Tokenize the request message by spaces (help for A4: Tokenization)
                parts = client_request.split()
                # Validate request format: must start with "DOWNLOAD" (Protocol specification)
                if len(parts) < 2 or parts[0] != "DOWNLOAD":
                    print(f"Invalid request format: {client_request}")
                    continue

                # Construct filename from parts (handles filenames with spaces)
                filename = ' '.join(parts[1:])
                # Check if file exists on server (File system interaction)
                if not os.path.exists(filename):
                    # Send error response for non-existent file (Protocol specification)
                    error_msg = f"ERR {filename} NOT_FOUND"
                    self.welcome_socket.sendto(error_msg.encode(), client_address)
                    print(f"File not found: {filename}")
                    continue

                # Get file size and create new thread for client (Lecture 5: Multithreading)
                file_size = os.path.getsize(filename)
                threading.Thread(target=self.handle_client, 
                               args=(filename, file_size, client_address)).start()

            except Exception as e:
                # Handle exceptions in main loop (Error handling best practices)
                print(f"Error in main server loop: {e}")

    def handle_client(self, filename, file_size, client_address):
        try:
            # Allocate random port for data transfer (50000-51000) (help for A4: Port Allocation)
            client_port = random.randint(50000, 51000)
            # Create new socket for this client's data communication (Lecture 5: Socket Creation)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Bind socket to the random port (Lecture 5: Socket Binding)
            client_socket.bind(('', client_port))

            # Send OK response with file details and data port (Protocol specification)
            ok_msg = f"OK {filename} SIZE {file_size} PORT {client_port}"
            self.welcome_socket.sendto(ok_msg.encode(), client_address)
            print(f"Sent to {client_address}: {ok_msg}")

            # Open file for binary reading (File I/O operations)
            with open(filename, 'rb') as file:
                while True:
                    # Receive client requests on the data port (Lecture 7: UDP Data Reception)
                    data, client_addr = client_socket.recvfrom(1024)
                    client_request = data.decode().strip()
                    print(f"Received on port {client_port}: {client_request}")

                    # Tokenize the client request (help for A4: Tokenization)
                    parts = client_request.split()
                    # Validate as FILE request (Protocol specification)
                    if len(parts) < 2 or parts[0] != "FILE":
                        print(f"Invalid FILE request: {client_request}")
                        continue

                    # Check for CLOSE request to terminate connection (Protocol specification)
                    if parts[2] == "CLOSE":
                        close_msg = f"FILE {filename} CLOSE_OK"
                        client_socket.sendto(close_msg.encode(), client_addr)
                        print(f"Sent to {client_addr}: {close_msg}")
                        break

                    # Validate GET request format with byte ranges (Protocol specification)
                    if len(parts) < 7 or parts[2] != "GET" or parts[3] != "START" or parts[5] != "END":
                        print(f"Invalid GET request: {client_request}")
                        continue

                    try:
                        # Parse start and end byte indices (Data range handling)
                        start = int(parts[4])
                        end = int(parts[6])
                        block_size = end - start + 1

                        # Seek to start position and read block (File seek and read)
                        file.seek(start)
                        file_data = file.read(block_size)

                        # Encode binary data to Base64 (help for A4: Base64 Encoding)
                        base64_data = base64.b64encode(file_data).decode('utf-8')
                        # Construct response with encoded data (Protocol specification)
                        response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                        client_socket.sendto(response.encode(), client_addr)
                        print(f"Sent block {start}-{end} to {client_addr}")

                    except Exception as e:
                        # Handle errors in data processing (Error handling)
                        print(f"Error processing GET request: {e}")

        except Exception as e:
            # Handle exceptions in client thread (Error handling)
            print(f"Error in client handler: {e}")
        finally:
            # Close client socket to release resources (Resource management)
            client_socket.close()
            print(f"Closed connection for {filename} with {client_address}")

if __name__ == "__main__":
    import sys
    # Validate command line arguments (Input validation)
    if len(sys.argv) != 2:
        print("Usage: python UDPserver.py <port>")
        sys.exit(1)

    # Parse port number from command line (Command line parsing)
    port = int(sys.argv[1])
    # Create and start server (Application entry point)
    server = UDPServer(port)
    server.start()
