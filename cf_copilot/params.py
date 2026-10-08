import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=False)
PLAYBOOK_PATH = BASE_DIR / "data" / "playbook"
CHROMA_PATH = BASE_DIR / "data" / "chroma_db"
LOCAL_REGISTRY_PATH = str(BASE_DIR / os.environ.get("LOCAL_REGISTRY_PATH", "raw_data"))
LOCAL_HISTORICAL_DATA_PATH = str(Path(LOCAL_REGISTRY_PATH) / "data" / "historical.csv")
GCP_PROJECT = os.environ.get("GCP_PROJECT_ID")
GCP_REGION = os.environ.get("GCP_REGION", "europe-west1")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
GCS_MODEL_PREFIX = os.environ.get("GCS_MODEL_PREFIX", "cf_copilot/")
GCS_HISTORICAL_DATA_PATH = os.environ.get("GCS_HISTORICAL_DATA_PATH", "data/historical.csv")
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI")
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT", "cf-copilot")
MLFLOW_MODEL_NAME = os.environ.get("MLFLOW_MODEL_NAME", "cf-copilot")
MODEL_TARGET = os.environ.get("MODEL_TARGET", "local")
API_URL = os.environ.get("API_URL", "http://localhost:8080")
ENV = os.environ.get("ENV", "development")
CURRENT_DATE = pd.Timestamp(os.environ.get("CURRENT_DATE") or pd.Timestamp.today().date())
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
