"""
The Nodes class retrieves all running nodes in a Proxmox cluster
and collects their resource metrics.
"""

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
    def get_nodes(proxmox_api: any) -> Dict[str, Any]:
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
            if node["status"] == "online":
                nodes["nodes"][node["node"]] = {}
                nodes["nodes"][node["node"]]["name"] = node["node"]
                nodes["nodes"][node["node"]]["maintenance"] = False
                nodes["nodes"][node["node"]]["ignore"] = False
                nodes["nodes"][node["node"]]["groups_affinity"] = {}
                nodes["nodes"][node["node"]]["groups_anti_affinity"] = {}
                nodes["nodes"][node["node"]]["cpu_total"] = node["maxcpu"]
                nodes["nodes"][node["node"]]["cpu_assigned"] = 0
                nodes["nodes"][node["node"]]["cpu_used"] = node["cpu"]
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

        logger.debug("Finished: get_nodes.")
        return nodes

    @staticmethod
    def set_node_maintenance(nodes: Dict[str, Any], proxlb_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set nodes to maintenance mode based on the provided configuration.

        This method updates the nodes dictionary to mark certain nodes as being in maintenance mode
        based on the configuration provided in proxlb_config.

        Args:
            nodes (Dict[str, Any]): A dictionary containing information about the nodes in the Proxmox cluster.
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration, including maintenance nodes.

        Returns:
            Dict[str, Any]: The updated nodes dictionary with maintenance status set for specified nodes.
        """
        logger.debug("Starting: set_node_maintenance.")

        if proxlb_config.get("proxmox_cluster", None).get("maintenance_nodes", None) is not None:

            if len(proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", [])) > 0:
                for node in proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", []):

                    if node in nodes["nodes"]:
                        nodes["nodes"][node]["maintenance"] = True
                        logger.warning(f"Node {node} is set to maintenance mode.")
                    else:
                        logger.debug(f"Node {node} is not set to maintenance mode.")

        else:
            logger.debug("Maintenance for nodes is not defined in config.")

        logger.debug("Finished: set_node_maintenance.")
        return nodes

    @staticmethod
    def set_node_ignore(nodes: Dict[str, Any], proxlb_config) -> Dict[str, Any]:
        """
        Set nodes to be ignored based on the provided configuration.

        This method updates the nodes dictionary to mark certain nodes as being ignored
        based on the configuration provided in proxlb_config.

        Args:
            nodes (Dict[str, Any]): A dictionary containing information about the nodes in the Proxmox cluster.
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration, including maintenance nodes.

        Returns:
            Dict[str, Any]: The updated nodes dictionary with ignore status set for specified nodes.
        """
        logger.debug("Starting: set_node_ignore.")

        if proxlb_config.get("proxmox_cluster", None).get("ignore_nodes", None) is not None:

            if len(proxlb_config.get("proxmox_cluster", {}).get("ignore_nodes", [])) > 0:
                for node in proxlb_config.get("proxmox_cluster", {}).get("ignore_nodes", []):

                    if node in nodes["nodes"]:
                        nodes["nodes"][node]["ignore"] = True
                        logger.warning(f"Node {node} is set to be ignored.")
                    else:
                        logger.debug(f"Node {node} is not set to be ignored.")

        else:
            logger.debug("Nodes to be ignored is not defined in config.")

        logger.debug("Finished: set_node_ignore.")
        return nodes
