import socket
import sys
import os
import base64
import time

class UDPClient:
    def __init__(self, hostname, port, file_list):
        # Initialize client with server details and file list
        self.server_host = hostname
        self.server_port = port
        self.file_list = file_list
        # Create UDP socket for communication (Lecture 5: Socket Programming)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.initial_timeout = 1000  # Initial timeout in milliseconds (help for A4: Timeout Setting)
        self.max_retries = 5  # Maximum retries for failed requests

    def send_and_receive(self, message, address, port, timeout=None):
        # Reliable send-receive with timeout and retries (help for A4: Retry Mechanism)
        retries = 0
        current_timeout = timeout if timeout is not None else self.initial_timeout
        
        while retries < self.max_retries:
            try:
                # Send message to specified address and port
                self.socket.sendto(message.encode(), (address, port))
                # Set socket timeout (Lecture 7: UDP Timeout Handling)
                self.socket.settimeout(current_timeout / 1000)
                
                # Receive response with buffer size 65536
                response, _ = self.socket.recvfrom(65536)
                self.socket.settimeout(None)  # Reset timeout
                return response.decode().strip()
                
            except socket.timeout:
                # Handle timeout by doubling timeout and retrying
                retries += 1
                current_timeout *= 2
                print(f"Timeout, retrying {retries}/{self.max_retries} with timeout {current_timeout}ms")
                continue
            except Exception as e:
                # Handle other exceptions
                print(f"Error in send_and_receive: {e}")
                break
                
        raise Exception("Max retries exceeded")

    def download_file(self, filename):
        print(f"\nStarting download of {filename}")
        
        try:
            # Send DOWNLOAD request to server (Protocol specification)
            download_msg = f"DOWNLOAD {filename}"
            response = self.send_and_receive(download_msg, self.server_host, self.server_port)
            
            # Parse server response
            parts = response.split()
            if parts[0] == "ERR":
                # Handle file not found error
                print(f"Error: {response}")
                return False
                
            # Validate OK response format (Protocol specification)
            if parts[0] != "OK" or len(parts) < 6 or parts[2] != "SIZE" or parts[4] != "PORT":
                print(f"Invalid response format: {response}")
                return False
                
            # Extract file size and data port from response
            file_size = int(parts[3])
            data_port = int(parts[5])
            print(f"File size: {file_size} bytes, using port {data_port}")

            # Open local file for binary writing
            with open(filename, 'wb') as file:
                bytes_received = 0
                block_size = 1000  # Request 1000 bytes per block (Protocol specification)
                
                while bytes_received < file_size:
                    # Calculate current block range
                    start = bytes_received
                    end = min(start + block_size - 1, file_size - 1)
                    
                    # Request block from server (Protocol specification)
                    request_msg = f"FILE {filename} GET START {start} END {end}"
                    response = self.send_and_receive(request_msg, self.server_host, data_port)
                    
                    # Validate block response format
                    response_parts = response.split()
                    if (len(response_parts) < 8 or response_parts[0] != "FILE" or 
                        response_parts[2] != "OK" or response_parts[3] != "START" or 
                        response_parts[5] != "END" or response_parts[6] != "DATA"):
                        print(f"Invalid block response: {response}")
                        continue
                        
                    # Extract received block details
                    received_start = int(response_parts[4])
                    received_end = int(response_parts[5])
                    base64_data = ' '.join(response_parts[7:])
                    
                    # Decode Base64 data (help for A4: Base64 Decoding)
                    file_data = base64.b64decode(base64_data)
                    # Write data to file at correct position
                    file.seek(received_start)
                    file.write(file_data)
                    
                    bytes_received += len(file_data)
                    print("*", end='', flush=True)  # Print progress indicator
                
                print(f"\nDownload complete: {bytes_received} bytes received")

            # Send CLOSE request to server (Protocol specification)
            close_msg = f"FILE {filename} CLOSE"
            response = self.send_and_receive(close_msg, self.server_host, data_port)
            
            if response != f"FILE {filename} CLOSE_OK":
                print(f"Unexpected close response: {response}")
                
            return True
            
        except Exception as e:
            print(f"\nError downloading file: {e}")
            return False

    def run(self):
        try:
            # Read file list from specified file
            with open(self.file_list, 'r') as f:
                files = [line.strip() for line in f if line.strip()]
                
            # Download each file in the list
            for filename in files:
                self.download_file(filename)
                
        except FileNotFoundError:
            # Handle file list not found error
            print(f"Error: File list '{self.file_list}' not found")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close socket to release resources (Resource management)
            self.socket.close()

if __name__ == "__main__":
    # Validate command line arguments (Input validation)
    if len(sys.argv) != 4:
        print("Usage: python UDPclient.py <hostname> <port> <file_list>")
        sys.exit(1)

    # Parse command line arguments
    hostname = sys.argv[1]
    port = int(sys.argv[2])
    file_list = sys.argv[3]

    # Create and run client
    client = UDPClient(hostname, port, file_list)
    client.run()
