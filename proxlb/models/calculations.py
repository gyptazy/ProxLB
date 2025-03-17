"""
The Calculations class is responsible for handling the balancing of virtual machines (VMs)
and containers (CTs) across all available nodes in a Proxmox cluster. It provides methods
to calculate the optimal distribution of VMs and CTs based on the provided data.
"""


__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import sys
from typing import Dict, Any
from utils.logger import SystemdLogger

logger = SystemdLogger()


class Calculations:
    """
    The calculation class is responsible for handling the balancing of virtual machines (VMs)
    and containers (CTs) across all available nodes in a Proxmox cluster. It provides methods
    to calculate the optimal distribution of VMs and CTs based on the provided data.

    Methods:
    __init__(proxlb_data: Dict[str, Any]):
        Initializes the Calculation class with the provided ProxLB data.

    set_node_assignments(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        Sets the assigned resources of the nodes based on the current assigned
        guest resources by their created groups as an initial base.

    get_balanciness(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        Gets the balanciness for further actions where the highest and lowest
        usage or assignments of Proxmox nodes are compared.

    get_most_free_node(proxlb_data: Dict[str, Any], return_node: bool = False) -> Dict[str, Any]:
        Gets the name of the Proxmox node in the cluster with the most free resources based on
        the user-defined method (e.g., memory) and mode (e.g., used).

    relocate_guests_on_maintenance_nodes(proxlb_data: Dict[str, Any]):
        Relocates guests that are currently on nodes marked for maintenance to
        nodes with the most available resources.

    relocate_guests(proxlb_data: Dict[str, Any]):
        Relocates guests within the provided data structure to ensure affinity groups are
        placed on nodes with the most free resources.

    val_anti_affinity(proxlb_data: Dict[str, Any], guest_name: str):
        Validates and assigns nodes to guests based on anti-affinity rules.

    update_node_resources(proxlb_data):
        Updates the resource allocation and usage statistics for nodes when a guest
        is moved from one node to another.
    """

    def __init__(self, proxlb_data: Dict[str, Any]):
        """
        Initializes the Calculation class with the provided ProxLB data.

        Args:
            proxlb_data (Dict[str, Any]): The data required for balancing VMs and CTs.
        """

    @staticmethod
    def set_node_assignments(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the assigned ressources of the nodes based on the current assigned
        guest resources by their created groups as an initial base.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all current statistics.

        Returns:
            Dict[str, Any]: Updated ProxLB data of nodes section with updated node assigned values.
        """
        logger.debug("Starting: set_node_assignments.")
        for group_name, group_meta in proxlb_data["groups"]["affinity"].items():

            for guest_name in group_meta["guests"]:
                guest_node_current = proxlb_data["guests"][guest_name]["node_current"]
                # Update Hardware assignments
                # Update assigned values for the current node
                proxlb_data["nodes"][guest_node_current]["cpu_assigned"] += proxlb_data["guests"][guest_name]["cpu_total"]
                proxlb_data["nodes"][guest_node_current]["memory_assigned"] += proxlb_data["guests"][guest_name]["memory_total"]
                proxlb_data["nodes"][guest_node_current]["disk_assigned"] += proxlb_data["guests"][guest_name]["disk_total"]
                # Update assigned percentage values for the current node
                proxlb_data["nodes"][guest_node_current]["cpu_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["cpu_assigned"] / proxlb_data["nodes"][guest_node_current]["cpu_total"] * 100
                proxlb_data["nodes"][guest_node_current]["memory_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["memory_assigned"] / proxlb_data["nodes"][guest_node_current]["memory_total"] * 100
                proxlb_data["nodes"][guest_node_current]["disk_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["disk_assigned"] / proxlb_data["nodes"][guest_node_current]["disk_total"] * 100

        logger.debug("Finished: set_node_assignments.")

    @staticmethod
    def get_balanciness(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the blanaciness for further actions where the highest and lowest
        usage or assignments of Proxmox nodes are compared. Based on the users
        provided balanciness delta the balancing will be performed.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
            Dict[str, Any]: Updated meta data section of the balanciness action defined
                  as a bool.
        """
        logger.debug("Starting: get_balanciness.")
        proxlb_data["meta"]["balancing"]["balance"] = False

        if len(proxlb_data["groups"]) > 0:
            method = proxlb_data["meta"]["balancing"].get("method", "memory")
            mode = proxlb_data["meta"]["balancing"].get("mode", "used")
            balanciness = proxlb_data["meta"]["balancing"].get("balanciness", 10)
            method_value = [node_meta[f"{method}_{mode}_percent"] for node_meta in proxlb_data["nodes"].values()]
            method_value_highest = max(method_value)
            method_value_lowest = min(method_value)

            if method_value_highest - method_value_lowest > balanciness:
                proxlb_data["meta"]["balancing"]["balance"] = True
                logger.debug(f"Guest balancing is required. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")
                logger.critical(f"Guest balancing is required. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")
            else:
                logger.debug(f"Guest balancing is ok. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")
                logger.critical(f"Guest balancing is ok. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")

        else:
            logger.warning("No guests for balancing found.")

        logger.debug("Finished: get_balanciness.")

    @staticmethod
    def get_most_free_node(proxlb_data: Dict[str, Any], return_node: bool = False) -> Dict[str, Any]:
        """
        Get the name of the Proxmox node in the cluster with the most free resources based on
        the user defined method (e.g.: memory) and mode (e.g.: used).

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
            return_node (bool): The indicator to simply return the best node for further
                                assignments.

        Returns:
            Dict[str, Any]: Updated meta data section of the node with the most free resources that should
                  be used for the next balancing action.
        """
        logger.debug("Starting: get_most_free_node.")
        proxlb_data["meta"]["balancing"]["balance_next_node"] = ""

        # Do not include nodes that are marked in 'maintenance'
        filtered_nodes = [node for node in proxlb_data["nodes"].values() if not node["maintenance"]]
        lowest_usage_node = min(filtered_nodes, key=lambda x: x["memory_used_percent"])
        proxlb_data["meta"]["balancing"]["balance_reason"] = 'resources'
        proxlb_data["meta"]["balancing"]["balance_next_node"] = lowest_usage_node["name"]

        # If executed to simply get the best node for further usage, we return
        # the best node on stdout and gracefully exit here
        if return_node:
            print(lowest_usage_node["name"])
            sys.exit(0)

        logger.debug("Finished: get_most_free_node.")

    @staticmethod
    def relocate_guests_on_maintenance_nodes(proxlb_data: Dict[str, Any]):
        """
        Relocates guests that are currently on nodes marked for maintenance to
        nodes with the most available resources.

        This function iterates over all guests on maintenance nodes and attempts
        to relocate them to nodes with the most free resources that are not in
        maintenance mode. It updates the node resources accordingly and logs
        warnings if the balancing may not be perfect due to the maintenance
        status of the original node.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
        None
        """
        logger.debug("Starting: get_most_free_node.")
        proxlb_data["meta"]["balancing"]["balance_next_guest"] = ""

        for guest_name in proxlb_data["groups"]["maintenance"]:
            # Update the node with the most free nodes which is
            # not in a maintenance
            proxlb_data["meta"]["balancing"]["balance_next_guest"] = guest_name
            Calculations.get_most_free_node(proxlb_data)
            Calculations.update_node_resources(proxlb_data)
            logger.warning(f"Warning: Balancing may not be perfect because guest {guest_name} was located on a node which is in maintenance mode.")

        logger.debug("Finished: get_most_free_node.")

    @staticmethod
    def relocate_guests(proxlb_data: Dict[str, Any]):
        """
        Relocates guests within the provided data structure to ensure affinity groups are
        placed on nodes with the most free resources.

        This function iterates over each affinity group in the provided data, identifies
        the node with the most free resources, and migrates all guests within the group
        to that node. It updates the node resources accordingly.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
        None
        """
        logger.debug("Starting: relocate_guests.")
        if proxlb_data["meta"]["balancing"]["balance"] or proxlb_data["meta"]["balancing"]["enforce_affinity"]:

            if proxlb_data["meta"]["balancing"].get("balance", False):
                logger.debug("Balancing of guests will be performt. Reason: balanciness")

            if proxlb_data["meta"]["balancing"].get("enforce_affinity", False):
                logger.debug("Balancing of guests will be performt. Reason: enforce affinity balancing")

            for group_name in proxlb_data["groups"]["affinity"]:

                # We get initially the node with the most free resources and then
                # migrate all guests within the group to that node to ensure the
                # affinity.
                Calculations.get_most_free_node(proxlb_data)

                for guest_name in proxlb_data["groups"]["affinity"][group_name]["guests"]:
                    proxlb_data["meta"]["balancing"]["balance_next_guest"] = guest_name
                    Calculations.val_anti_affinity(proxlb_data, guest_name)
                    Calculations.update_node_resources(proxlb_data)

        logger.debug("Finished: relocate_guests.")

    @staticmethod
    def val_anti_affinity(proxlb_data: Dict[str, Any], guest_name: str):
        """
        Validates and assigns nodes to guests based on anti-affinity rules.

        This function iterates over all defined anti-affinity groups in the provided
        `proxlb_data` and checks if the specified `guest_name` is included in any of
        these groups. If the guest is included and has not been processed yet, it
        attempts to assign an unused and non-maintenance node to the guest, ensuring
        that the anti-affinity rules are respected.

        Parameters:
        proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        guest_name (str): The name of the guest to be validated and assigned a node.

        Returns:
        None
        """
        logger.debug("Starting: val_anti_affinity.")
        # Start by interating over all defined anti-affinity groups
        for group_name in proxlb_data["groups"]["anti_affinity"].keys():

            # Validate if the provided guest ist included in the anti-affinity group
            if guest_name in proxlb_data["groups"]["anti_affinity"][group_name]['guests'] and not proxlb_data["guests"][guest_name]["processed"]:
                logger.debug(f"Anti-Affinity: Guest: {guest_name} is included in anti-affinity group: {group_name}.")

                # Iterate over all available nodes
                for node_name in proxlb_data["nodes"].keys():

                    # Only select node if it was not used before and is not in a
                    # maintenance mode. Afterwards, add it to the list of already
                    # used nodes for the current anti-affinity group
                    if node_name not in proxlb_data["groups"]["anti_affinity"][group_name]["used_nodes"]:

                        if not proxlb_data["nodes"][node_name]["maintenance"]:
                            # If the node has not been used yet, we assign this node to the guest
                            proxlb_data["meta"]["balancing"]["balance_next_node"] = node_name
                            proxlb_data["groups"]["anti_affinity"][group_name]["used_nodes"].append(node_name)
                            logger.debug(f"Node: {node_name} marked as used for anti-affinity group: {group_name} with guest {guest_name}")
                            break

                    else:
                        logger.critical(f"Node: {node_name} already got used for anti-affinity group:: {group_name}. (Tried for guest: {guest_name})")

            else:
                logger.debug(f"Guest: {guest_name} is not included in anti-affinity group: {group_name}. Skipping.")

        logger.debug("Finished: val_anti_affinity.")

    @staticmethod
    def update_node_resources(proxlb_data):
        """
        Updates the resource allocation and usage statistics for nodes when a guest
        is moved from one node to another.

        Parameters:
        proxlb_data (dict): A dictionary containing information about the nodes and
        guests, including their resource allocations and usage.

        The function performs the following steps:
        1. Retrieves the guest name, current node, and target node from the provided data.
        2. Updates the resource allocations and usage statistics for the target node by
           adding the resources of the moved guest.
        3. Updates the resource allocations and usage statistics for the current node by
           subtracting the resources of the moved guest.
        4. Logs the start and end of the resource update process, as well as the movement
           of the guest from the current node to the target node.
        """
        logger.debug("Starting: update_node_resources.")
        guest_name = proxlb_data["meta"]["balancing"]["balance_next_guest"]
        node_current = proxlb_data["guests"][guest_name]["node_current"]
        node_target = proxlb_data["meta"]["balancing"]["balance_next_node"]

        # Update resources for the target node by the moved guest resources
        # Add assigned resources to the target node
        proxlb_data["nodes"][node_target]["cpu_assigned"] += proxlb_data["guests"][guest_name]["cpu_total"]
        proxlb_data["nodes"][node_target]["memory_assigned"] += proxlb_data["guests"][guest_name]["memory_total"]
        proxlb_data["nodes"][node_target]["disk_assigned"] += proxlb_data["guests"][guest_name]["disk_total"]
        # Update the assigned percentages of assigned resources for the target node
        proxlb_data["nodes"][node_target]["cpu_assigned_percent"] = proxlb_data["nodes"][node_target]["cpu_assigned"] / proxlb_data["nodes"][node_target]["cpu_total"] * 100
        proxlb_data["nodes"][node_target]["memory_assigned_percent"] = proxlb_data["nodes"][node_target]["memory_assigned"] / proxlb_data["nodes"][node_target]["memory_total"] * 100
        proxlb_data["nodes"][node_target]["disk_assigned_percent"] = proxlb_data["nodes"][node_target]["disk_assigned"] / proxlb_data["nodes"][node_target]["disk_total"] * 100
        # Add used resources to the target node
        proxlb_data["nodes"][node_target]["cpu_used"] += proxlb_data["guests"][guest_name]["cpu_used"]
        proxlb_data["nodes"][node_target]["memory_used"] += proxlb_data["guests"][guest_name]["memory_used"]
        proxlb_data["nodes"][node_target]["disk_used"] += proxlb_data["guests"][guest_name]["disk_used"]
        # Update the used percentages of usage resources for the target node
        proxlb_data["nodes"][node_target]["cpu_used_percent"] = proxlb_data["nodes"][node_target]["cpu_used"] / proxlb_data["nodes"][node_target]["cpu_total"] * 100
        proxlb_data["nodes"][node_target]["memory_used_percent"] = proxlb_data["nodes"][node_target]["memory_used"] / proxlb_data["nodes"][node_target]["memory_total"] * 100
        proxlb_data["nodes"][node_target]["disk_used_percent"] = proxlb_data["nodes"][node_target]["disk_used"] / proxlb_data["nodes"][node_target]["disk_total"] * 100

        # Update resources for the current node by the moved guest resources
        # Add assigned resources to the target node
        proxlb_data["nodes"][node_current]["cpu_assigned"] -= proxlb_data["guests"][guest_name]["cpu_total"]
        proxlb_data["nodes"][node_current]["memory_assigned"] -= proxlb_data["guests"][guest_name]["memory_total"]
        proxlb_data["nodes"][node_current]["disk_assigned"] -= proxlb_data["guests"][guest_name]["disk_total"]
        # Update the assigned percentages of assigned resources for the target node
        proxlb_data["nodes"][node_current]["cpu_assigned_percent"] = proxlb_data["nodes"][node_current]["cpu_assigned"] / proxlb_data["nodes"][node_current]["cpu_total"] * 100
        proxlb_data["nodes"][node_current]["memory_assigned_percent"] = proxlb_data["nodes"][node_current]["memory_assigned"] / proxlb_data["nodes"][node_current]["memory_total"] * 100
        proxlb_data["nodes"][node_current]["disk_assigned_percent"] = proxlb_data["nodes"][node_current]["disk_assigned"] / proxlb_data["nodes"][node_current]["disk_total"] * 100
        # Add used resources to the target node
        proxlb_data["nodes"][node_current]["cpu_used"] -= proxlb_data["guests"][guest_name]["cpu_used"]
        proxlb_data["nodes"][node_current]["memory_used"] -= proxlb_data["guests"][guest_name]["memory_used"]
        proxlb_data["nodes"][node_current]["disk_used"] -= proxlb_data["guests"][guest_name]["disk_used"]
        # Update the used percentages of usage resources for the target node
        proxlb_data["nodes"][node_current]["cpu_used_percent"] = proxlb_data["nodes"][node_current]["cpu_used"] / proxlb_data["nodes"][node_current]["cpu_total"] * 100
        proxlb_data["nodes"][node_current]["memory_used_percent"] = proxlb_data["nodes"][node_current]["memory_used"] / proxlb_data["nodes"][node_current]["memory_total"] * 100
        proxlb_data["nodes"][node_current]["disk_used_percent"] = proxlb_data["nodes"][node_current]["disk_used"] / proxlb_data["nodes"][node_current]["disk_total"] * 100

        # Assign guest to the new target node
        proxlb_data["guests"][guest_name]["node_target"] = node_target
        logger.debug(f"Set guest {guest_name} from node {node_current} to node {node_target}.")

        logger.debug("Finished: update_node_resources.")
