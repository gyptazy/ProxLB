"""
The DPM (Dynamic Power Management) class is responsible for the dynamic management
of nodes within a Proxmox cluster, optimizing resource utilization by controlling
node power states based on specified schedules and conditions.

This class provides functionality for:
- Tracking and validating schedules for dynamic power management.
- Shutting down nodes that are underutilized or not needed.
- Starting up nodes using Wake-on-LAN (WOL) based on certain conditions.
- Ensuring that nodes are properly flagged for maintenance and startup/shutdown actions.

The DPM class can operate in different modes, such as static and automatic,
to either perform predefined actions or dynamically adjust based on real-time resource usage.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import proxmoxer
from typing import Dict, Any
from models.calculations import Calculations
from utils.logger import SystemdLogger

logger = SystemdLogger()


class DPM:
    """
    The DPM (Dynamic Power Management) class is responsible for the dynamic management
    of nodes within a Proxmox cluster, optimizing resource utilization by controlling
    node power states based on specified schedules and conditions.

    This class provides functionality for:
    - Tracking and validating schedules for dynamic power management.
    - Shutting down nodes that are underutilized or not needed.
    - Starting up nodes using Wake-on-LAN (WOL) based on certain conditions.
    - Ensuring that nodes are properly flagged for maintenance and startup/shutdown actions.

    The DPM class can operate in different modes, such as static and automatic,
    to either perform predefined actions or dynamically adjust based on real-time resource usage.

    Attributes:
        None directly defined for the class; instead, all actions are based on input data
        and interactions with the Proxmox API and other helper functions.

    Methods:
        __init__(proxlb_data: Dict[str, Any]):
            Initializes the DPM class, checking whether DPM is enabled and operating in the
            appropriate mode (static or auto).

        dpm_static(proxlb_data: Dict[str, Any]) -> None:
            Evaluates the cluster's resource availability and performs static power management
            actions by removing nodes that are not required.

        dpm_shutdown_nodes(proxmox_api, proxlb_data) -> None:
            Shuts down nodes flagged for DPM shutdown by using the Proxmox API, ensuring
            that Wake-on-LAN (WOL) is available for proper node recovery.

        dpm_startup_nodes(proxmox_api, proxlb_data) -> None:
            Powers on nodes that are flagged for startup and are not in maintenance mode,
            leveraging Wake-on-LAN (WOL) functionality.

        dpm_validate_wol_mac(proxmox_api, node) -> None:
            Validates and retrieves the Wake-on-LAN (WOL) MAC address for a given node,
            ensuring that a valid address is set for powering on the node remotely.
    """

    def __init__(self, proxlb_data: Dict[str, Any]):
        """
        Initializes the DPM class with the provided ProxLB data.

        Args:
            proxlb_data (dict): The data required for balancing VMs and CTs.
        """
        logger.debug("Starting: dpm class.")

        if proxlb_data["meta"].get("dpm", {}).get("enable", False):
            logger.debug("DPM function is enabled.")
            mode = proxlb_data["meta"].get("dpm", {}).get("mode", None)

            if mode == "static":
                self.dpm_static(proxlb_data)

            if mode == "auto":
                self.dpm_auto(proxlb_data)

        else:
            logger.debug("DPM function is not enabled.")

        logger.debug("Finished: dpm class.")

    def dpm_static(self, proxlb_data: Dict[str, Any]) -> None:
        """
        Evaluates and performs static Distributed Power Management (DPM) actions based on current cluster state.

        This method monitors cluster resource availability and attempts to reduce the number of active nodes
        when sufficient free resources are available. It ensures a minimum number of nodes remains active
        and prioritizes shutting down nodes with the least utilized resources to minimize impact. Nodes selected
        for shutdown are marked for maintenance and flagged for DPM shutdown.

        Parameters:
            proxlb_data (Dict[str, Any]): A dictionary containing metadata, cluster status, and node-level information
                including resource utilization, configuration settings, and DPM thresholds.

        Returns:
            None: Modifies the input dictionary in-place to reflect updated cluster state and node flags.
        """
        logger.debug("Starting: dpm_static.")

        method = proxlb_data["meta"].get("dpm", {}).get("method", "memory")
        cluster_nodes_overall = proxlb_data["cluster"]["node_count_overall"]
        cluster_nodes_available = proxlb_data["cluster"]["node_count_available"]
        cluster_free_resources_percent = int(proxlb_data["cluster"][f"{method}_free_percent"])
        cluster_free_resources_req_min = proxlb_data["meta"].get("dpm", {}).get("cluster_min_free_resources", 0)
        cluster_mind_nodes = proxlb_data["meta"].get("dpm", {}).get("cluster_min_nodes", 3)
        logger.debug(f"DPM: Cluster Nodes: {cluster_nodes_overall} | Nodes available: {cluster_nodes_available} | Nodes offline: {cluster_nodes_overall - cluster_nodes_available}")

        # Only proceed removing nodes if the cluster has enough resources
        while cluster_free_resources_percent > cluster_free_resources_req_min:
            logger.debug(f"DPM: More free resources {cluster_free_resources_percent}% available than required: {cluster_free_resources_req_min}%. DPM evaluation starting...")

            # Ensure that we have at least a defined minimum of nodes left
            if cluster_nodes_available > cluster_mind_nodes:
                logger.debug(f"DPM: A minimum of {cluster_mind_nodes} nodes is required. {cluster_nodes_available} are available. Proceeding...")

                # Get the node with the fewest used resources to keep migrations low
                Calculations.get_most_free_node(proxlb_data, False)
                dpm_node = proxlb_data["meta"]["balancing"]["balance_next_node"]

                # Perform cluster calculation for evaluating how many nodes can safely leave
                # the cluster. Further object calculations are being processed afterwards by
                # the calculation class
                logger.debug(f"DPM: Removing node {dpm_node} from cluster. Node will be turned off later.")
                Calculations.update_cluster_resources(proxlb_data, dpm_node, "remove")
                cluster_free_resources_percent = int(proxlb_data["cluster"][f"{method}_free_percent"])
                logger.debug(f"DPM: Free cluster resources changed to: {int(proxlb_data['cluster'][f'{method}_free_percent'])}%.")

                # Set node to maintenance and DPM shutdown
                proxlb_data["nodes"][dpm_node]["maintenance"] = True
                proxlb_data["nodes"][dpm_node]["dpm_shutdown"] = True
            else:
                logger.warning(f"DPM: A minimum of {cluster_mind_nodes} nodes is required. {cluster_nodes_available} are available. Cannot proceed!")

        logger.debug(f"DPM: Not enough free resources {cluster_free_resources_percent}% available than required: {cluster_free_resources_req_min}%. DPM evaluation stopped.")
        logger.debug("Finished: dpm_static.")
        return proxlb_data

    @staticmethod
    def dpm_shutdown_nodes(proxmox_api, proxlb_data: Dict[str, Any]) -> None:
        """
        Shuts down cluster nodes that are marked for maintenance and flagged for DPM shutdown.

        This method iterates through the cluster nodes in the provided data and attempts to
        power off any node that has both the 'maintenance' and 'dpm_shutdown' flags set.
        It communicates with the Proxmox API to issue shutdown commands and logs any failures.

        Parameters:
            proxmox_api: An instance of the Proxmox API client used to issue node shutdown commands.
            proxlb_data: A dictionary containing node status information, including flags for
                maintenance and DPM shutdown readiness.

        Returns:
            None: Performs shutdown operations and logs outcomes; modifies no data directly.
        """
        logger.debug("Starting: dpm_shutdown_nodes.")
        for node, node_info in proxlb_data["nodes"].items():

            if node_info["maintenance"] and node_info["dpm_shutdown"]:
                logger.debug(f"DPM: Node: {node} is flagged as maintenance mode and to be powered off.")

                # Ensure that the node has a valid WOL MAC defined. If not
                # we would be unable to power on that system again
                valid_wol_mac = DPM.dpm_validate_wol_mac(proxmox_api, node)

                if valid_wol_mac:
                    try:
                        logger.debug(f"DPM: Shutting down node: {node}.")
                        job_id = proxmox_api.nodes(node).status.post(command="shutdown")
                    except proxmoxer.core.ResourceException as proxmox_api_error:
                        logger.critical(f"DPM: Error while powering off node {node}. Please check job-id: {job_id}")
                        logger.debug(f"DPM: Error while powering off node {node}. Please check job-id: {job_id}")
                else:
                    logger.critical(f"DPM: Node {node} cannot be powered off due to missing WOL MAC. Please define a valid WOL MAC for this node.")

        logger.debug("Finished: dpm_shutdown_nodes.")

    @staticmethod
    def dpm_startup_nodes(proxmox_api, proxlb_data: Dict[str, Any]) -> None:
        """
        Starts uo cluster nodes that are marked for DPM start up.

        This method iterates through the cluster nodes in the provided data and attempts to
        power on any node that is not flagged as 'maintenance' but flagged as 'dpm_startup'.
        It communicates with the Proxmox API to issue poweron commands and logs any failures.

        Parameters:
            proxmox_api: An instance of the Proxmox API client used to issue node startup commands.
            proxlb_data: A dictionary containing node status information, including flags for
                maintenance and DPM shutdown readiness.

        Returns:
            None: Performs poweron operations and logs outcomes; modifies no data directly.
        """
        logger.debug("Starting: dpm_startup_nodes.")
        for node, node_info in proxlb_data["nodes"].items():

            if not node_info["maintenance"]:
                logger.debug(f"DPM: Node: {node} is not in maintenance mode.")

                if node_info["dpm_startup"]:
                    logger.debug(f"DPM: Node: {node} is flagged as to be started.")

                    try:
                        logger.debug(f"DPM: Powering on node: {node}.")
                        # Important: This requires Proxmox Operators to define the
                        # WOL address for each node within the Proxmox webinterface
                        job_id = proxmox_api.nodes().wakeonlan.post(node=node)
                    except proxmoxer.core.ResourceException as proxmox_api_error:
                        logger.critical(f"DPM: Error while powering on node {node}. Please check job-id: {job_id}")
                        logger.debug(f"DPM: Error while powering on node {node}. Please check job-id: {job_id}")

        logger.debug("Finished: dpm_startup_nodes.")

    @staticmethod
    def dpm_validate_wol_mac(proxmox_api, node: Dict[str, Any]) -> str:
        """
        Retrieves and validates the Wake-on-LAN (WOL) MAC address for a specified node.

        This method fetches the MAC address configured for Wake-on-LAN (WOL) from the Proxmox API.
        If the MAC address is found, it is logged. In case of failure to retrieve the address,
        a critical log is generated indicating the absence of a WOL MAC address for the node.

        Parameters:
            proxmox_api: An instance of the Proxmox API client used to query node configurations.
            node: The identifier (name or ID) of the node for which the WOL MAC address is to be validated.

        Returns:
            node_wol_mac_address: The WOL MAC address for the specified node if found, otherwise `None`.
        """
        logger.debug("Starting: dpm_validate_wol_mac.")

        try:
            logger.debug(f"DPM: Getting WOL MAC address for node {node} from API.")
            node_wol_mac_address = proxmox_api.nodes(node).config.get(property="wakeonlan")
            node_wol_mac_address = node_wol_mac_address.get("wakeonlan")
            logger.debug(f"DPM: Node {node} has MAC address: {node_wol_mac_address} for WOL.")
        except proxmoxer.core.ResourceException as proxmox_api_error:
            logger.debug(f"DPM: Failed to get WOL MAC address for node {node} from API.")
            node_wol_mac_address = None
            logger.critical(f"DPM: Node {node} has no MAC address defined for WOL.")

        logger.debug("Finished: dpm_validate_wol_mac.")
        return node_wol_mac_address
