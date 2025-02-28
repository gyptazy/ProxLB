"""
The CliParser class handles the parsing of command-line interface (CLI) arguments.
"""

import argparse
from utils.logger import SystemdLogger

logger = SystemdLogger()


class CliParser:
    """
    The CliParser class handles the parsing of command-line interface (CLI) arguments.
    """
    def __init__(self):
        """
        Initializes the argument parser and defines available CLI options.
        """
        logger.debug("Starting: CliParser.")
        self.parser = argparse.ArgumentParser(description="ProxLB - Proxmox Load Balancer")

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
            "-m", "--maintenance",
            help="Sets node to maintenance mode & moves workloads away",
            type=str,
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
        Parses and returns CLI arguments.
        """
        logger.debug("Starting: parse_args.")
        logger.debug(self.parser.parse_args())

        logger.debug("Finished: parse_args.")
        return self.parser.parse_args()
