import logging
import sys


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_formatter = logging.Formatter(
        "%(levelname)s:     %(name)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.INFO)
    uvicorn_access_logger.propagate = False
    if not uvicorn_access_logger.handlers:
        uvicorn_access_logger.addHandler(console_handler)

    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)
    if not fastapi_logger.handlers:
        fastapi_logger.addHandler(console_handler)

    logger.info("Logging configured successfully!")
