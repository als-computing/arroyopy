import logging


def setup_logger(logger: logging.Logger, log_level: str = "INFO"):
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.setLevel(log_level.upper())
    logger.debug("DEBUG LOGGING SET")
