import os
import socket
import threading

LOG_FILE = "download.log"

# Initialize paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
FRAGMENTS_DIR = os.path.join(FILES_DIR, "fragments")


# Read server IPs and ports from servers.txt
def discover_servers():
    servers = []
    with open("servers.txt", "r") as f:
        for line in f:
            ip, port = line.strip().split(":")
            servers.append((ip, int(port)))
    return servers


# Log successfully downloaded fragment
def log_progress(fragment_name):
    with open(LOG_FILE, "a") as log:
        log.write(f"{fragment_name}\n")


# Get downloaded fragments from log
def read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as log:
            return set(line.strip() for line in log)
    return set()


# Combine fragments into a single file
def combine_fragments(file_name, output_dir):
    base_name, extension = os.path.splitext(file_name)
    output_file = os.path.join(output_dir, file_name)
    with open(output_file, "wb") as outfile:
        fragment_number = 0
        while True:
            fragment_file = os.path.join(FRAGMENTS_DIR, f"{base_name}{fragment_number}{extension}")
            if not os.path.exists(fragment_file):
                break
            with open(fragment_file, "rb") as frag:
                outfile.write(frag.read())
            fragment_number += 1
    print(f"File '{file_name}' has been successfully combined.")


# Delete the fragment files and log upon completion
def cleanup():
    # Delete all fragment files
    for fragment_file in os.listdir(FRAGMENTS_DIR):
        fragment_path = os.path.join(FRAGMENTS_DIR, fragment_file)
        os.remove(fragment_path)

    # Delete the log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    print("Cleaned up fragment files and log.")


# Download a fragment from the server
def download_fragment(file_name, fragment_number, servers, completed_fragments, start_server_idx):
    base_name, extension = os.path.splitext(file_name)
    fragment_name = f"{base_name}{fragment_number}{extension}"
    fragment_path = os.path.join(FRAGMENTS_DIR, fragment_name)

    num_servers = len(servers)
    for i in range(num_servers):
        server_idx = (start_server_idx + i) % num_servers
        server_ip, port = servers[server_idx]

        try:
            # Send TCP requests to server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((server_ip, port))
                client_socket.sendall(f"{file_name},{fragment_number}".encode())

                # Handle server response
                response = client_socket.recv(1024)
                if response == b"BUSY":
                    print(f"Server {server_ip}:{port} is busy. Trying next server...")
                    continue
                elif response == b"ALL_FRAGMENTS_OBTAINED":
                    # If the server has no more fragments, stop downloading
                    return True

                # Receive fragment
                with open(fragment_path, "wb") as f:
                    f.write(response)
                    while (chunk := client_socket.recv(1024)):
                        f.write(chunk)
                log_progress(fragment_name)
                print(f"Downloaded {fragment_name} from {server_ip}:{port}.")
                completed_fragments.add(fragment_name)
                return False
        except Exception as e:
            print(f"Error downloading {fragment_name} from {server_ip}:{port}: {e}")

    print(f"Failed to download {fragment_name}. No servers available.")
    return False


# Threaded function to handle fragment downloads
def download_file(file_name, servers, completed_fragments):
    base_name, extension = os.path.splitext(file_name)
    fragment_number = 0
    start_server_idx = 0

    # Try downloading fragments in a round-robin style
    while True:
        fragment_name = f"{base_name}{fragment_number}{extension}"
        if fragment_name in completed_fragments:
            fragment_number += 1
            continue

        # Start a new thread to download the fragment
        all_fragments_obtained = download_fragment(file_name, fragment_number, servers, completed_fragments,
                                                   start_server_idx)

        if all_fragments_obtained:
            print(f"All fragments for {file_name} have been obtained.")
            break

        fragment_number += 1

    combine_fragments(file_name, FILES_DIR)
    cleanup()  # Cleanup after the download is completed


def download_file_threaded(file_name):
    completed_fragments = read_log()
    servers = discover_servers()

    # Start a new thread to download the file
    download_thread = threading.Thread(target=download_file, args=(file_name, servers, completed_fragments))
    download_thread.start()
    download_thread.join()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="Name of the file to download")
    args = parser.parse_args()

    download_file_threaded(args.file_name)
