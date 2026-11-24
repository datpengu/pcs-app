from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "people_counter.sqlite3"

# Camera settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Detection settings
MODEL_NAME = "yolo11n.pt"
CONFIDENCE = 0.25

# Tracking settings
TRACK_BUFFER = 60

# Counting settings
LINE_POSITION = 0.50
LINE_MARGIN = 20
CONFIRMATION_FRAMES = 3
