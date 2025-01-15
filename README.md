# File Download System

This project allows clients to download large files from multiple servers simultaneously. The file is segmented into smaller fragments and distributed across the servers. The client then downloads each fragment, combines them, and deletes the temporary files.

## Client Operation

1. **Setup Servers:**
   - A `servers.txt` file is manually set up to list all available servers and their respective port numbers.

2. **Download a File:**
   - To download a file from the client, run the following command:
     ```bash
     python client.py {file_name}
     ```
   - The client will handle the entire process of downloading the file by fetching its fragments.

3. **Resuming Downloads:**
   - The client reads a log file to check which fragments have already been downloaded in case the download was paused. It then continues from the next undownloaded fragment.

4. **Round-Robin Fragment Requests:**
   - The client uses a round-robin approach to request fragments from servers listed in `servers.txt`.
   - If a server is busy, the client moves to the next one. If all servers are busy, the client waits briefly before retrying.

5. **Simultaneous Downloads:**
   - For each fragment, a new thread is created to download the next fragment concurrently, allowing simultaneous downloads.

6. **Completion:**
   - The download stops once the client receives a message indicating that all fragments have been obtained.

7. **Combining Fragments:**
   - After downloading all fragments, the client combines them into a single file and deletes the fragments. The log file is also erased.

## Server Operation

1. **Uploading Files:**
   - Upload the files you want to make available for clients to the `files` directory in the server folder. This step is done manually.

2. **Starting the Server:**
   - Start a server by running the following command:
     ```bash
     python server.py {port_number}
     ```
   - The server will be active and listening for incoming requests.

3. **Fragmenting Files:**
   - Upon startup, the server checks if the files in the `files` directory have been fragmented into the `files/fragments` directory.
   - If not, the server will split the files into 100 MB fragments and name them `{file_name}{fragment_number}{extension}`.

4. **Handling Requests:**
   - The server listens for incoming requests and receives the file name and fragment number.
   - If the server is busy, it sends a "busy" message back to the client. If the requested fragment exists, it sends the fragment. If the file does not exist, an error message is sent.
   
5. **All Fragments Obtained:**
   - If the requested fragment number exceeds the total number of fragments, the server sends a message to the client stating that all fragments have been obtained.

## Notes

- **File Fragmentation:** Files are split into 100 MB fragments to enable efficient distribution across multiple servers.
- **Multithreading:** The client uses multiple threads to download file fragments concurrently for better performance.
- **Server Load Balancing:** Servers are accessed in a round-robin manner to ensure load balancing across multiple servers.
