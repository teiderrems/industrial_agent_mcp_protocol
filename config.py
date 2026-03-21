# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Mode de fonctionnement de l'application
# - True : lance la base de données SQLite mock et un mock LLM
# - False : utilise la configuration PostgreSQL / LLM réel.
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

# Fichier SQLite local pour le mode mock
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "industrial.db")

# Configuration PostgreSQL (non mock)
POSTGRES_CONFIG = { ... }  # inchangé

# Ordre des fournisseurs LLM (priorité). Séparez par virgule.
LLM_ORDER = os.getenv("LLM_ORDER", "gemini,mistral")

# Mistral (exemple, à adapter selon les modèles disponibles)
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-tiny")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000")
