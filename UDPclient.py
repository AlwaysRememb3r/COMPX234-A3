import socket
import sys
import os
import base64

class UDPClient:
    def __init__(self, hostname, port, file_list):
        self.server_host = hostname
        self.server_port = port
        self.file_list = file_list
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.initial_timeout = 1000  # 1 second
        self.max_retries = 5

    def send_and_receive(self, message, address, port):
        retries = 0
        current_timeout = self.initial_timeout
        while retries < self.max_retries:
            try:
                self.socket.sendto(message.encode('utf-8'), (address, port))
                self.socket.settimeout(current_timeout / 1000)
                response, _ = self.socket.recvfrom(65536)
                return response.decode('utf-8').strip()
            except socket.timeout:
                retries += 1
                current_timeout *= 2
                print(f"Timeout, retry {retries}/{self.max_retries}")
            except Exception as e:
                print(f"Error: {e}")
                break
        raise Exception("Max retries exceeded")

    def download_file(self, filename):
        print(f"\nDownloading: {filename}")
        try:
            # Step 1: Send DOWNLOAD request
            download_msg = f"DOWNLOAD {filename}"
            response = self.send_and_receive(download_msg, self.server_host, self.server_port)

            if response.startswith("ERR"):
                print(f"Error: {response}")
                return False

            parts = response.split()
            if len(parts) < 6 or parts[0] != "OK" or parts[2] != "SIZE" or parts[4] != "PORT":
                print(f"Invalid response: {response}")
                return False

            file_size = int(parts[3])
            data_port = int(parts[5])
            print(f"File size: {file_size} bytes, using port {data_port}")

            # Step 2: Download file blocks
            with open(filename, 'wb') as file:
                bytes_received = 0
                block_size = 1000
                while bytes_received < file_size:
                    start = bytes_received
                    end = min(start + block_size - 1, file_size - 1)
                    request_msg = f"FILE {filename} GET START {start} END {end}"
                    response = self.send_and_receive(request_msg, self.server_host, data_port)

                    # Parse response (split into max 8 parts to protect DATA)
                    parts = response.split(' ', 7)
                    if len(parts) < 8 or parts[0] != "FILE" or parts[2] != "OK":
                        print(f"Invalid block response: {response}")
                        continue

                    base64_data = parts[7]
                    file_data = base64.b64decode(base64_data)
                    file.write(file_data)
                    bytes_received += len(file_data)
                    print("*", end='', flush=True)

                # Step 3: Send CLOSE
                close_msg = f"FILE {filename} CLOSE"
                self.send_and_receive(close_msg, self.server_host, data_port)
                print(f"\nDownload complete: {filename}")

            return True

        except Exception as e:
            print(f"\nDownload failed: {e}")
            return False

    def run(self):
        try:
            with open(self.file_list, 'r', encoding='utf-8') as f:
                files = [line.strip() for line in f if line.strip()]

            for filename in files:
                self.download_file(filename)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python UDPclient.py <hostname> <port> <file_list>")
        sys.exit(1)
    client = UDPClient(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    client.run()
