from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config import settings


def get_app_logger() -> logging.Logger:
    logger = logging.getLogger("customer_support_ai")
    if logger.handlers:
        return logger

    log_path = Path(settings.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_interaction(payload: dict[str, Any]) -> None:
    get_app_logger().info(json.dumps(payload, ensure_ascii=False, default=str))
