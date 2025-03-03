"""
The CliParser class handles the parsing of command-line interface (CLI) arguments.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import argparse
import utils.version
from utils.logger import SystemdLogger

logger = SystemdLogger()


class CliParser:
    """
    The CliParser class handles the parsing of command-line interface (CLI) arguments.
    """
    def __init__(self):
        """
        Initializes the CliParser class.

        This method sets up an argument parser for the command-line interface (CLI) with various options:
        - `-c` or `--config`: Specifies the path to the configuration file.
        - `-d` or `--dry-run`: Performs a dry-run without executing any actions.
        - `-j` or `--json`: Returns a JSON of the VM movement.
        - `-b` or `--best-node`: Returns the best next node.
        - `-v` or `--version`: Returns the current ProxLB version.

        Logs the start and end of the initialization process.
        """
        logger.debug("Starting: CliParser.")

        self.parser = argparse.ArgumentParser(
            description=(
                f"{utils.version.__app_name__} ({utils.version.__version__}): "
                f"{utils.version.__app_desc__}"
            )
        )

        self.parser.add_argument(
            "-c", "--config",
            help="Path to the configuration file",
            type=str,
            required=False
        )
        self.parser.add_argument(
            "-d", "--dry-run",
            help="Perform a dry-run without executing any actions",
            action="store_true",
            required=False
        )
        self.parser.add_argument(
            "-j", "--json",
            help="Return a JSON of the VM movement",
            action="store_true",
            required=False
        )
        self.parser.add_argument(
            "-b", "--best-node",
            help="Returns the best next node",
            action="store_true",
            required=False
        )
        self.parser.add_argument(
            "-v", "--version",
            help="Returns the current ProxLB version",
            action="store_true",
            required=False
        )
        logger.debug("Finished: CliParser.")

    def parse_args(self) -> argparse.Namespace:
        """
        Parses and returns the parsed command-line interface (CLI) arguments.

        This method uses the argparse library to parse the arguments provided
        via the command line. It logs the start and end of the parsing process,
        as well as the parsed arguments for debugging purposes.

        Returns:
            argparse.Namespace: An object containing the parsed CLI arguments.
        """
        logger.debug("Starting: parse_args.")
        logger.debug(self.parser.parse_args())

        logger.debug("Finished: parse_args.")
        return self.parser.parse_args()
