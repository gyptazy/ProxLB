"""
The calculation class is responsible for handling the balancing of virtual machines (VMs)
and containers (CTs) across all available nodes in a Proxmox cluster. It provides methods
to calculate the optimal distribution of VMs and CTs based on the provided data.
"""

import random
from typing import Dict, Any
from utils.logger import SystemdLogger
logger = SystemdLogger()


class Calculations:
    """
    The calculation class is responsible for handling the balancing of virtual machines (VMs)
    and containers (CTs) across all available nodes in a Proxmox cluster. It provides methods
    to calculate the optimal distribution of VMs and CTs based on the provided data.
    """

    def __init__(self, proxlb_data: Dict[str, Any]):
        """
        Initializes the Calculation class with the provided ProxLB data.

        Args:
            proxlb_data (Dict[str, Any]): The data required for balancing VMs and CTs.
        """

    @staticmethod
    def update_node_assignments(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the assigned ressources of the nodes based on the current assigned
        guests of type VMs and CTs to have a starting point.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all current statistics.

        Returns:
            Dict[str, Any]: Updated ProxLB data of nodes section with updated node assigned values.
        """
        logger.debug("Starting: update_node_assignment.")
        for guest, meta in proxlb_data["guests"].items():

            # Update Hardware assignments
            # Update assigned values for the current node
            proxlb_data["nodes"][meta["node_current"]]["cpu_assigned"] += meta["cpu_total"]
            proxlb_data["nodes"][meta["node_current"]]["memory_assigned"] += meta["memory_total"]
            proxlb_data["nodes"][meta["node_current"]]["disk_assigned"] += meta["disk_total"]
            # Update assigned percentage values for the current node
            proxlb_data["nodes"][meta["node_current"]]["cpu_assigned_percent"] = proxlb_data["nodes"][meta["node_current"]]["cpu_assigned"] / proxlb_data["nodes"][meta["node_current"]]["cpu_total"] * 100
            proxlb_data["nodes"][meta["node_current"]]["memory_assigned_percent"] = proxlb_data["nodes"][meta["node_current"]]["memory_assigned"] / proxlb_data["nodes"][meta["node_current"]]["memory_total"] * 100
            proxlb_data["nodes"][meta["node_current"]]["disk_assigned_percent"] = proxlb_data["nodes"][meta["node_current"]]["disk_assigned"] / proxlb_data["nodes"][meta["node_current"]]["disk_total"] * 100

            # Update Tag assignments
            # Create affinity rules map
            for affinity_group in proxlb_data["guests"][guest]["affinity_groups"]:
                # Validate if this group has already been create on the current node
                # and create it initially if not already present.
                if not proxlb_data["nodes"][meta["node_current"]]["groups_affinity"].get(affinity_group, False):
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group] = {}
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group]["counter"] = 1
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group]["guests"] = []
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group]["guests"].append(meta["name"])
                    logger.debug(f"Initial Affinity created: {affinity_group} to node: {proxlb_data["nodes"][meta["node_current"]]["name"]} for guest: {meta["name"]}.")
                else:
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group]["counter"] += 1
                    proxlb_data["nodes"][meta["node_current"]]["groups_affinity"][affinity_group]["guests"].append(meta["name"])
                    logger.debug(f"Initial Affinity added: {affinity_group} to node: {proxlb_data["nodes"][meta["node_current"]]["name"]} for guest: {meta["name"]}.")

            # Create anti-affinity rules map
            for anti_affinity_group in proxlb_data["guests"][guest]["anti_affinity_groups"]:
                # Validate if this group has already been create on the current node
                # and create it initially if not already present.
                if not proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"].get(anti_affinity_group, False):
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group] = {}
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group]["counter"] = 1
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group]["guests"] = []
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group]["guests"].append(meta["name"])
                    logger.debug(f"Initial Anti-affinity created: {anti_affinity_group} to node: {proxlb_data["nodes"][meta["node_current"]]["name"]} for guest: {meta["name"]}.")
                else:
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group]["counter"] += 1
                    proxlb_data["nodes"][meta["node_current"]]["groups_anti_affinity"][anti_affinity_group]["guests"].append(meta["name"])
                    logger.debug(f"Initial Anti-affinity added: {anti_affinity_group} to node: {proxlb_data["nodes"][meta["node_current"]]["name"]} for guest: {meta["name"]}.")

        logger.debug("Finished: update_node_assignment.")
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
        #proxlb_data["meta"]["balancing"].update({"balance": False})
        proxlb_data["meta"]["balancing"]["balance"] = False

        # Check if balancing is enabled to avoid unnecessary calculations
        if not proxlb_data["meta"]["balancing"].get("enable", False):
            logger.info("Balancing is disabled in the configuration.")
            return proxlb_data

        if len(proxlb_data["guests"]) > 0:
            method = proxlb_data["meta"]["balancing"].get("method", "memory")
            mode = proxlb_data["meta"]["balancing"].get("mode", "used")
            balanciness = proxlb_data["meta"]["balancing"].get("balanciness", 10)
            method_value = [node_meta[f"{method}_{mode}_percent"] for node_meta in proxlb_data["nodes"].values()]
            method_value_highest = max(method_value)
            method_value_lowest = min(method_value)

            if method_value_highest - method_value_lowest > balanciness:
                proxlb_data["meta"]["balancing"]["balance"] = True
                logger.info(f"Guest balancing is required. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")
            else:
                logger.info(f"Guest balancing is ok. Highest value: {method_value_highest}, lowest value: {method_value_lowest} balanced by {method} and {mode}.")

            # Create debug output messages.
            nodes_usage_memory = " | ".join([f"{key}: {value['memory_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
            nodes_usage_cpu = "  | ".join([f"{key}: {value['cpu_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
            nodes_usage_disk = " | ".join([f"{key}: {value['disk_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
            logger.debug(f"Nodes usage memory: {nodes_usage_memory}")
            logger.debug(f"Nodes usage cpu:    {nodes_usage_cpu}")
            logger.debug(f"Nodes usage disk:   {nodes_usage_disk}")

        else:
            logger.warning("No guests for balancing found.")

        logger.debug("Finished: get_balanciness.")
        return proxlb_data

    @staticmethod
    def get_largest_guest(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the name of the Proxmox node in the cluster with the most free resources based on
        the user defined method (e.g.: memory) and mode (e.g.: used).

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
            Dict[str, Any]: Updated meta data section of the guest with the most used resources that
                  should be used for the next balancing action.
        """
        logger.debug("Starting: get_largest_guest.")
        proxlb_data["meta"]["balancing"].update({"balance_next_guest": ""})
        method = proxlb_data["meta"]["balancing"].get("method", "memory")

        # Do not include guests that are marked as 'ignore' or their current host node is marked as 'ignore'
        filtered_guests = [
            vm for vm in proxlb_data["guests"].values()
            if not vm["ignore"]
            and not vm["processed"]
            and not proxlb_data["nodes"][vm["node_current"]]["ignore"]
        ]

        # Handle empty list object
        if len(filtered_guests) > 0:
            highest_usage_guest = max(filtered_guests, key=lambda x: x[f"{method}_used"])
            proxlb_data["meta"]["balancing"]["balance_next_guest"] = highest_usage_guest["name"]
        else:
            proxlb_data["meta"]["balancing"]["balance"] = False

        logger.debug("Finished: get_largest_guest.")
        return proxlb_data

    @staticmethod
    def get_most_free_node(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the name of the Proxmox node in the cluster with the most free resources based on
        the user defined method (e.g.: memory) and mode (e.g.: used).

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
            Dict[str, Any]: Updated meta data section of the node with the most free resources that should
                  be used for the next balancing action.
        """
        logger.debug("Starting: get_most_free_node.")
        proxlb_data["meta"]["balancing"].update({"balance_next_node": ""})
        # Do not include nodes that are marked as 'ignore' or in 'maintenance'
        filtered_nodes = [node for node in proxlb_data["nodes"].values() if not node["ignore"] and not node["maintenance"]]
        lowest_usage_node = min(filtered_nodes, key=lambda x: x["memory_used_percent"])
        proxlb_data["meta"]["balancing"]["balance_reason"] = 'resources'
        proxlb_data["meta"]["balancing"]["balance_next_node"] = lowest_usage_node["name"]

        logger.debug("Finished: get_most_free_node.")
        return proxlb_data

    @staticmethod
    def val_affinty_rules(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the affinity and anti-affinity rules for the given guest in the provided data.

        This method checks the affinity and anti-affinity groups of a guest against the nodes in the 
        provided data. If an anti-affinity conflict is found, it sets the balance reason to 'anti-affinity-rules'
        and selects a node without the affinity as the next node for balancing. If an affinity match is found, it sets the 
        balance reason to 'affinity-rules' and selects the current node as the next node for balancing.

        Args:
            proxlb_data (Dict[str, Any]): The data containing information about guests, nodes, and balancing metadata.

        Returns:
            Dict[str, Any]: The updated data with the balance reason and next node for balancing set based on the 
                            affinity and anti-affinity rules.
        """
        logger.debug("Starting: val_affinty_rules.")
        guest = proxlb_data["meta"]["balancing"]["balance_next_guest"]

        if not guest:
            return None

        # Get the guest's affinity and anti-affinity groups
        guest_affinity_groups = proxlb_data["guests"][guest].get('affinity_groups', [])
        guest_anti_affinity_groups = proxlb_data["guests"][guest].get('anti_affinity_groups', [])

        for node_name, node in proxlb_data["nodes"].items():

            # Ensure node_name_random is not equal to node_name
            node_names = list(proxlb_data["nodes"].keys())
            node_name_random = random.choice(node_names)
            while node_name_random == node_name:
                node_name_random = random.choice(node_names)

            # Check anti-affinity groups
            for group in guest_anti_affinity_groups:
                if group in node.get('groups_anti_affinity', {}) and guest in node['groups_anti_affinity'][group]['guests']:
                    proxlb_data["meta"]["balancing"]["balance_reason"] = 'anti-affinity-rules'
                    proxlb_data["meta"]["balancing"]["balance"] = True
                    proxlb_data["meta"]["balancing"]["balance_next_node"] = node_name_random
                    logger.debug(f"Anti-affinity conflict for {guest} with rule: {group}.")
                    print(f"Anti-affinity conflict for {guest} with rule: {group}.")
                    break

            # Check affinity groups
            for group in guest_affinity_groups:
                if group in node.get('groups_affinity', {}):
                    proxlb_data["meta"]["balancing"]["balance_reason"] = 'affinity-rules'
                    proxlb_data["meta"]["balancing"]["balance"] = True
                    proxlb_data["meta"]["balancing"]["balance_next_node"] = node_name
                    logger.debug(f"Affinity match for {guest} with rule: {group}.")
                    print(f"Affinity match for {guest} with rule: {group}.")
                    break

        logger.debug("Finished: val_affinty_rules.")
        return proxlb_data

    @staticmethod
    def update_resources(proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the resource metrics and tags for affinity and anti-affinity groups on node level
        after moving a guest from one node to another node.

        Args:
            proxlb_data (Dict[str, Any]): The data holding all content of all objects.
        Returns:
            Dict[str, Any]: Updated meta data of the nodes resource usage after interacting with them.
        """
        logger.debug("Starting: update_resources.")
        # Only perform further actions if we are required to do so by balanciness or a desired
        # balance reason.
        #if proxlb_data['meta']["balancing"].get("balance", False) or proxlb_data["meta"].get("balance_reason", []) in ["anti-affinity-rules", "affinity-rules"]:

        guest = proxlb_data["meta"]["balancing"]["balance_next_guest"]
        node_target = proxlb_data["meta"]["balancing"]["balance_next_node"]
        node_current = proxlb_data["guests"][guest]["node_current"]
        proxlb_data["guests"][guest]["processed"] = True
        proxlb_data["guests"][guest]["node_target"] = node_target

        # ## Update Resources
        # ## Update resources for the target node by the moved guest resources
        # Add assigned resources to the target node
        proxlb_data["nodes"][node_target]["cpu_assigned"] += proxlb_data["guests"][guest]["cpu_total"]
        proxlb_data["nodes"][node_target]["memory_assigned"] += proxlb_data["guests"][guest]["memory_total"]
        proxlb_data["nodes"][node_target]["disk_assigned"] += proxlb_data["guests"][guest]["disk_total"]
        # Update the assigned percentages of assigned resources for the target node
        proxlb_data["nodes"][node_target]["cpu_assigned_percent"] = proxlb_data["nodes"][node_target]["cpu_assigned"] / proxlb_data["nodes"][node_target]["cpu_total"] * 100
        proxlb_data["nodes"][node_target]["memory_assigned_percent"] = proxlb_data["nodes"][node_target]["memory_assigned"] / proxlb_data["nodes"][node_target]["memory_total"] * 100
        proxlb_data["nodes"][node_target]["disk_assigned_percent"] = proxlb_data["nodes"][node_target]["disk_assigned"] / proxlb_data["nodes"][node_target]["disk_total"] * 100
        # Add used resources to the target node
        proxlb_data["nodes"][node_target]["cpu_used"] += proxlb_data["guests"][guest]["cpu_used"]
        proxlb_data["nodes"][node_target]["memory_used"] += proxlb_data["guests"][guest]["memory_used"]
        proxlb_data["nodes"][node_target]["disk_used"] += proxlb_data["guests"][guest]["disk_used"]
        # Update the used percentages of usage resources for the target node
        proxlb_data["nodes"][node_target]["cpu_used_percent"] = proxlb_data["nodes"][node_target]["cpu_used"] / proxlb_data["nodes"][node_target]["cpu_total"] * 100
        proxlb_data["nodes"][node_target]["memory_used_percent"] = proxlb_data["nodes"][node_target]["memory_used"] / proxlb_data["nodes"][node_target]["memory_total"] * 100
        proxlb_data["nodes"][node_target]["disk_used_percent"] = proxlb_data["nodes"][node_target]["disk_used"] / proxlb_data["nodes"][node_target]["disk_total"] * 100

        # # Update resources for the current node by the moved guest resources
        # Add assigned resources to the target node
        proxlb_data["nodes"][node_current]["cpu_assigned"] -= proxlb_data["guests"][guest]["cpu_total"]
        proxlb_data["nodes"][node_current]["memory_assigned"] -= proxlb_data["guests"][guest]["memory_total"]
        proxlb_data["nodes"][node_current]["disk_assigned"] -= proxlb_data["guests"][guest]["disk_total"]
        # Update the assigned percentages of assigned resources for the target node
        proxlb_data["nodes"][node_current]["cpu_assigned_percent"] = proxlb_data["nodes"][node_current]["cpu_assigned"] / proxlb_data["nodes"][node_current]["cpu_total"] * 100
        proxlb_data["nodes"][node_current]["memory_assigned_percent"] = proxlb_data["nodes"][node_current]["memory_assigned"] / proxlb_data["nodes"][node_current]["memory_total"] * 100
        proxlb_data["nodes"][node_current]["disk_assigned_percent"] = proxlb_data["nodes"][node_current]["disk_assigned"] / proxlb_data["nodes"][node_current]["disk_total"] * 100
        # Add used resources to the target node
        proxlb_data["nodes"][node_current]["cpu_used"] -= proxlb_data["guests"][guest]["cpu_used"]
        proxlb_data["nodes"][node_current]["memory_used"] -= proxlb_data["guests"][guest]["memory_used"]
        proxlb_data["nodes"][node_current]["disk_used"] -= proxlb_data["guests"][guest]["disk_used"]
        # Update the used percentages of usage resources for the target node
        proxlb_data["nodes"][node_current]["cpu_used_percent"] = proxlb_data["nodes"][node_current]["cpu_used"] / proxlb_data["nodes"][node_current]["cpu_total"] * 100
        proxlb_data["nodes"][node_current]["memory_used_percent"] = proxlb_data["nodes"][node_current]["memory_used"] / proxlb_data["nodes"][node_current]["memory_total"] * 100
        proxlb_data["nodes"][node_current]["disk_used_percent"] = proxlb_data["nodes"][node_current]["disk_used"] / proxlb_data["nodes"][node_current]["disk_total"] * 100

        # # Update tag assignments on the target node by the moved guest
        # Create affinity rules map
        for affinity_group in proxlb_data["guests"][guest]["affinity_groups"]:
            # Validate if this group has already been create on the current node
            # and create it initially if not already present.
            if not proxlb_data["nodes"][node_target]["groups_affinity"].get(affinity_group, False):
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group] = {}
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["counter"] = 1
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"] = []
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"].append(guest)
                logger.debug(f"Affinity created: {affinity_group} to node: {node_target} for guest: {guest}.")
            else:
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["counter"] += 1
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"].append(guest)
                logger.debug(f"Affinity added: {affinity_group} to node: {node_target} for guest: {guest}.")

        # Create anti-affinity rules map
        for affinity_group in proxlb_data["guests"][guest]["affinity_groups"]:
            # Validate if this group has already been create on the current node
            # and create it initially if not already present.
            if not proxlb_data["nodes"][node_target]["groups_affinity"].get(affinity_group, False):
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group] = {}
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["counter"] = 1
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"] = []
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"].append(guest)
                logger.debug(f"Anti-affinity created: {affinity_group} to node: {node_target} for guest: {guest}.")
            else:
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["counter"] += 1
                proxlb_data["nodes"][node_target]["groups_affinity"][affinity_group]["guests"].append(guest)
                logger.debug(f"Anti-affinity added: {affinity_group} to node: {node_target} for guest: {guest}.")

        # # Update tag assignments on the current node by the moved guest
        # Create affinity rules map
        for affinity_group in proxlb_data["guests"][guest]["affinity_groups"]:
            # Validate if this group has already been create on the current node
            # and create it initially if not already present.
            if not proxlb_data["nodes"][node_current]["groups_affinity"].get(affinity_group, False):
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group] = {}
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["counter"] = 0
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["guests"] = []
                logger.debug(f"Affinity removed: {affinity_group} to node: {node_current} for guest: {guest}.")
            else:
                #proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["counter"] += 1
                #proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["guests"].remove(guest)
                logger.debug(f"Affinity removed: {affinity_group} to node: {node_current} for guest: {guest}.")

        # Create anti-affinity rules map
        for affinity_group in proxlb_data["guests"][guest]["affinity_groups"]:
            # Validate if this group has already been create on the current node
            # and create it initially if not already present.
            if not proxlb_data["nodes"][node_current]["groups_affinity"].get(affinity_group, False):
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group] = {}
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["counter"] = 0
                proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["guests"] = []
                logger.debug(f"Anti-affinity removed: {affinity_group} to node: {node_current} for guest: {guest}.")
            else:
                #proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["counter"] -= 1
                #proxlb_data["nodes"][node_current]["groups_affinity"][affinity_group]["guests"].remove(guest)
                logger.debug(f"Anti-affinity removed: {affinity_group} to node: {node_current} for guest: {guest}.")

            logger.debug("Finished: update_resources.")
