import socket
import sys
import os
# Functions that handle client requests
def process_requests(server_host, server_port, request_file):
    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket. SOCK_STREAM)
    try:
        # Connect to the server
        client_socket.connect((server_host, server_port))
        with open(request_file, 'r') as file:
          
            for line in file:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(' ')
                command = parts[0]
                key = parts[1]
                value = parts[2] if len(parts) == 3 else ''
                # Check the length of the request string
                if len(key + ' ' + value) > 970:
                    print(f"Error: Request size exceeds limit for {line}")
                    continue
                # Build the request message
                msg = f"{str(len(line) + 3).zfill(3)}{command} {key}"
                if command == 'P':
                    msg += f" {value}"
                # Send a request message
                client_socket.send(msg.encode('utf-8'))
                # Receive a server response
                response = client_socket.recv(1024).decode('utf-8')
                print(f"{line}: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()


# Main function, start the client
def main():
    # Check the command line arguments, now all you need is the server host, port, and directory path
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <directory_path>")
        return
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    directory_path = sys.argv[3]

    # Check if the directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: The specified directory {directory_path} does not exist.")
        return

    # Get all .txt files in the directory
    txt_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.txt')]

    # Process each .txt file
    for txt_file in txt_files:
        print(f"Processing file: {txt_file}")
        process_requests(server_host, server_port, txt_file)


if __name__ == "__main__":
    main()



