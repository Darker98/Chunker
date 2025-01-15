import os
import socket
import threading

# Initialize paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
FRAGMENTS_DIR = os.path.join(FILES_DIR, "fragments")

# Setup for fragmentation
CHUNK_SIZE = 100 * 1024 * 1024  # 100 MB
os.makedirs(FRAGMENTS_DIR, exist_ok=True)

# Initialize variables for when server is busy
busy = False
lock = threading.Lock()

# Fragment file into 100 MB fragments
def fragment_file(file_path):
    file_name = os.path.basename(file_path)
    base_name, extension = os.path.splitext(file_name)  # Parse file name and extension
    fragment_prefix = os.path.join(FRAGMENTS_DIR, base_name)

    with open(file_path, 'rb') as f:
        fragment_number = 0
        while (chunk := f.read(CHUNK_SIZE)):
            fragment_file_name = f"{fragment_prefix}{fragment_number}{extension}"
            with open(fragment_file_name, 'wb') as frag:
                frag.write(chunk)
            fragment_number += 1

    print(f"File '{file_name}' fragmented into {fragment_number} parts.")

# Check for files that need to be fragmented
def check_and_fragment_files():
    # Check for unfragmented files in the 'files' directory
    for file_name in os.listdir(FILES_DIR):
        file_path = os.path.join(FILES_DIR, file_name)
        if os.path.isfile(file_path):
            base_name, extension = os.path.splitext(file_name)
            fragment_prefix = os.path.join(FRAGMENTS_DIR, base_name)
            if not any(f.startswith(fragment_prefix) for f in os.listdir(FRAGMENTS_DIR)):
                fragment_file(file_path)

# Handle client requests
def handle_client(client_socket):
    global busy
    with lock:
        if busy:
            # Send busy message if server is occupied
            client_socket.sendall(b"BUSY")
            client_socket.close()
            return
        busy = True

    try:
        # Receive file name and fragment number
        request = client_socket.recv(1024).decode()
        file_name, fragment_number = request.split(',')
        fragment_number = int(fragment_number)

        # Locate and send fragment
        base_name, extension = os.path.splitext(file_name)
        fragment_path = os.path.join(FRAGMENTS_DIR, f"{base_name}{fragment_number}{extension}")
        if os.path.exists(fragment_path):
            with open(fragment_path, 'rb') as f:
                while (chunk := f.read(1024)):
                    client_socket.sendall(chunk)
            print(f"Sent fragment {fragment_number} of {file_name} to client.")
        else:
            # Send a message if all fragments are obtained
            client_socket.sendall(b"ALL_FRAGMENTS_OBTAINED")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        busy = False
        client_socket.close()

# Start server and listen for client connections
def start_server(port):
    check_and_fragment_files()

    # Setup socket to listen to TCP requests
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    print(f"Server started on port {port}. Waiting for requests...")

    # Accept and handle client connections
    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="Port number for the server")
    args = parser.parse_args()

    start_server(args.port)
