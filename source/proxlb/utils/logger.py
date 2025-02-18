"""
The SystemdLogger class provides the root logger support. It dynamically
evaluates the further usage and imports of journald and adjusts
the logger to the systems functionality where it gets executed
"""

import logging
try:
    from systemd.journal import JournalHandler
    SYSTEMD_PRESENT = True
except ImportError:
    SYSTEMD_PRESENT = False


class SystemdLogger:
    """
    The SystemdLogger class provides the root logger support. It dynamically
    evaluates the further usage and imports of journald and adjusts
    the logger to the systems functionality where it gets executed.
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

        # Create a JournalHandler for systemd integration if this
        # is supported on the underlying OS.
        if SYSTEMD_PRESENT:
            # Add a JournalHandler for systemd integration
            journal_handler = JournalHandler()
            journal_handler.setLevel(level)
            # Set a formatter to include the logger's name and log message
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            journal_handler.setFormatter(formatter)
            # Add handler to logger
            self.logger.addHandler(journal_handler)

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
