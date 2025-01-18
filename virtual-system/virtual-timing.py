import socket
import random

# Server configuration
HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 65432      # Port to bind to

def generate_random_time():
    """Generate a random time between 2.00 and 5.00 seconds."""
    time = round(random.uniform(2.00, 5.00), 3)
    return (f"{time} sec") 

def main():
    print(f"Starting simulation server on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(3)
        print("Server is listening for incoming connections...")

        while True:
        # Wait for a client connection
            client_socket, client_address = server_socket.accept()
            amountOfData = 0
            with client_socket:
                print(f"Connected by {client_address}")
            
            # Start receiving data from the client only after a connection is made
                while True:
                    data = client_socket.recv(1024).decode()  # Wait for data from the client
                        
                        # Check if no data was received, but don't close the connection
                    if not data:
                        # This is a safeguard, but in this case, we are just keeping the connection alive
                        print("No data received yet, waiting for command...")
                        break
                        # Decode the data and check if it matches the "start" command
                    elif data and amountOfData == 0:
                        print("waiting for the start command from the client")
                        amountOfData += 1
                    elif data == "start":
                            print("Start command received. Beginning simulation....")
                            while True:
                                simulated_time = generate_random_time()
                                client_socket.send(f"{simulated_time}\n".encode())
                                print(f"Sent: READY: {simulated_time}")
                                amountOfData += 1
                                data = ""
                                break
                        # If an unknown command is received, log it and keep waiting
                    else:
                            print(f"Received unknown command: {data}")
                    
                print("Server shutting down...")
                amountOfData = 0

if __name__ == "__main__":
    main()