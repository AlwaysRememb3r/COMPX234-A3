import socket
import threading
import time
# Functions that handle client requests
def handle_client(client_socket, client_address):
    global tuple_space, total_clients, total_operations, total_reads, total_gets, total_puts, total_errors
    total_clients += 1

    try:
        while True:
           #Use client_socket.recv(1024) to receive the message sent by the client, with a maximum reception of 1024 bytes.
            data = client_socket.recv(1024).decode('utf-8') #decode('utf-8') decodes the received byte data into a string.
            if not data:
                break #If no data is received, break out of the loop.
      
            msg_size = int(data[:3]) #msg_size: The total length of the message, parsed from the first 3 characters of the message.
            command = data[3] #command: The operation command, obtained from the 4th character of the message. It can be R (read), G (get and remove), or P (put).
            key = data[4:msg_size - 1] if command != 'P' else data[4:msg_size - len(data.split(' ')[-1]) - 2]
            #key: The key. Different truncations are made according to different commands.
            value = data.split(' ')[-1] if command == 'P' else ''
            #value: The value, which only exists when the command is P.
            response = ''
            total_operations += 1 #total_operations is incremented by 1, indicating that one operation has been processed.
            if command == 'R':#R: Read operation. If the key exists, return the corresponding value; otherwise, return an error message.
                total_reads += 1
                if key in tuple_space:
                    response = f"{msg_size} OK ({key}, {tuple_space[key]}) read"
                else:
                    total_errors += 1
                    response = f"{msg_size} ERR {key} does not exist"
            elif command == 'G':#G: Get and remove operation. If the key exists, remove the key - value pair and return the removed value; otherwise, return an error message.
                total_gets += 1
                if key in tuple_space:
                    value = tuple_space.pop(key)
                    response = f"{msg_size} OK ({key}, {value}) removed"
                else:
                    total_errors += 1
                    response = f"{msg_size} ERR {key} does not exist"
            elif command == 'P':#P: Put operation. If the key already exists, return an error message; otherwise, put the key - value pair into the tuple space.
                total_puts += 1
                if key in tuple_space:
                    total_errors += 1
                    response = f"{msg_size} ERR {key} already exists"
                else:
                    tuple_space[key] = value
                    response = f"{msg_size} OK ({key}, {value}) added"

            client_socket.send(response.encode('utf-8')) #Encode the response message into byte data and send it to the client.
    except Exception as e:
        total_errors += 1
        print(f"Error handling client {client_address}: {e}") 
      #If an exception occurs while handling the client request, total_errors is incremented by 1, and an error message is printed.
    finally:
        client_socket.close()
      #Whether an exception occurs or not, finally close the socket connection with the client

# A function that prints tuple space information periodically
 def print_tuple_space_summary():
    global tuple_space, total_clients, total_operations, total_reads, total_gets, total_puts, total_errors
    while True:
        time.sleep(10) 
        #Pausing the program for 10 seconds means that subsequent statistics and printing operations are performed every 10 seconds.
        tuple_count = len(tuple_space)
       # Gets the number of key-value pairs in the tuple space.
        if tuple_count == 0:
            avg_tuple_size = 0
            avg_key_size = 0
            avg_value_size = 0
        else:
            total_tuple_size = sum(len(key) + len(value) for key, value in tuple_space.items())
            #The sum function and generator expressions calculate the total length of all key-value pairs
            total_key_size = sum(len(key) for key in tuple_space.keys())
            #Calculate the total length of all keys
            total_value_size = sum(len(value) for value in tuple_space.values())
            #Calculate the total length of all value
            avg_tuple_size = total_tuple_size / tuple_count
            avg_key_size = total_key_size / tuple_count
            avg_value_size = total_value_size / tuple_count
            #The average tuple size, average key size, and average size are calculated separately, i.e., the total length divided by the number of tuples

        print(f"Tuple Space Summary:")
        print(f"Number of tuples: {tuple_count}")
        print(f"Average tuple size: {avg_tuple_size}")
        print(f"Average key size: {avg_key_size}")
        print(f"Average value size: {avg_value_size}")
        print(f"Total clients: {total_clients}")
        print(f"Total operations: {total_operations}")
        print(f"Total READs: {total_reads}")
        print(f"Total GETs: {total_gets}")
        print(f"Total PUTs: {total_puts}")
        print(f"Total errors: {total_errors}")
        #The f-string is used to format the statistics of the output tuple space, which is convenient to view the status and operation of the tuple space
   # Main function, start the server     
def start_server():
    global tuple_space, total_clients, total_operations, total_reads, total_gets, total_puts, total_errors
    tuple_space = {}
    total_clients = 0
    total_operations = 0
    total_reads = 0
    total_gets = 0
    total_puts = 0
    total_errors = 0

    # This condition determines whether the number of command-line arguments is 2 (script name and port number). 
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        return
    port = int(sys.argv[1])
   # Then check if the port number is in the range of 50000 to 59999
    if not 50000 <= port <= 59999:
        print("Port number should be between 50000 and 59999")
        return
# Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket. SOCK_STREAM)
    # Set socket options to allow address reuse
    server_socket.setsockopt(socket. SOL_SOCKET, socket. SO_REUSEADDR, 1)
    # To bind the address and port, here we use the idea of bind in the lecture
    server_socket.bind(('localhost', port))
    # Start listening for the connection, corresponding to the listen in the lecture
    server_socket.listen(5)
    print(f"Server is running on port {port}, waiting for clients...")

    # Start the thread that prints the tuple space information
    summary_thread = threading. Thread(target=print_tuple_space_summary)
    summary_thread.daemon = True
    summary_thread.start()
while True:
        # Accept client connections
        client_socket, client_address = server_socket.accept()
        # Create a new thread for each client to process the request
        client_thread = threading. Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()


if __name__ == "__main__":
    start_server()

