"""
The SystemdLogger class provides a singleton logger that integrates with systemd's journal if available.
It dynamically evaluates the environment and adjusts the logger accordingly.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import logging
import sys
try:
    from systemd.journal import JournalHandler
    SYSTEMD_PRESENT = True
except ImportError:
    SYSTEMD_PRESENT = False


class SystemdLogger:
    """
    The SystemdLogger class provides a singleton logger that integrates with systemd's journal if available.
    It dynamically evaluates the environment and adjusts the logger accordingly.

    Attributes:
        instance (SystemdLogger): Singleton instance of the SystemdLogger class.

    Methods:
        __new__(cls, name: str = "ProxLB", level: str = logging.INFO) -> 'SystemdLogger':
            Creates a new instance of the SystemdLogger class or returns the existing instance.

        initialize_logger(self, name: str, level: str) -> None:
            Initializes the logger with the given name and log level. Adds a JournalHandler if systemd is present.

        set_log_level(self, level: str) -> None:
            Sets the log level for the logger and all its handlers.

        debug(self, msg: str) -> str:
            Logs a message with level DEBUG.

        info(self, msg: str) -> str:
            Logs a message with level INFO.

        warning(self, msg: str) -> str:
            Logs a message with level WARNING.

        error(self, msg: str) -> str:
            Logs a message with level ERROR.

        critical(self, msg: str) -> str:
            Logs a message with level CRITICAL.
    """
    # Create a singleton instance variable
    instance = None

    def __new__(cls, name: str = "ProxLB", level: str = logging.INFO) -> 'SystemdLogger':
        """
        Creating a new systemd logger class based on a given logging name
        and its logging level/verbosity.

        Args:
            name (str): The application name that is being used for the logger.
            level (str): The log level defined as a string (e.g.: INFO).

        Returns:
            SystemdLogger: The systemd logger object.
        """
        # Check if instance already exists, otherwise create a new one
        if cls.instance is None:
            cls.instance = super(SystemdLogger, cls).__new__(cls)
            cls.instance.initialize_logger(name, level)
        return cls.instance

    def initialize_logger(self, name: str, level: str) -> None:
        """
        Initializing the systemd logger class based on a given logging name
        and its logging level/verbosity.

        Args:
            name (str): The application name that is being used for the logger.
            level (str): The log level defined as a string (e.g.: INFO).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create a logging handler depending on the
        # capabilities of the underlying OS where systemd
        # logging is preferred.
        if SYSTEMD_PRESENT:
            # Add a JournalHandler for systemd integration
            handler = JournalHandler(SYSLOG_IDENTIFIER="ProxLB")
        else:
            # Add a stdout handler as a fallback
            handler = logging.StreamHandler(sys.stdout)

        handler.setLevel(level)
        # Set a formatter to include the logger's name and log message
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        # Add handler to logger
        self.logger.addHandler(handler)

    def set_log_level(self, level: str) -> None:
        """
        Modifies and sets the log level on the given log level.

        Args:
            level (str): The log level defined as a string (e.g.: INFO).
        """
        self.logger.setLevel(level)

        for handler in self.logger.handlers:
            handler.setLevel(level)

        self.logger.debug("Set to debug level")

    # Handle systemd log levels
    def debug(self, msg: str) -> str:
        """
        Logger out for messages of type: DEBUG
        """
        self.logger.debug(msg)

    def info(self, msg: str) -> str:
        """
        Logger out for messages of type: INFO
        """
        self.logger.info(msg)

    def warning(self, msg: str) -> str:
        """
        Logger out for messages of type: WARNING
        """
        self.logger.warning(msg)

    def error(self, msg: str) -> str:
        """
        Logger out for messages of type: ERROR
        """
        self.logger.error(msg)

    def critical(self, msg: str) -> str:
        """
        Logger out for messages of type: CRITICAL
        """
        self.logger.critical(msg)
