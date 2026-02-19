# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import functools
import logging
import os

from typing import Callable


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

class CustomLogger:
    """A custom logger class from GenAIComps that is needed for easy prototyping microservices from GenAIComps."""

    def __init__(self, name: str = None):
        """Initialize the logger with a name and custom levels."""
        name = "GenAIComps" if not name else name
        self.logger = logging.getLogger(name)

        # Define custom log levels
        log_config = {
            "DEBUG": 10,
            "INFO": 20,
            "TRAIN": 21,
            "EVAL": 22,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
            "EXCEPTION": 100,
        }

        # Add custom levels to logger
        for key, level in log_config.items():
            logging.addLevelName(level, key)
            if key == "EXCEPTION":
                self.__dict__[key.lower()] = self.logger.exception
            else:
                self.__dict__[key.lower()] = functools.partial(self.log_message, level)

        # Set up log format and handler
        self.format = logging.Formatter(fmt="[%(asctime)-15s] [%(levelname)8s] - %(name)s - %(message)s")
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.format)

        # Add handler to logger and set log level
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def log_message(self, log_level: str, msg: str):
        """Log a message at a given level.

        :param log_level: The level at which to log the message.
        :param msg: The message to log.
        """
        self.logger.log(log_level, msg)

    def close(self):
        """Close all the handlers."""
        for handler in self.logger.handlers:
            handler.close()

    # Define type hints for pylint check
    debug: Callable[[str], None]
    info: Callable[[str], None]
    train: Callable[[str], None]
    eval: Callable[[str], None]
    warning: Callable[[str], None]
    error: Callable[[str], None]
    critical: Callable[[str], None]
    exception: Callable[[str], None]
