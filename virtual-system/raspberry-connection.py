import socket

# Server details
PI_IP = "192.168.x.x"  # Replace with your Raspberry Pi's IP address
PORT = 65432

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((PI_IP, PORT))
        print("Connected to Raspberry Pi server.")

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode().strip()}")
        except KeyboardInterrupt:
            print("Closing connection.")
        finally:
            client_socket.close()

if __name__ == "__main__":
    main()
