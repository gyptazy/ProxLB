"""
The ConfigParser class handles the parsing of configuration file
from a given YAML file from any location.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import os
import sys
try:
    import yaml
    PYYAML_PRESENT = True
except ImportError:
    PYYAML_PRESENT = False
from typing import Dict, Any
from utils.logger import SystemdLogger


if not PYYAML_PRESENT:
    print("Error: The required library 'pyyaml' is not installed.")
    sys.exit(1)


logger = SystemdLogger()


class ConfigParser:
    """
    The ConfigParser class handles the parsing of a configuration file.

    Methods:
    __init__(config_path: str)

    test_config_path(config_path: str) -> None
        Checks if the configuration file is present at the given config path.

    get_config() -> Dict[str, Any]
        Parses and returns the configuration data from the YAML file.
    """
    def __init__(self, config_path: str):
        """
        Initializes the configuration file parser and validates the config file.
        """
        logger.debug("Starting: ConfigParser.")
        self.config_path = self.test_config_path(config_path)
        logger.debug("Finished: ConfigParser.")

    def test_config_path(self, config_path: str) -> None:
        """
        Checks if configuration file is present at given config path.
        """
        logger.debug("Starting: test_config_path.")
        # Test for config file at given location
        if config_path is not None:

            if os.path.exists(config_path):
                logger.debug(f"The file {config_path} exists.")
            else:
                logger.error(f"The file {config_path} does not exist.")
                sys.exit(1)

        # Test for config file at default location as a fallback
        if config_path is None:
            default_config_path = "/etc/proxlb/proxlb.yaml"

            if os.path.exists(default_config_path):
                logger.debug(f"The file {default_config_path} exists.")
                config_path = default_config_path
            else:
                print(f"The config file {default_config_path} does not exist.")
                logger.critical(f"The config file {default_config_path} does not exist.")
                sys.exit(1)

        logger.debug("Finished: test_config_path.")
        return config_path

    def get_config(self) -> Dict[str, Any]:
        """
        Parses and returns CLI arguments.
        """
        logger.debug("Starting: get_config.")
        logger.info(f"Using config path: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as config_file:
                config_data = yaml.load(config_file, Loader=yaml.FullLoader)
            return config_data
        except yaml.YAMLError as exception_error:
            print(f"Error loading YAML file: {exception_error}")
            logger.critical(f"Error loading YAML file: {exception_error}")
            sys.exit(1)

        logger.debug("Finished: get_config.")
