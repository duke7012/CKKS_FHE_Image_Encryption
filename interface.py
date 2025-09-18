import tenseal as ts
import numpy as np
import pickle


class Client:
    """
    Client interface for encrypting and decrypting FHE data with TenSEAL.
    """

    def __init__(self, user_id):
        """
        Initialize the client with a TenSEAL context.

        Args:
            user_id (int): The unique identifier for the user.
        """
        self.user_id = user_id

        # Create a CKKS context for FHE with specific parameters.
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,  # Sets the polynomial modulus degree.
            coeff_mod_bit_sizes=[60, 40, 40, 60]  # Coefficient modulus bit sizes for encryption security.
        )

        # Save the public context for use on the server side (without secret keys).
        self.public_profile = self.context.copy()
        self.public_profile.make_context_public()  # Remove secret key to make it public.

        # Set the scale for the CKKS scheme.
        self.context.global_scale = 2 ** 40

        # Generate Galois keys for operations such as rotations.
        self.context.generate_galois_keys()

    def get_public_profile(self):
        """
        Serialize and return the public profile for server-side use.

        Returns:
            bytes: Serialized public profile of the client.
        """
        return self.public_profile.serialize()

    def get_private_profile(self):
        """
        Serialize and return the full context, including the secret key.

        Returns:
            bytes: Serialized private profile of the client.
        """
        return self.context.serialize()

    def deserialize_decrypt_post_process(self, grayscale_encrypted_path, image_height, image_width):
        """
        Deserialize, decrypt, and post-process the grayscale image.

        Args:
            grayscale_encrypted_path (pathlib.Path): Path to the file containing encrypted grayscale data.
            image_height (int): The height of the image.
            image_width (int): The width of the image.

        Returns:
            numpy.ndarray: The decrypted and processed grayscale image.
        """
        decrypted_image = []  # List to store decrypted segments of the image.

        # Open the encrypted file and load each encrypted segment for decryption.
        with grayscale_encrypted_path.open('rb') as f:
            while True:
                try:
                    # Load and deserialize the encrypted data.
                    encrypted_bytes = pickle.load(f)
                    encrypted_vec = ts.ckks_vector_from(self.context, encrypted_bytes)

                    # Decrypt the data and reshape it to match the image dimensions.
                    decrypted_segment = np.array(encrypted_vec.decrypt(self.context.secret_key())).reshape(image_height,
                                                                                                           image_width)
                    decrypted_image.append(decrypted_segment)  # Append the decrypted segment to the list.
                except EOFError:
                    break  # Exit the loop when the end of the file is reached.

        # Combine all decrypted segments to form the full image.
        decrypted_image = np.concatenate(decrypted_image, axis=0)

        # Convert the image data type to uint8 for proper image representation (0-255 range).
        decrypted_image = decrypted_image.astype(np.uint8)

        return decrypted_image  # Return the final decrypted image array.
