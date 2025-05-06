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


import json
from typing import Dict, Any
from utils.helper import Helper
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

                # Evaluate guest count on node
                guests_vm = [
                    guest for guest in proxmox_api.nodes(node["node"]).qemu.get()
                    if guest.get('status') == 'running'
                ]

                guests_ct = [
                    guest for guest in proxmox_api.nodes(node["node"]).lxc.get()
                    if guest.get('status') == 'running'
                ]

                guests_vm = len(guests_vm)
                guests_ct = len(guests_ct)
                nodes["nodes"][node["node"]]["guest_count"] = guests_vm + guests_ct

                # Add debug log of node
                logger.debug(f"Added node: {nodes['nodes'][node['node']]}.")

        logger.debug("Finished: get_nodes.")
        return nodes

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

        # Only validate if we have more than a single node in our cluster
        if len(proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", [])) > 0:

            # Evaluate maintenance mode by config
            logger.debug("Evaluate maintenance mode by config.")
            if proxlb_config.get("proxmox_cluster", None).get("maintenance_nodes", None) is not None:
                if node_name in proxlb_config.get("proxmox_cluster", {}).get("maintenance_nodes", []):
                    logger.warning(f"Node: {node_name} has been set to maintenance mode.")
                    return True

            # Evaluate maintenance mode by ProxLB API
            logger.debug("Evaluate maintenance mode by ProxLB API.")
            if proxlb_config.get("proxlb_api", {}).get("enable", False):
                logger.debug("ProxLB API is active.")
                proxlb_api_listener = proxlb_config.get("proxlb_api", {}).get("listen_address", "127.0.0.1")
                proxlb_api_port = proxlb_config.get("proxlb_api", {}).get("port", 8008)
                try:
                    api_node_status = Helper.http_client_get(f"http://{proxlb_api_listener}:{proxlb_api_port}/nodes/{node_name}", show_errors=False)
                    api_node_status = json.loads(api_node_status)
                except:
                    pass

                # Set to maintenance when DPM or node patching is active and the
                # node has not been released yet
                if isinstance(api_node_status, dict):
                    logger.debug(f"Information for Node: {node_name} in ProxLB API available.")

                    if api_node_status.get("mode_dpm") or api_node_status.get("mode_patch"):
                        logger.debug(f"Node: {node_name} is defined for DPM or node-patching.")

                        if not api_node_status.get("processed"):
                            logger.debug(f"Node: {node_name} has not been processed. Setting to maintenance.")

                            if not api_node_status.get("release"):
                                logger.debug(f"Node: {node_name} has not been released. Waiting until node has been released. Setting to maintenance.")
                                return True

                            else:
                                logger.debug(f"Node: {node_name} has been released. Removing maintenance.")
                        else:
                            logger.debug(f"Node: {node_name} has been processed. Removing maintenance.")
                    else:
                        logger.debug(f"Node: {node_name} is not defined for DPM or node-patching.")
            else:
                logger.debug("ProxLB API is not active. Skipping ProxLB API validations.")

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
