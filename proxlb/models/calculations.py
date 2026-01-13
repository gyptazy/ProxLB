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
        Set the assigned resources of the nodes based on the current assigned
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
                # Update resource assignments
                # Update assigned values for the current node
                logger.debug(f"set_node_assignment of guest {guest_name} on node {guest_node_current} with cpu_total: {proxlb_data['guests'][guest_name]['cpu_total']}, memory_total: {proxlb_data['guests'][guest_name]['memory_total']}, disk_total: {proxlb_data['guests'][guest_name]['disk_total']}.")
                proxlb_data["nodes"][guest_node_current]["cpu_assigned"] += proxlb_data["guests"][guest_name]["cpu_total"]
                proxlb_data["nodes"][guest_node_current]["memory_assigned"] += proxlb_data["guests"][guest_name]["memory_total"]
                proxlb_data["nodes"][guest_node_current]["disk_assigned"] += proxlb_data["guests"][guest_name]["disk_total"]
                # Update assigned percentage values for the current node
                proxlb_data["nodes"][guest_node_current]["cpu_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["cpu_assigned"] / proxlb_data["nodes"][guest_node_current]["cpu_total"] * 100
                proxlb_data["nodes"][guest_node_current]["memory_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["memory_assigned"] / proxlb_data["nodes"][guest_node_current]["memory_total"] * 100
                proxlb_data["nodes"][guest_node_current]["disk_assigned_percent"] = proxlb_data["nodes"][guest_node_current]["disk_assigned"] / proxlb_data["nodes"][guest_node_current]["disk_total"] * 100

        logger.debug("Finished: set_node_assignments.")

    def set_node_hot(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates node 'full' pressure metrics for memory, cpu, and io
        against defined thresholds and sets <metric>_pressure_hot = True
        when a node is considered HOT.

        Returns the modified proxlb_data dict.
        """
        logger.debug("Starting: set_node_hot.")
        balancing_cfg = proxlb_data.get("meta", {}).get("balancing", {})
        thresholds = balancing_cfg.get("psi_thresholds", balancing_cfg.get("psi", {}).get("nodes", {}))
        nodes = proxlb_data.get("nodes", {})

        for node_name, node in nodes.items():

            if node.get("maintenance"):
                continue

            if node.get("ignore"):
                continue

            # PSI metrics are only availavble on Proxmox VE 9.0 and higher.
            if proxlb_data["meta"]["balancing"].get("mode", "used") == "psi":

                if tuple(map(int, proxlb_data["nodes"][node["name"]]["pve_version"].split('.'))) < tuple(map(int, "9.0".split('.'))):
                    logger.critical(f"Proxmox node {node['name']} runs Proxmox VE version {proxlb_data['nodes'][node['name']]['pve_version']}."
                                    " PSI metrics require Proxmox VE 9.0 or higher. Balancing deactivated!")

            for metric, threshold in thresholds.items():
                pressure_full = node.get(f"{metric}_pressure_full_percent", 0.0)
                pressure_some = node.get(f"{metric}_pressure_some_percent", 0.0)
                pressure_spikes = node.get(f"{metric}_pressure_full_spikes_percent", 0.0)
                is_hot = (pressure_full >= threshold["pressure_full"] and pressure_some >= threshold["pressure_some"]) or (pressure_spikes >= threshold["pressure_spikes"])

                if is_hot:
                    logger.debug(f"Set node {node['name']} as hot based on {metric} pressure metrics.")
                    proxlb_data["nodes"][node["name"]][f"{metric}_pressure_hot"] = True
                    proxlb_data["nodes"][node["name"]][f"pressure_hot"] = True
                else:
                    logger.debug(f"Node {node['name']} is not hot based on {metric} pressure metrics.")

        logger.debug("Finished: set_node_hot.")
        return proxlb_data

    def set_guest_hot(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates guest 'full' pressure metrics for memory, cpu, and io
        against defined thresholds and sets <metric>_pressure_hot = True
        when a guest is considered HOT.

        Returns the modified proxlb_data dict.
        """
        logger.debug("Starting: set_guest_hot.")
        balancing_cfg = proxlb_data.get("meta", {}).get("balancing", {})
        thresholds = balancing_cfg.get("psi_thresholds", balancing_cfg.get("psi", {}).get("guests", {}))
        guests = proxlb_data.get("guests", {})

        for guest_name, guest in guests.items():
            if guest.get("ignore"):
                continue

            for metric, threshold in thresholds.items():
                pressure_full = guest.get(f"{metric}_pressure_full_percent", 0.0)
                pressure_some = guest.get(f"{metric}_pressure_some_percent", 0.0)
                pressure_spikes = guest.get(f"{metric}_pressure_full_spikes_percent", 0.0)
                is_hot = (pressure_full >= threshold["pressure_full"] and pressure_some >= threshold["pressure_some"]) or (pressure_spikes >= threshold["pressure_spikes"])

                if is_hot:
                    logger.debug(f"Set guest {guest['name']} as hot based on {metric} pressure metrics.")
                    proxlb_data["guests"][guest["name"]][f"{metric}_pressure_hot"] = True
                    proxlb_data["guests"][guest["name"]][f"pressure_hot"] = True
                else:
                    logger.debug(f"guest {guest['name']} is not hot based on {metric} pressure metrics.")

        logger.debug("Finished: set_guest_hot.")
        return proxlb_data

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

            if mode == "assigned":
                method_value = [node_meta[f"{method}_{mode}_percent"] for node_meta in proxlb_data["nodes"].values()]

                if proxlb_data["meta"]["balancing"].get(f"{method}_threshold", None):
                    threshold = proxlb_data["meta"]["balancing"].get(f"{method}_threshold")
                    highest_usage_node = max(proxlb_data["nodes"].values(), key=lambda x: x[f"{method}_{mode}_percent"])
                    highest_node_value = highest_usage_node[f"{method}_{mode}_percent"]

                    if highest_node_value >= threshold:
                        logger.debug(f"Guest balancing is required. Highest {method} usage node {highest_usage_node['name']} is above the defined threshold of {threshold}% with a value of {highest_node_value}%.")
                        proxlb_data["meta"]["balancing"]["balance"] = True
                    else:
                        logger.debug(f"Guest balancing is ok. Highest {method} usage node {highest_usage_node['name']} is below the defined threshold of {threshold}% with a value of {highest_node_value}%.")
                        proxlb_data["meta"]["balancing"]["balance"] = False

                else:
                    logger.debug(f"No {method} threshold defined for balancing. Skipping threshold check.")

            elif mode == "used":
                method_value = [node_meta[f"{method}_{mode}_percent"] for node_meta in proxlb_data["nodes"].values()]

                if proxlb_data["meta"]["balancing"].get(f"{method}_threshold", None):
                    threshold = proxlb_data["meta"]["balancing"].get(f"{method}_threshold")
                    highest_usage_node = max(proxlb_data["nodes"].values(), key=lambda x: x[f"{method}_{mode}_percent"])
                    highest_node_value = highest_usage_node[f"{method}_{mode}_percent"]

                    if highest_node_value >= threshold:
                        logger.debug(f"Guest balancing is required. Highest {method} usage node {highest_usage_node['name']} is above the defined threshold of {threshold}% with a value of {highest_node_value}%.")
                        proxlb_data["meta"]["balancing"]["balance"] = True
                    else:
                        logger.debug(f"Guest balancing is ok. Highest {method} usage node {highest_usage_node['name']} is below the defined threshold of {threshold}% with a value of {highest_node_value}%.")
                        proxlb_data["meta"]["balancing"]["balance"] = False

                else:
                    logger.debug(f"No {method} threshold defined for balancing. Skipping threshold check.")

            elif mode == "psi":
                method_value = [node_meta[f"{method}_pressure_full_spikes_percent"] for node_meta in proxlb_data["nodes"].values()]
                any_node_hot = any(node.get(f"{method}_pressure_hot", False) for node in proxlb_data["nodes"].values())
                any_guest_hot = any(node.get(f"{method}_pressure_hot", False) for node in proxlb_data["guests"].values())

                if any_node_hot:
                    logger.debug(f"Guest balancing is required. A node is marked as HOT based on {method} pressure metrics.")
                    proxlb_data["meta"]["balancing"]["balance"] = True
                else:
                    logger.debug(f"Guest balancing is ok. No node is marked as HOT based on {method} pressure metrics.")

                if any_guest_hot:
                    logger.debug(f"Guest balancing is required. A guest is marked as HOT based on {method} pressure metrics.")
                    proxlb_data["meta"]["balancing"]["balance"] = True
                else:
                    logger.debug(f"Guest balancing is ok. No guest is marked as HOT based on {method} pressure metrics.")

                return proxlb_data

            else:
                logger.critical(f"Unknown balancing mode: {mode} provided. Cannot get balanciness.")
                sys.exit(1)

            method_value_highest = max(method_value)
            method_value_lowest = min(method_value)

            if method_value_highest - method_value_lowest > balanciness:
                proxlb_data["meta"]["balancing"]["balance"] = True
                logger.debug(f"Guest balancing is required. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")
            else:
                logger.debug(f"Guest balancing is ok. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")

        else:
            logger.warning("No guests for balancing found.")

        logger.debug("Finished: get_balanciness.")

    @staticmethod
    def get_most_free_node(proxlb_data: Dict[str, Any], return_node: bool = False, guest_node_relation_list: list = []) -> Dict[str, Any]:
        """
        Get the name of the Proxmox node in the cluster with the most free resources based on
        the user defined method (e.g.: memory) and mode (e.g.: used).

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
            return_node (bool): The indicator to simply return the best node for further
                                assignments.
            guest_node_relation_list (list): A list of nodes that have a tag on the given
                                             guest relationship for pinning.

        Returns:
            Dict[str, Any]: Updated meta data section of the node with the most free resources that should
                  be used for the next balancing action.
        """
        logger.debug("Starting: get_most_free_node.")
        proxlb_data["meta"]["balancing"]["balance_next_node"] = ""

        # Filter and exclude nodes that are in maintenance mode
        filtered_nodes = [node for node in proxlb_data["nodes"].values() if not node["maintenance"]]

        # Filter and include nodes that given by a relationship between guest and node. This is only
        # used if the guest has a relationship to a node defined by "pin" tags.
        if len(guest_node_relation_list) > 0:
            filtered_nodes = [node for node in proxlb_data["nodes"].values() if node["name"] in guest_node_relation_list]

        # Filter by the defined methods and modes for balancing
        method = proxlb_data["meta"]["balancing"].get("method", "memory")
        mode = proxlb_data["meta"]["balancing"].get("mode", "used")

        if mode == "assigned":
            logger.debug(f"Get best node for balancing by assigned {method} resources.")
            lowest_usage_node = min(filtered_nodes, key=lambda x: x[f"{method}_{mode}_percent"])

        elif mode == "used":
            logger.debug(f"Get best node for balancing by used {method} resources.")
            lowest_usage_node = min(filtered_nodes, key=lambda x: x[f"{method}_{mode}_percent"])

        elif mode == "psi":
            logger.debug(f"Get best node for balancing by pressure of {method} resources.")
            lowest_usage_node = min(filtered_nodes, key=lambda x: x[f"{method}_pressure_full_spikes_percent"])

        else:
            logger.critical(f"Unknown balancing mode: {mode} provided. Cannot get best node.")
            sys.exit(1)

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
        logger.debug("Starting: relocate_guests_on_maintenance_nodes.")
        proxlb_data["meta"]["balancing"]["balance_next_guest"] = ""

        for guest_name in proxlb_data["groups"]["maintenance"]:
            # Update the node with the most free nodes which is
            # not in a maintenance
            proxlb_data["meta"]["balancing"]["balance_next_guest"] = guest_name
            Calculations.get_most_free_node(proxlb_data)
            Calculations.update_node_resources(proxlb_data)
            logger.warning(f"Warning: Balancing may not be perfect because guest {guest_name} was located on a node which is in maintenance mode.")

        logger.debug("Finished: relocate_guests_on_maintenance_nodes.")

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

        # Balance only if it is required by:
        #  - balanciness
        #  - Affinity/Anti-Affinity rules
        # - Pinning rules
        if proxlb_data["meta"]["balancing"]["balance"] or proxlb_data["meta"]["balancing"].get("enforce_affinity", False) or proxlb_data["meta"]["balancing"].get("enforce_pinning", False):

            if proxlb_data["meta"]["balancing"].get("balance", False):
                logger.debug("Balancing of guests will be performed. Reason: balanciness")

            if proxlb_data["meta"]["balancing"].get("enforce_affinity", False):
                logger.debug("Balancing of guests will be performed. Reason: enforce affinity balancing")

            if proxlb_data["meta"]["balancing"].get("enforce_pinning", False):
                logger.debug("Balancing of guests will be performed. Reason: enforce pinning balancing")

            # Sort guests by used memory
            # Allows processing larger guests first or smaller guests first
            larger_first = proxlb_data.get("meta", {}).get("balancing", {}).get("balance_larger_guests_first", False)

            if larger_first:
                logger.debug("Larger guests will be processed first. (Sorting descending by memory used)")
            else:
                logger.debug("Smaller guests will be processed first. (Sorting ascending by memory used)")

            # Sort affinity groups by number of guests to avoid creating more migrations than needed
            # because of affinity-groups and use afterwards memory for defining smaller/larger guests
            sorted_guest_usage_groups = sorted(
                proxlb_data["groups"]["affinity"],
                key=lambda g: (
                    proxlb_data["groups"]["affinity"][g]["counter"],
                    -proxlb_data["groups"]["affinity"][g]["memory_used"]
                    if larger_first
                    else proxlb_data["groups"]["affinity"][g]["memory_used"],
                )
            )

            # Iterate over all affinity groups
            for group_name in sorted_guest_usage_groups:

                # Validate balanciness again before processing each group
                Calculations.get_balanciness(proxlb_data)
                logger.debug(proxlb_data["meta"]["balancing"]["balance"])

                if (not proxlb_data["meta"]["balancing"]["balance"]) and (not proxlb_data["meta"]["balancing"].get("enforce_affinity", False)) and (not proxlb_data["meta"]["balancing"].get("enforce_pinning", False)):
                    logger.debug("Skipping further guest relocations as balanciness is now ok.")
                    break

                for guest_name in proxlb_data["groups"]["affinity"][group_name]["guests"]:

                    # Stop moving guests if the source node is no longer the most loaded
                    source_node = proxlb_data["guests"][guest_name]["node_current"]
                    method = proxlb_data["meta"]["balancing"].get("method", "memory")
                    mode = proxlb_data["meta"]["balancing"].get("mode", "used")
                    highest_node = max(proxlb_data["nodes"].values(), key=lambda n: n[f"{method}_used_percent"])

                    if highest_node["name"] != source_node:
                        logger.debug(f"Stopping relocation for guest {guest_name}: source node {source_node} is no longer the most loaded node.")
                        break

                    if not Calculations.validate_node_resources(proxlb_data, guest_name):
                        logger.warning(f"Skipping relocation of guest {guest_name} due to insufficient resources on target node {proxlb_data['meta']['balancing']['balance_next_node']}. This might affect affinity group {group_name}.")
                        continue

                    if mode == 'psi':
                        logger.debug(f"Evaluating guest relocation based on {mode} mode.")
                        method = proxlb_data["meta"]["balancing"].get("method", "memory")
                        processed_guests_psi = proxlb_data["meta"]["balancing"].setdefault("processed_guests_psi", [])
                        unprocessed_guests_psi = [guest for guest in proxlb_data["guests"].values() if guest["name"] not in processed_guests_psi]

                        # Filter by the defined methods and modes for balancing
                        highest_usage_guest = max(unprocessed_guests_psi, key=lambda x: x[f"{method}_pressure_full_spikes_percent"])

                        # Append guest to the psi based processed list of guests
                        if highest_usage_guest["name"] == guest_name and guest_name not in proxlb_data["meta"]["balancing"]["processed_guests_psi"]:
                            proxlb_data["meta"]["balancing"]["processed_guests_psi"].append(guest_name)
                            proxlb_data["meta"]["balancing"]["balance_next_guest"] = guest_name

                    else:
                        logger.debug(f"Evaluating guest relocation based on {mode} mode.")
                        proxlb_data["meta"]["balancing"]["balance_next_guest"] = guest_name

                    Calculations.val_anti_affinity(proxlb_data, guest_name)
                    Calculations.val_node_relationships(proxlb_data, guest_name)
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
        # Start by iterating over all defined anti-affinity groups
        for group_name in proxlb_data["groups"]["anti_affinity"].keys():

            # Validate if the provided guest is included in the anti-affinity group
            if guest_name in proxlb_data["groups"]["anti_affinity"][group_name]['guests'] and not proxlb_data["guests"][guest_name]["processed"]:
                logger.debug(f"Anti-Affinity: Guest: {guest_name} is included in anti-affinity group: {group_name}.")

                # Check if the group has only one member. If so skip new guest node assignment.
                if proxlb_data["groups"]["anti_affinity"][group_name]["counter"] > 1:
                    logger.debug(f"Anti-Affinity: Group has more than 1 member.")
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
                    logger.debug(f"Anti-Affinity: Group has less than 2 members. Skipping node calculation for the group.")

            else:
                logger.debug(f"Guest: {guest_name} is not included in anti-affinity group: {group_name}. Skipping.")

        logger.debug("Finished: val_anti_affinity.")

    @staticmethod
    def val_node_relationships(proxlb_data: Dict[str, Any], guest_name: str):
        """
        Validates and assigns guests to nodes based on defined relationships based on tags.

        Parameters:
        proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        guest_name (str): The name of the guest to be validated and assigned a node.

        Returns:
        None
        """
        logger.debug("Starting: val_node_relationships.")
        proxlb_data["guests"][guest_name]["processed"] = True

        if len(proxlb_data["guests"][guest_name]["node_relationships"]) > 0:
            logger.debug(f"Guest '{guest_name}' has relationships defined to node(s): {','.join(proxlb_data['guests'][guest_name]['node_relationships'])}. Pinning to node.")

            # Get the list of nodes that are defined as relationship for the guest
            guest_node_relation_list = proxlb_data["guests"][guest_name]["node_relationships"]

            # Validate if strict relationships are defined. If not, we prefer
            # the most free node in addition to the relationship list.
            if proxlb_data["guests"][guest_name]["node_relationships_strict"]:
                logger.debug(f"Guest '{guest_name}' has strict node relationships defined. Only nodes in the relationship list will be considered for pinning.")
            else:
                logger.debug(f"Guest '{guest_name}' has non-strict node relationships defined. Prefering nodes in the relationship list for pinning.")
                Calculations.get_most_free_node(proxlb_data)
                most_free_node = proxlb_data["meta"]["balancing"]["balance_next_node"]
                guest_node_relation_list.append(most_free_node)

            # Get the most free node from the relationship list, or the most free node overall
            Calculations.get_most_free_node(proxlb_data, False, guest_node_relation_list)

            # Validate if the specified node name is really part of the cluster
            if proxlb_data["meta"]["balancing"]["balance_next_node"] in proxlb_data["nodes"].keys():
                logger.debug(f"Guest '{guest_name}' has a specific relationship defined to node: {proxlb_data['meta']['balancing']['balance_next_node']} is a known hypervisor node in the cluster.")
            else:
                logger.warning(f"Guest '{guest_name}' has a specific relationship defined to node: {proxlb_data['meta']['balancing']['balance_next_node']} but this node name is not known in the cluster!")

        else:
            logger.debug(f"Guest '{guest_name}' does not have any specific node relationships.")

        logger.debug("Finished: val_node_relationships.")

    @staticmethod
    def update_node_resources(proxlb_data: Dict[str, Any]):
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

        if guest_name == "":
            logger.debug("No guest defined to update node resources for.")
            return

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
        if not proxlb_data["guests"][guest_name]["ignore"]:
            proxlb_data["guests"][guest_name]["node_target"] = node_target
            logger.debug(f"Set guest {guest_name} from node {node_current} to node {node_target}.")
        else:
            logger.debug(f"Guest {guest_name} is marked as ignored. Skipping target node assignment.")

        Calculations.recalc_node_statistics(proxlb_data, node_target)
        Calculations.recalc_node_statistics(proxlb_data, node_current)

        logger.debug("Finished: update_node_resources.")

    def validate_affinity_map(proxlb_data: Dict[str, Any]):
        """
        Validates the affinity and anti-affinity constraints for all guests in the ProxLB data structure.

        This function iterates through each guest and checks both affinity and anti-affinity rules.
        If any guest violates these constraints, it sets the enforce_affinity flag to trigger rebalancing
        and skips further validation for efficiency.

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing ProxLB configuration with the following structure:
                - "guests" (list): List of guest identifiers to validate
                - "meta" (dict): Metadata dictionary containing:
                    - "balancing" (dict): Balancing configuration with "enforce_affinity" flag

        Returns:
            None: Modifies proxlb_data in-place by updating the "enforce_affinity" flag in meta.balancing

        Raises:
            None: Function handles validation gracefully and logs outcomes
        """
        logger.debug("Starting: validate_current_affinity.")
        balancing_ok = True

        for guest in proxlb_data["guests"]:

            # We do not need to validate anymore if rebalancing is required
            if balancing_ok is False:
                proxlb_data["meta"]["balancing"]["enforce_affinity"] = True
                logger.debug(f"Rebalancing based on affinity/anti-affinity map is required. Skipping further validation...")
                break

            balancing_state_affinity = Calculations.validate_current_affinity(proxlb_data, guest)
            balancing_state_anti_affinity = Calculations.validate_current_anti_affinity(proxlb_data, guest)
            logger.debug(f"Affinity for guest {guest} is {'valid' if balancing_state_affinity else 'NOT valid'}")
            logger.debug(f"Anti-affinity for guest {guest} is {'valid' if balancing_state_anti_affinity else 'NOT valid'}")

            balancing_ok = balancing_state_affinity and balancing_state_anti_affinity

        if balancing_ok:
            logger.debug(f"Rebalancing based on affinity/anti-affinity map is not required.")
            proxlb_data["meta"]["balancing"]["enforce_affinity"] = False

        logger.debug("Finished: validate_current_affinity.")

    @staticmethod
    def get_guest_node(proxlb_data: Dict[str, Any], guest_name: str) -> str:
        """
        Return a currently assoicated PVE node where the guest is running on.

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing ProxLB configuration.

        Returns:
            node_name_current (str): The name of the current node where the guest runs on.

        """
        return proxlb_data["guests"][guest_name]["node_current"]

    @staticmethod
    def validate_current_affinity(proxlb_data: Dict[str, Any], guest_name: str) -> bool:
        """
        Validate that all guests in affinity groups containing the specified guest are on the same non-maintenance node.

        This function checks affinity group constraints for a given guest. It ensures that:
        1. All guests within an affinity group are located on the same physical node
        2. The node hosting the affinity group is not in maintenance mode

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing the complete ProxLB state including:
                - "groups": Dictionary with "affinity" key containing affinity group definitions
                - "guests": Dictionary with guest information
                - "nodes": Dictionary with node information including maintenance status
            guest_name (str): The name of the guest to validate affinity for

        Returns:
            bool: True if all affinity groups containing the guest are valid (all members on same
                non-maintenance node), False otherwise
        """
        logger.debug("Starting: validate_current_affinity.")
        for group_name, grp in proxlb_data["groups"]["affinity"].items():
            if guest_name not in grp["guests"]:
                continue

            nodes = []
            for group in grp["guests"]:
                if group not in proxlb_data["guests"]:
                    continue

                node = Calculations.get_guest_node(proxlb_data, group)
                if proxlb_data["nodes"][node]["maintenance"]:
                    logger.debug(f"Group '{group_name}' invalid: node '{node}' in maintenance.")
                    return False
                nodes.append(node)

            if len(set(nodes)) != 1:
                logger.debug(f"Group '{group_name}' invalid: guests spread across nodes {set(nodes)}.")
                return False

        return True

    @staticmethod
    def validate_current_anti_affinity(proxlb_data: Dict[str, Any], guest_name: str) -> bool:
        """
        Validate that all guests in anti-affinity groups containing the specified guest are not on the same node.

        This function checks anti-affinity group constraints for a given guest. It ensures that:
        1. All guests within an anti-affinity group are located on the same physical node
        2. The node hosting the anti-affinity group is not in maintenance mode

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing the complete ProxLB state including:
                - "groups": Dictionary with "affinity" key containing affinity group definitions
                - "guests": Dictionary with guest information
                - "nodes": Dictionary with node information including maintenance status
            guest_name (str): The name of the guest to validate affinity for

        Returns:
            bool: True if all anti-affinity groups containing the guest are valid (all members on different
                non-maintenance node), False otherwise
        """
        logger.debug("Starting: validate_current_anti_affinity.")
        for group_name, grp in proxlb_data["groups"]["anti_affinity"].items():
            if guest_name not in grp["guests"]:
                continue
            nodes = []
            for group in grp["guests"]:
                if group not in proxlb_data["guests"]:
                    continue

                node = Calculations.get_guest_node(proxlb_data, group)
                if proxlb_data["nodes"][node]["maintenance"]:
                    return False
                nodes.append(node)

            if len(nodes) != len(set(nodes)):
                return False

        return True

    @staticmethod
    def validate_node_resources(proxlb_data: Dict[str, Any], guest_name: str) -> bool:
        """
        Validate that the target node has sufficient resources to host the specified guest.

        This function checks if the target node, determined by the balancing logic,
        has enough CPU, memory, and disk resources available to accommodate the guest.

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing the complete ProxLB state including:
                - "nodes": Dictionary with node resource information
                - "guests": Dictionary with guest resource requirements
                - "meta": Dictionary with balancing information including target node
            guest_name (str): The name of the guest to validate resources for
        Returns:
            bool: True if the target node has sufficient resources, False otherwise
        """
        logger.debug("Starting: validate_node_resources.")
        node_target = proxlb_data["meta"]["balancing"]["balance_next_node"]

        node_memory_free = proxlb_data["nodes"][node_target]["memory_free"]
        node_cpu_free = proxlb_data["nodes"][node_target]["cpu_free"]
        node_disk_free = proxlb_data["nodes"][node_target]["disk_free"]

        guest_memory_required = proxlb_data["guests"][guest_name]["memory_used"]
        guest_cpu_required = proxlb_data["guests"][guest_name]["cpu_used"]
        guest_disk_required = proxlb_data["guests"][guest_name]["disk_used"]

        if guest_memory_required < node_memory_free:
            logger.debug(f"Node '{node_target}' has sufficient resources ({node_memory_free / (1024 ** 3):.2f} GB free) for guest '{guest_name}'.")
            logger.debug("Finished: validate_node_resources.")
            return True
        else:
            logger.debug(f"Node '{node_target}' lacks sufficient resources ({node_memory_free / (1024 ** 3):.2f} GB free) for guest '{guest_name}'.")
            logger.debug("Finished: validate_node_resources.")
            return False

    @staticmethod
    def recalc_node_statistics(proxlb_data: Dict[str, Any], node_name: str) -> None:
        """
        Recalculates node statistics including free resources and usage percentages.

        This function updates the computed statistics for a node based on its current
        resource allocation and usage. It calculates free resources, usage percentages,
        and assigned percentages for CPU, memory, and disk.

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing the complete ProxLB state including:
            - "nodes": Dictionary with node resource information
            node_name (str): The name of the node to recalculate statistics for

        Returns:
            None: Modifies proxlb_data in-place by updating node statistics
        """
        n = proxlb_data["nodes"][node_name]
        n["cpu_free"] = max(0, n["cpu_total"] - n["cpu_used"])
        n["memory_free"] = max(0, n["memory_total"] - n["memory_used"])
        n["disk_free"] = max(0, n["disk_total"] - n["disk_used"])
        n["cpu_used_percent"] = (n["cpu_used"] / n["cpu_total"] * 100) if n["cpu_total"] else 0
        n["memory_used_percent"] = (n["memory_used"] / n["memory_total"] * 100) if n["memory_total"] else 0
        n["disk_used_percent"] = (n["disk_used"] / n["disk_total"] * 100) if n["disk_total"] else 0
        n["cpu_assigned_percent"] = (n["cpu_assigned"] / n["cpu_total"] * 100) if n["cpu_total"] else 0
        n["memory_assigned_percent"] = (n["memory_assigned"] / n["memory_total"] * 100) if n["memory_total"] else 0
        n["disk_assigned_percent"] = (n["disk_assigned"] / n["disk_total"] * 100) if n["disk_total"] else 0
