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


import time
from typing import Dict, Any
from utils.logger import SystemdLogger
from utils.helper import Helper

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
            proxmox_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.
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
                nodes["nodes"][node["node"]]["pve_version"] = Nodes.get_node_pve_version(proxmox_api, node["node"])
                nodes["nodes"][node["node"]]["pressure_hot"] = False
                nodes["nodes"][node["node"]]["maintenance"] = False
                nodes["nodes"][node["node"]]["cpu_total"] = node["maxcpu"]
                nodes["nodes"][node["node"]]["cpu_assigned"] = 0
                nodes["nodes"][node["node"]]["cpu_used"] = node["cpu"] * node["maxcpu"]
                nodes["nodes"][node["node"]]["cpu_free"] = (node["maxcpu"]) - (node["cpu"] * node["maxcpu"])
                nodes["nodes"][node["node"]]["cpu_assigned_percent"] = nodes["nodes"][node["node"]]["cpu_assigned"] / nodes["nodes"][node["node"]]["cpu_total"] * 100
                nodes["nodes"][node["node"]]["cpu_free_percent"] = nodes["nodes"][node["node"]]["cpu_free"] / node["maxcpu"] * 100
                nodes["nodes"][node["node"]]["cpu_used_percent"] = nodes["nodes"][node["node"]]["cpu_used"] / node["maxcpu"] * 100
                nodes["nodes"][node["node"]]["cpu_pressure_some_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "cpu", "some")
                nodes["nodes"][node["node"]]["cpu_pressure_full_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "cpu", "full")
                nodes["nodes"][node["node"]]["cpu_pressure_some_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "cpu", "some", spikes=True)
                nodes["nodes"][node["node"]]["cpu_pressure_full_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "cpu", "full", spikes=True)
                nodes["nodes"][node["node"]]["cpu_pressure_hot"] = False
                nodes["nodes"][node["node"]]["memory_total"] = Nodes.set_node_resource_reservation(node["node"], node["maxmem"], proxlb_config, "memory")
                nodes["nodes"][node["node"]]["memory_assigned"] = 0
                nodes["nodes"][node["node"]]["memory_used"] = node["mem"]
                nodes["nodes"][node["node"]]["memory_free"] = node["maxmem"] - node["mem"]
                nodes["nodes"][node["node"]]["memory_assigned_percent"] = nodes["nodes"][node["node"]]["memory_assigned"] / nodes["nodes"][node["node"]]["memory_total"] * 100
                nodes["nodes"][node["node"]]["memory_free_percent"] = nodes["nodes"][node["node"]]["memory_free"] / node["maxmem"] * 100
                nodes["nodes"][node["node"]]["memory_used_percent"] = nodes["nodes"][node["node"]]["memory_used"] / node["maxmem"] * 100
                nodes["nodes"][node["node"]]["memory_pressure_some_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "memory", "some")
                nodes["nodes"][node["node"]]["memory_pressure_full_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "memory", "full")
                nodes["nodes"][node["node"]]["memory_pressure_some_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "memory", "some", spikes=True)
                nodes["nodes"][node["node"]]["memory_pressure_full_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "memory", "full", spikes=True)
                nodes["nodes"][node["node"]]["memory_pressure_hot"] = False
                nodes["nodes"][node["node"]]["disk_total"] = node["maxdisk"]
                nodes["nodes"][node["node"]]["disk_assigned"] = 0
                nodes["nodes"][node["node"]]["disk_used"] = node["disk"]
                nodes["nodes"][node["node"]]["disk_free"] = node["maxdisk"] - node["disk"]
                nodes["nodes"][node["node"]]["disk_assigned_percent"] = nodes["nodes"][node["node"]]["disk_assigned"] / nodes["nodes"][node["node"]]["disk_total"] * 100
                nodes["nodes"][node["node"]]["disk_free_percent"] = nodes["nodes"][node["node"]]["disk_free"] / node["maxdisk"] * 100
                nodes["nodes"][node["node"]]["disk_used_percent"] = nodes["nodes"][node["node"]]["disk_used"] / node["maxdisk"] * 100
                nodes["nodes"][node["node"]]["disk_pressure_some_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "disk", "some")
                nodes["nodes"][node["node"]]["disk_pressure_full_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "disk", "full")
                nodes["nodes"][node["node"]]["disk_pressure_some_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "disk", "some", spikes=True)
                nodes["nodes"][node["node"]]["disk_pressure_full_spikes_percent"] = Nodes.get_node_rrd_data(proxmox_api, node["node"], "disk", "full", spikes=True)
                nodes["nodes"][node["node"]]["disk_pressure_hot"] = False

                # Evaluate if node should be set to maintenance mode
                if Nodes.set_node_maintenance(proxmox_api, proxlb_config, node["node"]):
                    nodes["nodes"][node["node"]]["maintenance"] = True

        logger.debug(f"Node metrics collected: {nodes}")
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

    @staticmethod
    def get_node_rrd_data(proxmox_api, node_name: str, object_name: str, object_type: str, spikes=False) -> float:
        """
        Retrieves the rrd data metrics for a specific resource (CPU, memory, disk) of a node.

        Args:
            proxmox_api (Any): The Proxmox API client instance.
            node_name (str): The name of the node hosting the guest.
            object_name (str): The resource type to query (e.g., 'cpu', 'memory', 'disk').
            object_type (str, optional): The pressure type ('some', 'full') or None for average usage.
            spikes (bool, optional): Whether to consider spikes in the calculation. Defaults to False.

        Returns:
            float: The calculated average usage value for the specified resource.
        """
        logger.debug("Starting: get_node_rrd_data.")
        time.sleep(0.1)

        try:
            if spikes:
                logger.debug(f"Getting spike RRD data for {object_name} from node: {node_name}.")
                node_data_rrd = proxmox_api.nodes(node_name).rrddata.get(timeframe="hour", cf="MAX")
            else:
                logger.debug(f"Getting average RRD data for {object_name} from node: {node_name}.")
                node_data_rrd = proxmox_api.nodes(node_name).rrddata.get(timeframe="hour", cf="AVERAGE")

        except Exception:
            logger.error(f"Failed to retrieve RRD data for guest: {node_name}. Using 0.0 as value.")
            logger.debug("Finished: get_node_rrd_data.")
            return 0.0

        lookup_key = f"pressure{object_name}{object_type}"

        if spikes:
            # RRD data is collected every minute, so we look at the last 6 entries
            # and take the maximum value to represent the spike
            rrd_data_value = [row.get(lookup_key) for row in node_data_rrd if row.get(lookup_key) is not None]
            rrd_data_value = max(rrd_data_value[-6:], default=0.0)
        else:
            # Calculate the average value from the RRD data entries
            rrd_data_value = sum(entry.get(lookup_key, 0.0) for entry in node_data_rrd) / len(node_data_rrd)

        logger.debug(f"RRD data (spike: {spikes}) for {object_name} from node: {node_name}: {rrd_data_value}")
        logger.debug("Finished: get_node_rrd_data.")
        return rrd_data_value

    @staticmethod
    def get_node_pve_version(proxmox_api, node_name: str) -> float:
        """
        Return the Proxmox VE (PVE) version for a given node by querying the Proxmox API.

        This function calls proxmox_api.nodes(node_name).version.get() and extracts the
        'version' field from the returned mapping. The value is expected to be numeric
        (or convertible to float) and is returned as a float.

        Args:
            proxmox_api (Any): The Proxmox API client instance.
            node_name (str): The name of the node hosting the guest.

        Returns:
            float: The PVE version for the specified node as a floating point number.

        Raises:
        Exception: If the proxmox_api call fails, returns an unexpected structure, or the
                   'version' field is missing or cannot be converted to float. Callers should
                    handle or propagate exceptions as appropriate.
        """
        logger.debug("Starting: get_node_pve_version.")
        time.sleep(0.1)

        try:
            logger.debug(f"Trying to get PVE version for node: {node_name}.")
            version = proxmox_api.nodes(node_name).version.get()
        except Exception:
            logger.error(f"Failed to get PVE version for node: {node_name}.")

        logger.debug(f"Got version {version['version']} for node {node_name}.")
        logger.debug("Finished: get_node_pve_version.")
        return version["version"]

    @staticmethod
    def set_node_resource_reservation(node_name, resource_value, proxlb_config, resource_type) -> int:
        """
        Check if there is a configured resource reservation for the current node and apply it as needed.
        Checks for a node specific config first, then if there is any configured default and if neither then nothing is reserved.
        Reservations are applied by directly modifying the resource value.

        Args:
            node_name (str):                    The name of the node.
            resource_value (int):               The total resource value in bytes.
            proxlb_config (Dict[str, Any]):     A dictionary containing the ProxLB configuration.
            resource_type (str):                The type of resource ('memory', 'disk', etc.).

        Returns:
            int:                                The resource value after applying any configured reservations.
        """
        logger.debug(f"Starting: apply_resource_reservation")

        balancing_cfg = proxlb_config.get("balancing", {})
        reserve_cfg = balancing_cfg.get("node_resource_reserve", {})
        node_resource_reservation = reserve_cfg.get(node_name, {}).get(resource_type, 0)
        default_resource_reservation = reserve_cfg.get("defaults", {}).get(resource_type, 0)

        # Ensure reservations are numeric values
        node_resource_reservation = node_resource_reservation if isinstance(node_resource_reservation, (int, float)) else 0
        default_resource_reservation = default_resource_reservation if isinstance(default_resource_reservation, (int, float)) else 0

        # Apply node specific reservation if set
        if node_resource_reservation > 0:
            if resource_value < (node_resource_reservation * 1024 ** 3):
                logger.critical(f"Configured resource reservation for node {node_name} of type {resource_type} with {node_resource_reservation} GB is higher than available resource value {resource_value / (1024 ** 3):.2f} GB. Not applying...")
                return resource_value
            else:
                logger.debug(f"Applying node specific reservation for {node_name} of type {resource_type} with {node_resource_reservation} GB.")
                resource_value_new = resource_value - (node_resource_reservation * 1024 ** 3)
                logger.debug(f'Switched resource value for node {node_name} of type {resource_type} from {resource_value / (1024 ** 3):.2f} GB to {resource_value_new / (1024 ** 3):.2f} GB after applying reservation.')
                logger.debug(f"Before: {resource_value} | After: {resource_value_new}")
                return resource_value_new

        # Apply default reservation if set and no node specific reservation has been performed
        elif default_resource_reservation > 0:
            if resource_value < (default_resource_reservation * 1024 ** 3):
                logger.critical(f"Configured default reservation for node {node_name} of type {resource_type} with {default_resource_reservation} GB is higher than available resource value {resource_value / (1024 ** 3):.2f} GB. Not applying...")
                return resource_value
            else:
                logger.debug(f"Applying default reservation for {node_name} of type {resource_type} with {default_resource_reservation} GB.")
                resource_value_new = resource_value - (default_resource_reservation * 1024 ** 3)
                logger.debug(f'Switched resource value for node {node_name} of type {resource_type} from {resource_value / (1024 ** 3):.2f} GB to {resource_value_new / (1024 ** 3):.2f} GB after applying reservation.')
                logger.debug(f"Before: {resource_value} | After: {resource_value_new}")
                return resource_value_new

        else:
            logger.debug(f"No default or node specific resource reservation for node {node_name} found. Skipping...")
            logger.debug(f"Finished: apply_resource_reservation")
            return resource_value
