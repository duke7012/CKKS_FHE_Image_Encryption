"""
All the constants used in this repo.
"""
from pathlib import Path
import random
from interface import Client

# This repository's directory
REPO_DIR = Path(__file__).parent
TEMP_DIR = REPO_DIR / "temp"
CLIENT_TMP_PATH = TEMP_DIR / "client_tmp"
SERVER_TMP_PATH = TEMP_DIR / "server_tmp"

# The input images' shape. Images with different input shapes will be cropped and resized by Gradio
# CURRENT_CLIENT = None
IMAGE_SIZE = None

# Create an ID for the current user
USER_ID = random.randint(0, 2 ** 32)

# Retrieve the client API
client = Client(USER_ID)
CURRENT_CLIENT = client

# Store the server's URL
SERVER_URL = "http://localhost:5000/"

# Create the necessary folders
TEMP_DIR.mkdir(exist_ok=True)
CLIENT_TMP_PATH.mkdir(exist_ok=True)
SERVER_TMP_PATH.mkdir(exist_ok=True)
