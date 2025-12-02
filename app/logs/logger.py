import logging
import os
from logging.handlers import RotatingFileHandler

# === Crear carpeta logs si no existe ===
LOGS_DIR = "app/logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# === Configuración del logger ===
log_file = os.path.join(LOGS_DIR, "app.log")

logger = logging.getLogger("TutorIA")
logger.setLevel(logging.INFO)

# RotatingFileHandler → limita tamaño del archivo
handler = RotatingFileHandler(
    log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)
