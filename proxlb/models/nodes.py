"""
The Nodes class retrieves all running nodes in a Proxmox cluster
and collects their resource metrics.

Methods:
    __init__:
        Initializes the Nodes class.

    get_nodes(proxmox_api: any, proxlb_config: Dict[str, Any]) -> Dict[str, Any]:
        Gets metrics of all nodes in a Proxmox cluster.

    set_node_maintenance(proxlb_config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        Sets Proxmox nodes to a maintenance mode if required.

    set_node_ignore(proxlb_config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        Sets Proxmox nodes to be ignored if requested.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import Dict, Any
from utils.logger import SystemdLogger

logger = SystemdLogger()


class Nodes:
    """
    The Nodes class retrieves all running nodes in a Proxmox cluster
    and collects their resource metrics.
    """
    def __init__(self):
        """
        Initializes the Nodes class with the provided ProxLB data.
        """

    @staticmethod
    def get_nodes(proxmox_api: any, proxlb_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metrics of all nodes in a Proxmox cluster.

        This method retrieves metrics for all available nodes in the Proxmox cluster.
        It iterates over each node and collects resource metrics including CPU, memory, and disk usage.

        Args:
            proxmox_api (any): The Proxmox API client instance.
            nodes (Dict[str, Any]): A dictionary containing information about the nodes in the Proxmox cluster.

        Returns:
            Dict[str, Any]: A dictionary containing metrics and information for all running nodes.
        """
        logger.debug("Starting: get_nodes.")
        nodes = {"nodes": {}}

        for node in proxmox_api.nodes.get():
            # Ignoring a node results into ignoring all placed guests on the ignored node!
            if node["status"] == "online" and not Nodes.set_node_ignore(proxlb_config, node["node"]):
                nodes["nodes"][node["node"]] = {}
                nodes["nodes"][node["node"]]["name"] = node["node"]
                nodes["nodes"][node["node"]]["maintenance"] = False
                nodes["nodes"][node["node"]]["patching"] = False
                nodes["nodes"][node["node"]]["cpu_total"] = node["maxcpu"]
                nodes["nodes"][node["node"]]["cpu_assigned"] = 0
                nodes["nodes"][node["node"]]["cpu_used"] = node["cpu"] * node["maxcpu"]
                nodes["nodes"][node["node"]]["cpu_free"] = (node["maxcpu"]) - (node["cpu"] * node["maxcpu"])
                nodes["nodes"][node["node"]]["cpu_assigned_percent"] = nodes["nodes"][node["node"]]["cpu_assigned"] / nodes["nodes"][node["node"]]["cpu_total"] * 100
                nodes["nodes"][node["node"]]["cpu_free_percent"] = nodes["nodes"][node["node"]]["cpu_free"] / node["maxcpu"] * 100
                nodes["nodes"][node["node"]]["cpu_used_percent"] = nodes["nodes"][node["node"]]["cpu_used"] / node["maxcpu"] * 100
                nodes["nodes"][node["node"]]["memory_total"] = node["maxmem"]
                nodes["nodes"][node["node"]]["memory_assigned"] = 0
                nodes["nodes"][node["node"]]["memory_used"] = node["mem"]
                nodes["nodes"][node["node"]]["memory_free"] = node["maxmem"] - node["mem"]
                nodes["nodes"][node["node"]]["memory_assigned_percent"] = nodes["nodes"][node["node"]]["memory_assigned"] / nodes["nodes"][node["node"]]["memory_total"] * 100
                nodes["nodes"][node["node"]]["memory_free_percent"] = nodes["nodes"][node["node"]]["memory_free"] / node["maxmem"] * 100
                nodes["nodes"][node["node"]]["memory_used_percent"] = nodes["nodes"][node["node"]]["memory_used"] / node["maxmem"] * 100
                nodes["nodes"][node["node"]]["disk_total"] = node["maxdisk"]
                nodes["nodes"][node["node"]]["disk_assigned"] = 0
                nodes["nodes"][node["node"]]["disk_used"] = node["disk"]
                nodes["nodes"][node["node"]]["disk_free"] = node["maxdisk"] - node["disk"]
                nodes["nodes"][node["node"]]["disk_assigned_percent"] = nodes["nodes"][node["node"]]["disk_assigned"] / nodes["nodes"][node["node"]]["disk_total"] * 100
                nodes["nodes"][node["node"]]["disk_free_percent"] = nodes["nodes"][node["node"]]["disk_free"] / node["maxdisk"] * 100
                nodes["nodes"][node["node"]]["disk_used_percent"] = nodes["nodes"][node["node"]]["disk_used"] / node["maxdisk"] * 100

                # Evaluate if node should be set to maintenance mode
                if Nodes.set_node_maintenance(proxmox_api, proxlb_config, node["node"]):
                    nodes["nodes"][node["node"]]["maintenance"] = True

        logger.debug("Finished: get_nodes.")
        return nodes

    @staticmethod
    def set_node_maintenance(proxmox_api, proxlb_config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        """
        Set nodes to maintenance mode based on the provided configuration.

        This method updates the nodes dictionary to mark certain nodes as being in maintenance mode
        based on the configuration provided in proxlb_config.

        Args:
            proxmox_api (any): The Proxmox API client instance.
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration, including maintenance nodes.
            node_name: (str): The current node name within the outer iteration.

        Returns:
            Bool: Returns a bool if the provided node name is present in the maintenance section of the config file.
        """
        logger.debug("Starting: set_node_maintenance.")

        # Evaluate maintenance mode by config
        if proxlb_config.get("proxmox_cluster", None).get("maintenance_nodes", None) is not None:
            if len(proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", [])) > 0:
                if node_name in proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", []):
                    logger.info(f"Node: {node_name} has been set to maintenance mode (by ProxLB config).")
                    return True
                else:
                    logger.debug(f"Node: {node_name} is not in maintenance mode by ProxLB config.")

        # Evaluate maintenance mode by Proxmox HA
        for ha_element in proxmox_api.cluster.ha.status.current.get():
            if ha_element.get("status"):
                if "maintenance mode" in ha_element.get("status"):
                    if ha_element.get("node") == node_name:
                        logger.info(f"Node: {node_name} has been set to maintenance mode (by Proxmox HA API).")
                        return True
                    else:
                        logger.debug(f"Node: {node_name} is not in maintenance mode by Proxmox HA API.")

        logger.debug("Finished: set_node_maintenance.")

    @staticmethod
    def set_node_ignore(proxlb_config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        """
        Set nodes to be ignored based on the provided configuration.

        This method updates the nodes dictionary to mark certain nodes as being ignored
        based on the configuration provided in proxlb_config.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration, including maintenance nodes.
            node_name: (str): The current node name within the outer iteration.

        Returns:
            Bool: Returns a bool if the provided node name is present in the ignore section of the config file.
        """
        logger.debug("Starting: set_node_ignore.")

        if proxlb_config.get("proxmox_cluster", None).get("ignore_nodes", None) is not None:
            if len(proxlb_config.get("proxmox_cluster", {}).get("ignore_nodes", [])) > 0:
                if node_name in proxlb_config.get("proxmox_cluster", {}).get("ignore_nodes", []):
                    logger.info(f"Node: {node_name} has been set to be ignored. Not adding node!")
                    return True

        logger.debug("Finished: set_node_ignore.")
