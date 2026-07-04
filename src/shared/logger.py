"""shared/logger.py"""

import sys

from loguru import logger


def configure_logging(log_level: str = "INFO", service_name: str = "ddos-system") -> None:
    """Configure Loguru with structured JSON output for production."""
    logger.remove()  # Remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        f"<cyan>{service_name}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console output (human-readable during development)
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        enqueue=True,  # Thread-safe async logging
    )

    # File output (JSON structured for ELK/Loki in production)
    logger.add(
        "logs/{service_name}.log".format(service_name=service_name),
        format="{time} {level} {name} {message}",
        level=log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        serialize=True,  # JSON format
        enqueue=True,
    )


def get_logger(name: str):
    """Returns a Loguru logger bound with the calling module name."""
    return logger.bind(module=name)
