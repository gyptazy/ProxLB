"""
The Helper class provides some basic helper functions to not mess up the code in other
classes.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import json
import uuid
import sys
import time
import utils.version
from utils.logger import SystemdLogger
from typing import Dict, Any

logger = SystemdLogger()


class Helper:
    """
    The Helper class provides some basic helper functions to not mess up the code in other
    classes.

    Methods:
        __init__():
            Initializes the general Helper class.

        get_uuid_string() -> str:
            Generates a random uuid and returns it as a string.

        log_node_metrics(proxlb_data: Dict[str, Any], init: bool = True) -> None:
            Logs the memory, CPU, and disk usage metrics of nodes in the provided proxlb_data dictionary.

        get_version(print_version: bool = False) -> None:
            Returns the current version of ProxLB and optionally prints it to stdout.

        get_daemon_mode(proxlb_config: Dict[str, Any]) -> None:
            Checks if the daemon mode is active and handles the scheduling accordingly.
    """
    proxlb_reload = False

    def __init__(self):
        """
        Initializes the general Helper clas.
        """

    @staticmethod
    def get_uuid_string() -> str:
        """
        Generates a random uuid and returns it as a string.

        Args:
            None

        Returns:
            Str: Returns a random uuid as a string.
        """
        logger.debug("Starting: get_uuid_string.")
        generated_uuid = uuid.uuid4()
        logger.debug("Finished: get_uuid_string.")
        return str(generated_uuid)

    @staticmethod
    def log_node_metrics(proxlb_data: Dict[str, Any], init: bool = True) -> None:
        """
        Logs the memory, CPU, and disk usage metrics of nodes in the provided proxlb_data dictionary.

        This method processes the usage metrics of nodes and logs them. It also updates the
        'statistics' field in the 'meta' section of the proxlb_data dictionary with the
        memory, CPU, and disk usage metrics before and after a certain operation.

            proxlb_data (Dict[str, Any]): A dictionary containing node metrics and metadata.
            init (bool): A flag indicating whether to initialize the 'before' statistics
                        (True) or update the 'after' statistics (False). Default is True.
        """
        logger.debug("Starting: log_node_metrics.")
        nodes_usage_memory = " | ".join([f"{key}: {value['memory_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
        nodes_usage_cpu = "  | ".join([f"{key}: {value['cpu_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
        nodes_usage_disk = " | ".join([f"{key}: {value['disk_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])

        if init:
            proxlb_data["meta"]["statistics"] = {"before": {"memory": nodes_usage_memory, "cpu": nodes_usage_cpu, "disk": nodes_usage_disk}, "after": {"memory": "", "cpu": "", "disk": ""}}
        else:
            proxlb_data["meta"]["statistics"]["after"] = {"memory": nodes_usage_memory, "cpu": nodes_usage_cpu, "disk": nodes_usage_disk}

        logger.debug(f"Nodes usage memory: {nodes_usage_memory}")
        logger.debug(f"Nodes usage cpu:    {nodes_usage_cpu}")
        logger.debug(f"Nodes usage disk:   {nodes_usage_disk}")
        logger.debug("Finished: log_node_metrics.")

    @staticmethod
    def get_version(print_version: bool = False) -> None:
        """
        Returns the current version of ProxLB and optionally prints it to stdout.

        Parameters:
            print_version (bool): If True, prints the version information to stdout and exits the program.

        Returns:
            None
        """
        if print_version:
            print(f"{utils.version.__app_name__} version: {utils.version.__version__}\n(C) 2025 by {utils.version.__author__}\n{utils.version.__url__}")
            sys.exit(0)

    @staticmethod
    def get_daemon_mode(proxlb_config: Dict[str, Any]) -> None:
        """
        Checks if the daemon mode is active and handles the scheduling accordingly.

        Parameters:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

        Returns:
            None
        """
        logger.debug("Starting: get_daemon_mode.")
        if proxlb_config.get("service", {}).get("daemon", True):

            # Validate schedule format which changed in v1.1.1
            if type(proxlb_config["service"].get("schedule", None)) != dict:
                logger.error("Invalid format for schedule. Please use 'hours' or 'minutes'.")
                sys.exit(1)

            # Convert hours to seconds
            if proxlb_config["service"]["schedule"].get("format", "hours") == "hours":
                sleep_seconds = proxlb_config.get("service", {}).get("schedule", {}).get("interval", 12) * 3600
            # Convert minutes to seconds
            elif proxlb_config["service"]["schedule"].get("format", "hours") == "minutes":
                sleep_seconds = proxlb_config.get("service", {}).get("schedule", {}).get("interval", 720) * 60
            else:
                logger.error("Invalid format for schedule. Please use 'hours' or 'minutes'.")
                sys.exit(1)

            logger.info(f"Daemon mode active: Next run in: {proxlb_config.get('service', {}).get('schedule', {}).get('interval', 12)} {proxlb_config['service']['schedule'].get('format', 'hours')}.")
            time.sleep(sleep_seconds)

        else:
            logger.debug("Successfully executed ProxLB. Daemon mode not active - stopping.")
            print("Daemon mode not active - stopping.")
            sys.exit(0)

        logger.debug("Finished: get_daemon_mode.")

    @staticmethod
    def get_service_delay(proxlb_config: Dict[str, Any]) -> None:
        """
        Checks if a start up delay for the service is defined and waits to proceed until
        the time is up.

        Parameters:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

        Returns:
            None
        """
        logger.debug("Starting: get_service_delay.")
        if proxlb_config.get("service", {}).get("delay", {}).get("enable", False):

            # Convert hours to seconds
            if proxlb_config["service"]["delay"].get("format", "hours") == "hours":
                sleep_seconds = proxlb_config.get("service", {}).get("delay", {}).get("time", 1) * 3600
            # Convert minutes to seconds
            elif proxlb_config["service"]["delay"].get("format", "hours") == "minutes":
                sleep_seconds = proxlb_config.get("service", {}).get("delay", {}).get("time", 60) * 60
            else:
                logger.error("Invalid format for service delay. Please use 'hours' or 'minutes'.")
                sys.exit(1)

            logger.info(f"Service delay active: First run in: {proxlb_config.get('service', {}).get('delay', {}).get('time', 1)} {proxlb_config['service']['delay'].get('format', 'hours')}.")
            time.sleep(sleep_seconds)

        else:
            logger.debug("Service delay not active. Proceeding without delay.")

        logger.debug("Finished: get_service_delay.")

    @staticmethod
    def print_json(proxlb_config: Dict[str, Any], print_json: bool = False) -> None:
        """
        Prints the calculated balancing matrix as a JSON output to stdout.

        Parameters:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

        Returns:
            None
        """
        logger.debug("Starting: print_json.")
        if print_json:
            # Create a filtered list by stripping the 'meta' key from the proxlb_config dictionary
            # to make sure that no credentials are leaked.
            filtered_data = {k: v for k, v in proxlb_config.items() if k != "meta"}
            print(json.dumps(filtered_data, indent=4))

        logger.debug("Finished: print_json.")

    @staticmethod
    def handler_sighup(signum, frame):
        """
        Signal handler for SIGHUP.

        This method is triggered when the process receives a SIGHUP signal.
        It sets the `proxlb_reload` class variable to True to indicate that
        configuration should be reloaded in the main loop.

        Args:
            signum (int): The signal number (expected to be signal.SIGHUP).
            frame (frame object): Current stack frame (unused but required by signal handler signature).
        """
        logger.debug("Starting: handle_sighup.")
        logger.debug("Got SIGHUP signal. Reloading...")
        Helper.proxlb_reload = True
        logger.debug("Starting: handle_sighup.")
