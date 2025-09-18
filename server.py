import socket
import pickle
import tenseal as ts
from common import SERVER_TMP_PATH
from tqdm import tqdm

# Configuration Constants
HOST = 'localhost'
PORT = 8080
BUFFER_SIZE = 4096

# Store client data temporarily (for potential use)
client_data = {}


def get_server_file_path(name, user_id):
    """
    Get the correct temporary file path for the server.

    Args:
        name (str): The desired file name.
        user_id (str): The current user's ID.

    Returns:
        pathlib.Path: The constructed file path.
    """
    return SERVER_TMP_PATH / f"{name}_{user_id}"


def handle_client_connection(conn, addr):
    """
    Handle incoming client connections and process commands.

    Args:
        conn (socket obj): The connection object to the client.
        addr (tuple): The address of the connected client.
    """
    print(f"Connection established with {addr}")

    # Receive command from the client
    command = conn.recv(BUFFER_SIZE).decode("utf-8")
    command = str(command)

    if command.startswith('INPUT'):
        # Handle receiving input files from the client
        data = command.split("_")
        file_name = data[1]
        user_id = data[2]  # Extract user ID
        file_size = int(data[3])  # Extract file size

        print(f"User ID received: {user_id}")
        print(f"Receiving file {file_name}_{user_id} with size {file_size}...")
        conn.send("Filename received.".encode("utf-8"))

        # Data transfer progress bar setup
        bar = tqdm(
            range(file_size),
            f"Receiving {file_name}_{user_id}",
            unit="B", unit_scale=True, unit_divisor=BUFFER_SIZE
        )

        # Write incoming data to a file on the server
        path = SERVER_TMP_PATH / f"{file_name}_{user_id}"
        with open(path, "wb") as f:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break  # Exit when no more data is received
                f.write(data)
                conn.send("Partial data received...".encode("utf-8"))  # Acknowledge receipt
                bar.update(len(data))  # Update the progress bar

    elif command.startswith('APPLY-FHE-GRAYSCALE'):
        # Handle applying the grayscale operation
        data = command.split("_")
        user_id = data[1]  # Extract user ID
        number_of_channels = int(data[2])  # Extract number of channels

        # Load the public profile context for homomorphic operations
        public_profile_path = get_server_file_path("profile", user_id)
        with public_profile_path.open("rb") as p:
            public_context = ts.context_from(p.read())

        # Prepare output path for the grayscale result
        output_file = get_server_file_path(f"output-0", user_id)
        weighted_results = []  # List to store results of each channel

        for i in range(number_of_channels):
            # Load and process each channel file
            encrypted_image_path = get_server_file_path(f"image-{i}", user_id)
            with encrypted_image_path.open("rb") as f:
                channel_result = []
                while True:
                    try:
                        encrypted_bytes = pickle.load(f)
                        encrypted_vec = ts.ckks_vector_from(public_context, encrypted_bytes)

                        # Apply the weighted grayscale transformation
                        if i == 0:
                            result = encrypted_vec * 0.299  # Red channel weight
                        elif i == 1:
                            result = encrypted_vec * 0.587  # Green channel weight
                        elif i == 2:
                            result = encrypted_vec * 0.114  # Blue channel weight
                            print("Blue: ", encrypted_vec.data)

                        channel_result.append(result)
                    except EOFError:
                        break  # Exit when end of file is reached

                weighted_results.append(channel_result)

        # Combine the channels into a single output by summing the weighted results
        with output_file.open('wb') as out_f:
            for vecs in zip(*weighted_results):
                combined_result = vecs[0] + vecs[1] + vecs[2]  # Sum the weighted channels
                pickle.dump(combined_result.serialize(), out_f)  # Serialize and save

        conn.send("Apply grayscale filter successfully".encode("utf-8"))  # Notify the client

    elif command.startswith('GET-OUTPUT'):
        # Handle sending the processed output back to the client
        data = command.split("_")
        user_id = data[1]  # Extract user ID
        channel_number = 0  # Assuming a single output channel

        file_name = f"output-{channel_number}"
        output_file = get_server_file_path(file_name, user_id)

        print(f"Sending {file_name}_{user_id} to client...")

        # Send the output file in chunks
        with open(output_file, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    conn.send("EOF".encode("utf-8"))  # Send end-of-file signal
                    break  # Exit when the file transfer is complete
                conn.send(data)
                msg = conn.recv(BUFFER_SIZE).decode("utf-8")  # Receive acknowledgment from client
                print(f"CLIENT: {msg}")

        print(f"Transfer of {file_name}_{user_id} completed")


def main():
    """
    Main function to start the server and listen for incoming connections.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()  # Listen for incoming connections
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            # Accept incoming client connections
            conn, addr = server.accept()
            handle_client_connection(conn, addr)  # Handle each client connection


if __name__ == "__main__":
    main()  # Run the server
