import os
import socket

import structlog
from linz_logger import get_log, set_contextvars


def get_logger() -> structlog.stdlib.BoundLogger:
    __init_logger()
    logger: structlog.stdlib.BoundLogger = get_log()
    return logger


def __init_logger() -> None:
    set_contextvars({"hostname": __get_hostname()})


def __get_hostname() -> str:
    # Get the pod name
    hostname = os.getenv("ARGO_NODE_ID")
    # If local
    if not hostname:
        hostname = socket.gethostname()

    return hostname


LOGGER: structlog.stdlib.BoundLogger = get_logger()
