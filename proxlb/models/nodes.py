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
        cluster = {"cluster": {}}

        for node in proxmox_api.nodes.get():
            # Ignoring a node results into ignoring all placed guests on the ignored node!
            if node["status"] == "online" and not Nodes.set_node_ignore(proxlb_config, node["node"]):
                nodes["nodes"][node["node"]] = {}
                nodes["nodes"][node["node"]]["name"] = node["node"]
                nodes["nodes"][node["node"]]["maintenance"] = False
                nodes["nodes"][node["node"]]["dpm_shutdown"] = False
                nodes["nodes"][node["node"]]["dpm_startup"] = False
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
                if Nodes.set_node_maintenance(proxlb_config, node["node"]):
                    nodes["nodes"][node["node"]]["maintenance"] = True

                # Generate the intial cluster statistics within the same loop to avoid a further one.
                logger.debug(f"Updating cluster statistics by online node {node['node']}.")
                cluster["cluster"]["node_count"] = cluster["cluster"].get("node_count", 0) + 1
                cluster["cluster"]["cpu_total"] = cluster["cluster"].get("cpu_total", 0) + nodes["nodes"][node["node"]]["cpu_total"]
                cluster["cluster"]["cpu_used"] = cluster["cluster"].get("cpu_used", 0) + nodes["nodes"][node["node"]]["cpu_used"]
                cluster["cluster"]["cpu_free"] = cluster["cluster"].get("cpu_free", 0) + nodes["nodes"][node["node"]]["cpu_free"]
                cluster["cluster"]["cpu_free_percent"] = cluster["cluster"].get("cpu_free", 0) / cluster["cluster"].get("cpu_total", 0) * 100
                cluster["cluster"]["cpu_used_percent"] = cluster["cluster"].get("cpu_used", 0) / cluster["cluster"].get("cpu_total", 0) * 100
                cluster["cluster"]["memory_total"] = cluster["cluster"].get("memory_total", 0) + nodes["nodes"][node["node"]]["memory_total"]
                cluster["cluster"]["memory_used"] = cluster["cluster"].get("memory_used", 0) + nodes["nodes"][node["node"]]["memory_used"]
                cluster["cluster"]["memory_free"] = cluster["cluster"].get("memory_free", 0) + nodes["nodes"][node["node"]]["memory_free"]
                cluster["cluster"]["memory_free_percent"] = cluster["cluster"].get("memory_free", 0) / cluster["cluster"].get("memory_total", 0) * 100
                cluster["cluster"]["memory_used_percent"] = cluster["cluster"].get("memory_used", 0) / cluster["cluster"].get("memory_total", 0) * 100
                cluster["cluster"]["disk_total"] = cluster["cluster"].get("disk_total", 0) + nodes["nodes"][node["node"]]["disk_total"]
                cluster["cluster"]["disk_used"] = cluster["cluster"].get("disk_used", 0) + nodes["nodes"][node["node"]]["disk_used"]
                cluster["cluster"]["disk_free"] = cluster["cluster"].get("disk_free", 0) + nodes["nodes"][node["node"]]["disk_free"]
                cluster["cluster"]["disk_free_percent"] = cluster["cluster"].get("disk_free", 0) / cluster["cluster"].get("disk_total", 0) * 100
                cluster["cluster"]["disk_used_percent"] = cluster["cluster"].get("disk_used", 0) / cluster["cluster"].get("disk_total", 0) * 100

                cluster["cluster"]["node_count_available"] = cluster["cluster"].get("node_count_available", 0) + 1
                cluster["cluster"]["node_count_overall"] = cluster["cluster"].get("node_count_overall", 0) + 1

            # Update the cluster statistics by offline nodes to have the overall count of nodes in the cluster
            else:
                logger.debug(f"Updating cluster statistics by offline node {node['node']}.")
                cluster["cluster"]["node_count_overall"] = cluster["cluster"].get("node_count_overall", 0) + 1

        logger.debug("Finished: get_nodes.")
        return nodes, cluster

    @staticmethod
    def set_node_maintenance(proxlb_config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        """
        Set nodes to maintenance mode based on the provided configuration.

        This method updates the nodes dictionary to mark certain nodes as being in maintenance mode
        based on the configuration provided in proxlb_config.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration, including maintenance nodes.
            node_name: (str): The current node name within the outer iteration.

        Returns:
            Bool: Returns a bool if the provided node name is present in the maintenance section of the config file.
        """
        logger.debug("Starting: set_node_maintenance.")

        if proxlb_config.get("proxmox_cluster", None).get("maintenance_nodes", None) is not None:
            if len(proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", [])) > 0:
                if node_name in proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", []):
                    logger.warning(f"Node: {node_name} has been set to maintenance mode.")
                    return True

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
                    logger.warning(f"Node: {node_name} has been set to be ignored. Not adding node!")
                    return True

        logger.debug("Finished: set_node_ignore.")
