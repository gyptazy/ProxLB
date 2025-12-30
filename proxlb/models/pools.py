"""
The Pools class retrieves all present pools defined on a Proxmox cluster
including the chield objects.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import Dict, Any
from utils.logger import SystemdLogger
from models.tags import Tags
import time

logger = SystemdLogger()


class Pools:
    """
    The Pools class retrieves all present pools defined on a Proxmox cluster
    including the chield objects.

    Methods:
        __init__:
            Initializes the Pools class.

        get_pools(proxmox_api: any) -> Dict[str, Any]:
            Retrieve pool definitions and membership from the Proxmox cluster.
            Returns a dict with a top-level "pools" mapping each poolid to
            {"name": <poolid>, "members": [<member_names>...]}.
            This method does not collect per-member metrics or perform node filtering.
    """
    def __init__(self):
        """
        Initializes the Pools class with the provided ProxLB data.
        """

    @staticmethod
    def get_pools(proxmox_api: any) -> Dict[str, Any]:
        """
        Retrieve all pools and their members from a Proxmox cluster.

        Queries the Proxmox API for pool definitions and returns a dictionary
        containing each pool's id/name and a list of its member VM/CT names.
        This function does not perform per-member metric collection or node
        filtering — it only gathers pool membership information.

        Args:
            proxmox_api (any): Proxmox API client instance.

        Returns:
            Dict[str, Any]: Dictionary with a top-level "pools" key mapping poolid
                    to {"name": <poolid>, "members": [<member_names>...]}.
        """
        logger.debug("Starting: get_pools.")
        pools = {"pools": {}}

        # Pool objects: iterate over all pools in the cluster.
        # We keep pool members even if their nodes are ignored so resource accounting
        # for rebalancing remains correct and we avoid overprovisioning nodes.
        for pool in proxmox_api.pools.get():
            logger.debug(f"Got pool: {pool['poolid']}")
            pools['pools'][pool['poolid']] = {}
            pools['pools'][pool['poolid']]['name'] = pool['poolid']
            pools['pools'][pool['poolid']]['members'] = []

            # Fetch pool details and collect member names
            pool_details = proxmox_api.pools(pool['poolid']).get()
            for member in pool_details.get("members", []):

                # We might also have objects without the key "name", e.g. storage pools
                if "name" not in member:
                    logger.debug(f"Skipping member without name in pool: {pool['poolid']}")
                    continue

                logger.debug(f"Got member: {member['name']} for pool: {pool['poolid']}")
                pools['pools'][pool['poolid']]['members'].append(member["name"])

        logger.debug("Finished: get_pools.")
        return pools

    @staticmethod
    def get_pools_for_guest(guest_name: str, pools: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return the list of pool names that include the given guest.

        Args:
            guest_name (str): Name of the VM or CT to look up.
            pools (Dict[str, Any]): Pools structure as returned by get_pools(),
            expected to contain a top-level "pools" mapping each poolid to
            {"name": <poolid>, "members": [<member_names>...]}.

        Returns:
            list[str]: Names of pools the guest is a member of (empty list if none).
        """
        logger.debug("Starting: get_pools_for_guests.")
        guest_pools = []

        for pool in pools.items():
            for pool_id, pool_data in pool[1].items():

                if type(pool_data) is dict:
                    pool_name = pool_data.get("name", "")
                    pool_name_members = pool_data.get("members", [])

                    if guest_name in pool_name_members:
                        logger.debug(f"Guest: {guest_name} is member of Pool: {pool_name}.")
                        guest_pools.append(pool_name)
                    else:
                        logger.debug(f"Guest: {guest_name} is NOT member of Pool: {pool_name}.")

                else:
                    logger.debug(f"Pool data for pool_id {pool_id} is not a dict: {pool_data}")

        logger.debug("Finished: get_pools_for_guests.")
        return guest_pools

    @staticmethod
    def get_pool_node_affinity_strictness(proxlb_config: Dict[str, Any], guest_pools: list) -> bool:
        """
        Retrieve the node affinity strictness setting for a guest across its pools.

        Queries the ProxLB configuration to determine the node affinity strictness
        level for the specified guest based on its pool memberships. Returns the
        strictness setting from the first matching pool configuration.

        Args:
            proxlb_config (Dict[str, Any]):     ProxLB configuration dictionary.
            guest_pools (list):                 List of pool names the guest belongs to.

        Returns:
            bool:                               Node affinity strictness setting (default True if not specified).
        """
        logger.debug("Starting: get_pool_node_affinity_strictness.")

        node_strictness = True
        for pool in guest_pools:
            pool_settings = proxlb_config.get("balancing", {}).get("pools", {}).get(pool, {})
            node_strictness = pool_settings.get("strict", True)

        logger.debug("Finished: get_pool_node_affinity_strictness.")
        return node_strictness
