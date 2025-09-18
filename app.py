import os
import socket
import numpy as np
import pickle
from PIL import Image
from common import CLIENT_TMP_PATH, SERVER_TMP_PATH, CURRENT_CLIENT, USER_ID
import gradio as gr
import tenseal as ts
import shutil
from tqdm import tqdm

# Configuration Constants
HOST = 'localhost'
PORT = 8080
BUFFER_SIZE = 4096


# =============== HELPER FUNCTIONS =================
def get_client_file_path(name, user_id, extension=""):
    """
    Construct a file path for client-side temporary storage.

    Args:
        name (str): Base name for the file.
        user_id (int): User identifier.
        extension (str): File extension.

    Returns:
        pathlib.Path: The constructed file path.
    """
    return CLIENT_TMP_PATH / f"{name}_{user_id}{extension}"


def save_bytes_to_file(bytes_seq, seq_name, user_id, extension=""):
    """
    Save a sequence of bytes to a file at a specific path.

    Args:
        bytes_seq (bytes): Byte sequence to be saved.
        seq_name (str): Name of the file.
        user_id (int): User identifier.
        extension (str): File extension.
    """
    file_path = get_client_file_path(seq_name, user_id, extension)
    file_path.open("wb").write(bytes_seq)  # Write the bytes to the file.


def send_command(command):
    """
    Send a command to the server and receive its response.

    Args:
        command (bytes): Command to send.

    Returns:
        str: Response from the server.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))  # Connect to the server.
        s.send(command)  # Send the command.
        response = s.recv(BUFFER_SIZE).decode("utf-8")  # Receive the response.
        return response


def clean_temporary_files():
    """
    Delete files in CLIENT_TMP_PATH and SERVER_TMP_PATH without
    removing the directories themselves.
    """
    for directory in [CLIENT_TMP_PATH, SERVER_TMP_PATH]:
        if directory.exists() and directory.is_dir():
            for item in directory.iterdir():  # Iterate over directory contents.
                if item.is_file():
                    item.unlink()  # Remove file.
                elif item.is_dir():
                    shutil.rmtree(item)  # Remove subdirectory.
            print(f"Files in {directory.name} cleaned successfully.")
        else:
            print(f"Directory {directory.name} does not exist.")


# ============ FUNCTION USED IN INTERFACE ================
def encrypt_image(image):
    """
    Encrypt the input image using FHE and save it for transmission.

    Args:
        image (numpy.ndarray): Image to encrypt.

    Returns:
        tuple: Metadata about the encryption and a status message.
    """
    client = CURRENT_CLIENT
    user_id = USER_ID

    serialized_public_profile = client.get_public_profile()
    save_bytes_to_file(serialized_public_profile, "profile", user_id)  # Save the public profile.
    print("Client public profile generated!")

    image_array = np.array(Image.fromarray(image), dtype=np.float32)  # Convert image to array.

    # Validate image has 3 channels (RGB).
    if image_array.shape[-1] != 3:
        raise ValueError(f"Input image must have 3 channels (RGB). Current shape: {image_array.shape}")

    # Encrypt and save each channel separately.
    for i in range(image_array.shape[-1]):
        output_file = get_client_file_path(f"image-{i}", user_id)
        with open(output_file, 'wb') as f:
            channel = ts.ckks_vector(client.context, image_array[:, :, i].flatten().tolist())
            pickle.dump(channel.serialize(), f)  # Serialize and save encrypted channel.

    print("Image encrypted!")

    # Send encrypted files to the server.
    try:
        for i in range(image_array.shape[-1] + 1):
            file_name = "profile" if i == image_array.shape[-1] else f"image-{i}"

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                print(f"Sending {file_name}_{user_id} to server...")

                file_path = get_client_file_path(file_name, USER_ID)
                file_size = os.path.getsize(file_path)
                s.send(f"INPUT_{file_name}_{user_id}_{file_size}".encode("utf-8"))

                msg = s.recv(BUFFER_SIZE).decode("utf-8")
                print(f"SERVER: {msg}")

                # Transfer file data in chunks.
                bar = tqdm(range(file_size), f"Sending {file_name}", unit="B", unit_scale=True,
                           unit_divisor=BUFFER_SIZE)
                with open(file_path, "rb") as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        s.send(data)
                        msg = s.recv(BUFFER_SIZE).decode("utf-8")
                        print(f"SERVER: {msg}")
                        bar.update(len(data))

    except BrokenPipeError:
        print("Failed to send data to server.")

    return (user_id, image, image_array.shape[0], image_array.shape[1], image_array.shape[-1],
            f"Encryption completed (into {image_array.shape[-1]} files). Data sent to server.")


def apply_fhe_grayscale(user_id, number_of_channels):
    """
    Request the server to apply FHE-based grayscale to the encrypted image.

    Args:
        user_id (int): User identifier.
        number_of_channels (int): Number of channels in the image.

    Returns:
        str: Server response after applying grayscale.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(f'APPLY-FHE-GRAYSCALE_{user_id}_{number_of_channels}'.encode("utf-8"))
        return s.recv(BUFFER_SIZE).decode("utf-8")  # Receive response.


