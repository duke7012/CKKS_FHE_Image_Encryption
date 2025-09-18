# Image Filtering on Encrypted Data using Fully Homomorphic Encryption

## Project Overview

The project implements a secure image processing system leveraging Fully Homomorphic Encryption (FHE) to filter and apply operations on images without exposing the image data. This innovative approach uses [TenSEAL](https://github.com/OpenMined/TenSEAL) for FHE and is showcased via a Gradio-based web interface.

### Key Files in the Project:

- **main.py**: The primary script containing the Gradio interface for image encryption, decryption, and interaction with the server.
- **interface.py**: Defines the `Client` class responsible for creating and managing encrypted data, as well as key serialization and deserialization.
- **common.py**: Includes shared constants and utility functions, such as paths for temporary directories and other configurations.
- **server.py**: Contains the server-side logic for receiving encrypted images, applying transformations (like grayscale filtering), and returning the processed encrypted results.

## Encryption Scheme with TenSEAL

The project uses the TenSEAL library to implement the CKKS scheme, which allows encrypted data to be manipulated without decryption. This provides a significant privacy advantage, as image data remains encrypted during processing, even on the server side. The project showcases how images can be encrypted, transferred to a server, processed (e.g., grayscale transformation), and returned in an encrypted format.

### Grayscale Image Processing Explained

The grayscale filter is applied by calculating the weighted sum of the RGB channels using the following formula:

- `Gray = 0.299 * Red + 0.587 * Green + 0.114 * Blue`

In this project, each RGB channel is encrypted, transferred to the server, and weighted individually using homomorphic operations. The server processes these encrypted channels, computes the weighted sum homomorphically, and returns the final encrypted result to the client.

## Getting Started

### Prerequisites

- Python 3.8+
- **Gradio**: Install via `pip install gradio`
- **TenSEAL**: Follow the [installation instructions](https://github.com/OpenMined/TenSEAL) on their GitHub page.
- **Uvicorn**: Install via `pip install uvicorn`

### Installation

1. Clone the repository and navigate to the project folder.
2. Install the required dependencies by running:
    ```bash
    pip install -r requirements.txt
    ```

I didn't include those steps previously. Here's an updated version of the "Running the App" section in the `README.md` with these instructions:

---

## Running the App

To run the app, you need to start the server and the Gradio interface in separate terminals:

1. **Start the Server**:
    - Open a terminal and run the following command to ensure that port 8080 is not already in use:
        ```bash
        sudo lsof -i :8080
        ```
    - If port 8080 is in use, close the process or choose a different port in the code.
    - Start the server:
        ```bash
        python3 server.py
        ```

2. **Launch the Gradio Interface**:
    - Open another terminal and navigate to the project directory.
    - Run the Gradio app:
        ```bash
        python3 app.py
        ```

3. **Access the App**:
    - Open the provided link in your browser to interact with the image filtering application.

## Interacting with the Website

1. **Upload Image**: Start by uploading any type of image (PNG, JPG, etc.). The system supports all standard image formats.
2. **Encrypt and Process**: The app encrypts the uploaded image using the CKKS encryption scheme provided by TenSEAL and sends it to the server for grayscale processing.
3. **Apply Grayscale**: The server homomorphically applies the grayscale filter and returns the processed, encrypted result to the client.
4. **Decrypt and View**: The client decrypts the processed image, which is then displayed for the user to view.

### Features:

- **Support for All Image Types**: The system can process a variety of image formats efficiently, making it versatile for different use cases.
- **Efficient Processing**: While working with FHE can be computationally intensive, the project is optimized to process and return results within a reasonable timeframe.
- **End-to-End Encryption**: The entire image processing workflow—encryption, server transfer, grayscale operation, and decryption—is done securely using FHE, ensuring privacy at every stage.

## How the Encryption Scheme Works

### CKKS Encryption Scheme:

- **Client-Side Encryption**: The `Client` class creates a TenSEAL context and encrypts the image channels using the CKKS scheme. The context is initialized with a polynomial modulus degree and coefficient modulus bit sizes for secure encryption.
- **Server Processing**: Encrypted image data is transferred to the server, which processes the data using the CKKS scheme. The server applies homomorphic multiplication to the encrypted channels to compute the grayscale transformation.
- **Encrypted Result**: The processed image data remains encrypted when sent back to the client, ensuring that no sensitive information is exposed at any point.
- **Decryption and Display**: The client decrypts the received data and reconstructs the grayscale image, which is then displayed for the user.

## Project Structure

- **main.py**: Main script for running the Gradio app.
- **interface.py**: Class definitions for client operations, key management, and data serialization.
- **common.py**: Shared constants and utility functions for paths and configurations.
- **server.py**: Server logic to handle incoming encrypted data, apply grayscale transformations, and send results.

## Acknowledgements

- **[Gradio](https://www.gradio.app/)** for providing an easy-to-use UI framework for deploying machine learning models.
- **[TenSEAL](https://github.com/OpenMined/TenSEAL)** for their invaluable tools in implementing FHE and promoting privacy-preserving machine learning solutions.

---