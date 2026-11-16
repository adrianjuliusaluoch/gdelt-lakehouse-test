# Settings and secrets, all read from environment variables
import os

from dotenv import load_dotenv

load_dotenv()

HF_NAMESPACE = os.environ["HF_NAMESPACE"]
HF_BUCKET = os.environ["HF_BUCKET"]
HF_S3_KEY_ID = os.environ["HF_S3_KEY_ID"]
HF_S3_SECRET = os.environ["HF_S3_SECRET"]
PG_CATALOG = os.environ["PG_CATALOG"]

# GDELT 2.0 publishes one events file every 15 minutes, named by its UTC slot
GDELT_BASE_URL = "http://data.gdeltproject.org/gdeltv2/"
LOOKBACK_HOURS = 6       # each run also catches up on slots missed in this window
MAX_TRIES = 3
PAUSE = 0.5              # seconds between downloads, to be polite to the source