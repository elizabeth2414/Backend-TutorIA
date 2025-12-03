import logging
import os
from logging.handlers import RotatingFileHandler

# ====== RUTA BASE DEL PROYECTO ======
# Si este archivo está en:   app/logs/logger.py
# BASE_DIR será la carpeta:  <raíz del proyecto> (la que contiene /app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Carpeta /logs en la raíz del proyecto
LOGS_DIR = os.path.join(BASE_DIR, "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

log_file = os.path.join(LOGS_DIR, "app.log")

# ====== CONFIGURAR LOGGER ======
logger = logging.getLogger("TutorIA")
logger.setLevel(logging.INFO)

# Evitar duplicar handlers cuando uvicorn recarga
if not logger.handlers:
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

# Opcional: no propagar al root logger (para no duplicar mensajes)
logger.propagate = False
