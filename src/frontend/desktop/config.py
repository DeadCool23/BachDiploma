import os
import dotenv
from pathlib import Path

dotenv.load_dotenv()

API_URL = f"http://{os.getenv('API_HOST')}:{os.getenv('API_PORT')}"
WINDOW_SIZE = "950x500"