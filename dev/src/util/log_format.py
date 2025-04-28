import structlog
import logging
import os
from datetime import datetime
from pathlib import Path


def setup_global_logging():
    log_directory = "./log/"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    now = datetime.now()
    formatted_time = now.strftime("%d-%m-%Y_%H-%M-%S")

    file_name = f"{formatted_time}.log"
    log_file_path = os.path.join(log_directory, file_name)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.add_log_level,
            # structlog.dev.ConsoleRenderer(),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(
            file=Path(log_file_path).open("wt")
        ),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
