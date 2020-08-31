import logging

from . import constants


def _create_logger():
    logger = logging.Logger(constants.TOOL_NAME) # pylint: disable=redefined-outer-name

    formatter = logging.Formatter(constants.LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


logger = _create_logger()
