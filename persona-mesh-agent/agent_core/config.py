import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL       = os.getenv("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Obsidian vault
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH",
                                    r"C:\ARIA\ARIA-Memory-Vault")

    # Persona
    PERSONA_NAME = os.getenv("PERSONA", "Assistant")

    # Memory
    TOP_K_VECTOR       = int(os.getenv("TOP_K_VECTOR", "3"))
    MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))

    # Paths
    DATA_DIR          = os.getenv("DATA_DIR", "./data")
    INDEX_PERSIST_DIR = os.getenv("INDEX_PERSIST_DIR", "./data/.index")

    # Watchdog: comma-separated directories to auto-index on file changes
    WATCH_DIRS        = [d.strip() for d in os.getenv("WATCH_DIRS", "").split(",") if d.strip()]

config = Config()
