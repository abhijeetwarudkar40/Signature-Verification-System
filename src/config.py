from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset" / "cedar"

MODELS_DIR = PROJECT_ROOT / "models"
CEDAR_MODELS_DIR = MODELS_DIR / "cedar"
USER_MODELS_DIR = MODELS_DIR / "users"

DATABASE_DIR = PROJECT_ROOT / "database"
RESULTS_DIR = PROJECT_ROOT / "results"
USER_DATA_DIR = PROJECT_ROOT / "user_data"

DATABASE_PATH = DATABASE_DIR / "users.db"

TOTAL_WRITERS = 55
IMPOSTOR_SAMPLES_PER_WRITER = 5
MIN_SIGNATURES = 10

IMAGE_WIDTH = 200
IMAGE_HEIGHT = 100
IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)

CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)

GAUSSIAN_KERNEL = (3, 3)

MIN_COMPONENT_AREA = 15

BOUNDING_BOX_PADDING = 10

HOG_ORIENTATIONS = 9
HOG_PIXELS_PER_CELL = (8, 8)
HOG_CELLS_PER_BLOCK = (2, 2)
HOG_BLOCK_NORM = "L2-Hys"

SVM_KERNEL = "rbf"
SVM_C = 10
SVM_GAMMA = "scale"
SVM_PROBABILITY = True
RANDOM_STATE = 42

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
CEDAR_MODELS_DIR.mkdir(parents=True, exist_ok=True)
USER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)