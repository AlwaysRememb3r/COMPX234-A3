import socket
import threading
import time
def handle_client(client_socket, client_address):
    global tuple_space, total_clients, total_operations, total_reads, total_gets, total_puts, total_errors
    total_clients += 1

    try:
        while True:
           #Use client_socket.recv(1024) to receive the message sent by the client, with a maximum reception of 1024 bytes.
            data = client_socket.recv(1024).decode('utf-8') #decode('utf-8') decodes the received byte data into a string.
            if not data:
                break #If no data is received, break out of the loop.
      
            msg_size = int(data[:3])
            command = data[3]
            key = data[4:msg_size - 1] if command != 'P' else data[4:msg_size - len(data.split(' ')[-1]) - 2]
            value = data.split(' ')[-1] if command == 'P' else ''

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
      #Whether an exception occurs or not, finally close the socket connection with the client.
