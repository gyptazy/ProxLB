"""
The Groups class is responsible for handling the correlations between the guests
and their groups, such as affinity and anti-affinity groups. It ensures proper balancing
by grouping guests and evaluating them for further balancing. The class provides methods
to initialize with ProxLB data and to generate groups based on guest and node data.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import Dict, Any
from utils.logger import SystemdLogger
from utils.helper import Helper

logger = SystemdLogger()


class Groups:
    """
    The groups class is responsible for handling the correlations between the guests
    and their groups like affinity and anti-affinity groups. To ensure a proper balancing
    guests will ge grouped and then evaluated for further balancing.

    Methods:
        __init__(proxlb_data: Dict[str, Any]):
            Initializes the Groups class.

        get_groups(guests: Dict[str, Any], nodes: Dict[str, Any]) -> Dict[str, Any]:
            Generates and returns a dictionary of affinity and anti-affinity groups
            based on the provided data.
    """

    def __init__(self, proxlb_data: Dict[str, Any]):
        """
        Initializes the Groups class with the provided ProxLB data.

        Args:
            proxlb_data (Dict[str, Any]): The data required for balancing VMs and CTs.
        """

    @staticmethod
    def get_groups(guests: Dict[str, Any], nodes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates and returns a dictionary of affinity and anti-affinity groups based on the provided data.

        Args:
            guests (Dict[str, Any]): A dictionary containing the guest data.
            nodes  (Dict[str, Any]): A dictionary containing the nodes data.

        Returns:
            Dict[str, Any]: A dictionary containing the created groups that includes:
                            * Affinity groups (or a randon and uniq group)
                            * Anti-affinity groups
                            * A list of guests that are currently placed on a node which
                              is defined to be in maintenance.
        """
        logger.debug("Starting: get_groups.")
        groups = {'groups': {'affinity': {}, 'anti_affinity': {}, 'maintenance': []}}

        for guest_name, guest_meta in guests["guests"].items():
            # Create affinity grouping
            # Use an affinity group if available for the guest
            if len(guest_meta["affinity_groups"]) > 0:
                for affinity_group in guest_meta["affinity_groups"]:
                    group_name = affinity_group
                    logger.debug(f'Affinity group {affinity_group} for {guest_name} will be used.')
            else:
                # Generate a random uniq group name for the guest if
                # the guest does not belong to any affinity group
                random_group = Helper.get_uuid_string()
                group_name = random_group
                logger.debug(f'Random uniq group {random_group} for {guest_name} will be used.')

            if not groups["groups"]["affinity"].get(group_name, False):
                # Create group template with initial guest meta information
                groups["groups"]["affinity"][group_name] = {}
                groups["groups"]["affinity"][group_name]["guests"] = []
                groups["groups"]["affinity"][group_name]["guests"].append(guest_name)
                groups["groups"]["affinity"][group_name]["counter"] = 1
                # Create groups resource template by the guests resources
                groups["groups"]["affinity"][group_name]["cpu_total"] = guest_meta["cpu_total"]
                groups["groups"]["affinity"][group_name]["cpu_used"] = guest_meta["cpu_used"]
                groups["groups"]["affinity"][group_name]["memory_total"] = guest_meta["memory_total"]
                groups["groups"]["affinity"][group_name]["memory_used"] = guest_meta["cpu_used"]
                groups["groups"]["affinity"][group_name]["disk_total"] = guest_meta["disk_total"]
                groups["groups"]["affinity"][group_name]["disk_used"] = guest_meta["cpu_used"]
            else:
                # Update group templates by guest meta information
                groups["groups"]["affinity"][group_name]["guests"].append(guest_name)
                groups["groups"]["affinity"][group_name]["counter"] += 1
                # Update group resources by guest resources
                groups["groups"]["affinity"][group_name]["cpu_total"] += guest_meta["cpu_total"]
                groups["groups"]["affinity"][group_name]["cpu_used"] += guest_meta["cpu_used"]
                groups["groups"]["affinity"][group_name]["memory_total"] += guest_meta["memory_total"]
                groups["groups"]["affinity"][group_name]["memory_used"] += guest_meta["cpu_used"]
                groups["groups"]["affinity"][group_name]["disk_total"] += guest_meta["disk_total"]
                groups["groups"]["affinity"][group_name]["disk_used"] += guest_meta["cpu_used"]

            # Create anti-affinity grouping
            if len(guest_meta["anti_affinity_groups"]) > 0:
                for anti_affinity_group in guest_meta["anti_affinity_groups"]:
                    anti_affinity_group_name = anti_affinity_group
                    logger.debug(f'Anti-affinity group {anti_affinity_group_name} for {guest_name} will be used.')

                    if not groups["groups"]["anti_affinity"].get(anti_affinity_group_name, False):
                        groups["groups"]["anti_affinity"][anti_affinity_group_name] = {}
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["guests"] = []
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["guests"].append(guest_name)
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["counter"] = 1
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["used_nodes"] = []
                    else:
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["guests"].append(guest_name)
                        groups["groups"]["anti_affinity"][anti_affinity_group_name]["counter"] += 1

            # Create grouping of guests that are currently located on nodes that are
            # marked as in maintenance and must be migrated
            if nodes["nodes"][guest_meta["node_current"]]["maintenance"]:
                logger.debug(f'{guest_name} will be migrated to another node because the underlying node {guest_meta["node_current"]} is defined to be in maintenance.')
                groups["groups"]["maintenance"].append(guest_name)

        logger.debug("Finished: get_groups.")
        return groups