def retrieve_server_output(user_id, number_of_channels):
    """
    Retrieve the processed output from the server.

    Args:
        user_id (int): User identifier.
        number_of_channels (str): Number of channels in the image.

    Returns:
        str: Status message indicating retrieval success.
    """
    for channel_number in range(int(number_of_channels)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.send(f'GET-OUTPUT_{user_id}_{channel_number}'.encode("utf-8"))

            path = get_client_file_path(f"output-{channel_number}", user_id)
            with open(path, "wb") as f:
                while True:
                    data = s.recv(BUFFER_SIZE)
                    if not data or data == b'EOF':
                        break
                    f.write(data)
                    s.send("Partial data received...".encode("utf-8"))

            print("Retrieved encrypted output from server.")

    return "Retrieved encrypted output from server."


def decrypt_output(user_id, height, width):
    """
    Decrypt the output and reconstruct the image.

    Args:
        user_id (int): User identifier.
        height (str): Image height.
        width (str): Image width.

    Returns:
        numpy.ndarray: Decrypted image array.
    """
    channel_encrypted = get_client_file_path("output-0", user_id)
    decrypted_output = CURRENT_CLIENT.deserialize_decrypt_post_process(
        channel_encrypted, int(height), int(width)  # Decrypt and process the output.
    )
    return decrypted_output  # Return the decrypted image.


# Create Gradio Interface
interface = gr.Blocks()
with interface:
    gr.Markdown('<h1 align="center">Image Filtering On Encrypted Data Using Fully Homomorphic Encryption</h1>')

    # Step 1: Upload an image
    gr.Markdown("## Step 1: Upload an image")
    input_image = gr.Image(value=None, label="Upload an image here.", height=256, width=256, interactive=True)

    curr_user_id = gr.Textbox(label="user_id", max_lines=2, interactive=False, visible=False)
    channel_count = gr.Textbox(label="channel_count", max_lines=2, interactive=False, visible=False)
    img_width = gr.Textbox(label="image_width", max_lines=2, interactive=False, visible=False)
    img_height = gr.Textbox(label="image_height", max_lines=2, interactive=False, visible=False)

    # Step 2: Image Encryption
    gr.Markdown("## Step 2: Generate client profile and encrypt the image using FHE scheme")
    encrypt_button = gr.Button("Encrypt the image")
    encrypted_output = gr.Textbox(label="Encrypted image:", max_lines=12, interactive=False)

    # Step 3: Apply FHE Grayscale
    gr.Markdown("## Step 3: Apply gray-scaling algorithm on the encrypted image using FHE")
    apply_grayscale_button = gr.Button("Apply")
    execution_time = gr.Textbox(label="Execution status:", max_lines=1, interactive=False)

    # Step 4: Receive ciphertext
    gr.Markdown("### Step 4: Receive ciphertext")
    receive_button = gr.Button("Retrieve ciphertext from server")
    server_ciphertext = gr.Textbox(label="Ciphertext received from server:", max_lines=12, interactive=False)

    # Step 5: Decrypt the ciphertext
    gr.Markdown("### Step 5: Decrypt the ciphertext")
    decrypt_button = gr.Button("Decrypt")
    original_image = gr.Image(input_image.value, label=f"Input image:", interactive=False, height=256, width=256)
    output_image = gr.Image(label=f"Output image:", interactive=False, height=256, width=256)

    # Connect Gradio elements to Python functions
    encrypt_button.click(
        encrypt_image,
        inputs=[input_image],
        outputs=[curr_user_id, original_image, img_height, img_width, channel_count, encrypted_output]
    )

    apply_grayscale_button.click(
        apply_fhe_grayscale,
        inputs=[curr_user_id, channel_count],
        outputs=[execution_time]
    )

    receive_button.click(
        retrieve_server_output,
        inputs=[curr_user_id, channel_count],
        outputs=[server_ciphertext]
    )

    decrypt_button.click(
        decrypt_output,
        inputs=[curr_user_id, img_height, img_width],
        outputs=[output_image]
    )

if __name__ == "__main__":
    clean_temporary_files()  # Clean temporary files before launching.
    interface.launch()  # Launch the Gradio interface.
