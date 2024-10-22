# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import functools
import logging
import os


class OPEALogger(logging.Logger):
    """A custom logger class that adds additional logging levels."""

    def __init__(self, name: str = "GenAIComps"):
        """Initialize the logger with a name and custom levels."""
        super().__init__(name)

        # Define custom log levels
        log_config = {
            "TRAIN": 21,
            "EVAL": 22,
        }

        # Add custom levels to logger
        for k, level in log_config.items():
            logging.addLevelName(level, k)
            self.__dict__[k.lower()] = functools.partial(self.log_message, level)

    def log_message(self, log_level: str, msg: str, args=None):
        """Log a message at a given level.

        :param log_level: The level at which to log the message.
        :param msg: The message to log.
        :param args: Additional arguments to pass to the logger.
        """
        self._log(log_level, msg, args)


logging.setLoggerClass(OPEALogger)


def get_opea_logger(name: str = "GenAIComps", log_level: str = "INFO"):
    if name not in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(name)
        # Set up log format and handler
        format = logging.Formatter(fmt="[%(asctime)-15s] [%(levelname)8s] - [%(name)s] - %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(format)

        # Add handler to logger and set log level
        logger.addHandler(handler)
        logger.setLevel(log_level)

        if os.environ.get('LOGGING_PROPAGATE', 'false').lower() == 'true':
            logger.propagate = True
        else:
            logger.propagate = False

        return logger
    else:
        logger = logging.getLogger(name)
        return logger

def change_opea_logger_level(logger, log_level) -> None:
    logger.setLevel(log_level)
