import sys
from loguru import logger
from app.core.config import settings

def setup_logger():
    # remove default handler
    logger.remove() 
    # Console (develpment)
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    ) 

    # ── File: all logs

    logger.add(
        "logs/app.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
        rotation="10 MB",       # new file every 10MB
        retention="30 days",    # keep 30 days of logs
        compression="zip",      # compress old files
        enqueue=True,           # async write (no slowdown)
    )

    # ── File: errors only

    logger.add(
        "logs/error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
        rotation="10 MB",
        retention="90 days",    # keep errors longer
        compression="zip",
        enqueue=True,
        backtrace=True,         # full stack trace
        diagnose=True,          # variable values in trace
    )
    # ── File: security events

    logger.add(
        "logs/security.log",
        level="WARNING",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        enqueue=True,
        filter=lambda r: "SECURITY" in r["message"],
    )

    return logger

logger = setup_logger()