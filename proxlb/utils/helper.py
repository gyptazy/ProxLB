"""
The Helper class provides some basic helper functions to not mess up the code in other
classes.
"""

import uuid
import sys
import utils.version
from utils.logger import SystemdLogger
from typing import Dict, Any

logger = SystemdLogger()


class Helper:
    """
    The Helper class provides some basic helper functions to not mess up the code in other
    classes.
    """
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
