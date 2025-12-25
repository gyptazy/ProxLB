"""
The Tags class retrieves and processes tags from guests of type VM or CT running
in a Proxmox cluster. It provides methods to fetch tags from the Proxmox API and
evaluate them for affinity, anti-affinity, and ignore tags, which are used during
balancing calculations.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import time
from typing import List
from typing import Dict, Any
from utils.logger import SystemdLogger
from utils.helper import Helper

logger = SystemdLogger()


class Tags:
    """
    The Tags class retrieves and processes tags from guests of type VM or CT running
    in a Proxmox cluster. It provides methods to fetch tags from the Proxmox API and
    evaluate them for affinity, anti-affinity, and ignore tags, which are used during
    balancing calculations.

    Methods:
        __init__:
            Initializes the Tags class.

        get_tags_from_guests(proxmox_api: any, node: str, guest_id: int, guest_type: str) -> List[str]:
            Retrieves all tags for a given guest from the Proxmox API.

        get_affinity_groups(tags: List[str]) -> List[str]:
            Evaluates and returns all affinity tags from the provided list of tags.

        get_anti_affinity_groups(tags: List[str]) -> List[str]:
            Evaluates and returns all anti-affinity tags from the provided list of tags.

        get_ignore(tags: List[str]) -> bool:
            Evaluates and returns a boolean indicating whether the guest should be ignored based on the provided list of tags.
    """
    def __init__(self):
        """
        Initializes the tags class.
        """

    @staticmethod
    def get_tags_from_guests(proxmox_api: any, node: str, guest_id: int, guest_type: str) -> List[str]:
        """
        Get tags for a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest from the Proxmox API which
        is held in the guest_config.

        Args:
            proxmox_api (any): The Proxmox API client instance.
            node (str): The node name where the given guest is located.
            guest_id (int): The internal Proxmox ID of the guest.
            guest_type (str): The type (vm or ct) of the guest.

        Returns:
            List: A list of all tags assoiciated with the given guest.
        """
        logger.debug("Starting: get_tags_from_guests.")
        time.sleep(0.1)
        if guest_type == 'vm':
            guest_config = proxmox_api.nodes(node).qemu(guest_id).config.get()
            tags = guest_config.get("tags", [])
        if guest_type == 'ct':
            guest_config = proxmox_api.nodes(node).lxc(guest_id).config.get()
            tags = guest_config.get("tags", [])

        if isinstance(tags, str):
            tags = tags.split(";")

        logger.debug("Finished: get_tags_from_guests.")
        return tags

    @staticmethod
    def get_affinity_groups(tags: List[str], pools: List[str], ha_rules: List[str], proxlb_config: Dict[str, Any]) -> List[str]:
        """
        Get affinity tags for a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest or based on a
        membership of a pool and evaluates the affinity groups which are
        required during the balancing calculations.

        Args:
            tags (List): A list holding all defined tags for a given guest.
            pools (List): A list holding all defined pools for a given guest.
            ha_rules (List): A list holding all defined ha_rules for a given guest.
            proxlb_config (Dict): A dict holding the ProxLB configuration.

        Returns:
            List: A list including all affinity tags for the given guest.
        """
        logger.debug("Starting: get_affinity_groups.")
        affinity_tags = []

        # Tag based affinity groups
        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_affinity"):
                    logger.debug(f"Adding affinity group for tag {tag}.")
                    affinity_tags.append(tag)
                else:
                    logger.debug(f"Skipping evaluation of tag: {tag} This is not an affinity tag.")

        # Pool based affinity groups
        if len(pools) > 0:
            for pool in pools:
                if pool in (proxlb_config['balancing'].get('pools') or {}):
                    if proxlb_config['balancing']['pools'][pool].get('type', None) == 'affinity':
                        logger.debug(f"Adding affinity group for pool {pool}.")
                        affinity_tags.append(pool)
                else:
                    logger.debug(f"Skipping evaluation of pool: {pool} This is not an affinity pool.")

        # HA rule based affinity groups
        if len(ha_rules) > 0:
            for ha_rule in ha_rules:
                if ha_rule.get('type', None) == 'affinity':
                    logger.debug(f"Adding affinity group for ha-rule {ha_rule}.")
                    affinity_tags.append(ha_rule['rule'])

        logger.debug("Finished: get_affinity_groups.")
        return affinity_tags

    @staticmethod
    def get_anti_affinity_groups(tags: List[str], pools: List[str], ha_rules: List[str], proxlb_config: Dict[str, Any]) -> List[str]:
        """
        Get anti-affinity tags for a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest or based on a
        membership of a pool and evaluates the anti-affinity groups which
        are required during the balancing calculations.

        Args:
            tags (List): A list holding all defined tags for a given guest.
            pools (List): A list holding all defined pools for a given guest.
            ha_rules (List): A list holding all defined ha_rules for a given guest.
            proxlb_config (Dict): A dict holding the ProxLB configuration.

        Returns:
            List: A list including all anti-affinity tags for the given guest..
        """
        logger.debug("Starting: get_anti_affinity_groups.")
        anti_affinity_tags = []

        # Tag based anti-affinity groups
        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_anti_affinity"):
                    logger.debug(f"Adding anti-affinity group for tag {tag}.")
                    anti_affinity_tags.append(tag)
                else:
                    logger.debug(f"Skipping evaluation of tag: {tag} This is not an anti-affinity tag.")

        # Pool based anti-affinity groups
        if len(pools) > 0:
            for pool in pools:
                if pool in (proxlb_config['balancing'].get('pools') or {}):
                    if proxlb_config['balancing']['pools'][pool].get('type', None) == 'anti-affinity':
                        logger.debug(f"Adding anti-affinity group for pool {pool}.")
                        anti_affinity_tags.append(pool)
                else:
                    logger.debug(f"Skipping evaluation of pool: {pool} This is not an anti-affinity pool.")

        # HA rule based anti-affinity groups
        if len(ha_rules) > 0:
            for ha_rule in ha_rules:
                if ha_rule.get('type', None) == 'anti-affinity':
                    logger.debug(f"Adding anti-affinity group for ha-rule {ha_rule}.")
                    anti_affinity_tags.append(ha_rule['rule'])

        logger.debug("Finished: get_anti_affinity_groups.")
        return anti_affinity_tags

    @staticmethod
    def get_ignore(tags: List[str]) -> bool:
        """
        Validate for ignore tags of a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest and evaluates the
        ignore tag which are required during the balancing calculations.

        Args:
            tags (List): A list holding all defined tags for a given guest.

        Returns:
            Bool: Returns a bool that indicates whether to ignore a guest or not.
        """
        logger.debug("Starting: get_ignore.")
        ignore_tag = False

        if len(tags) > 0:
            logger.debug(f"Found {len(tags)} tags to evaluate.")
            for tag in tags:
                logger.debug(f"Evaluating tag: {tag}.")
                if tag.startswith("plb_ignore"):
                    logger.debug(f"Found valid ignore tag: {tag}. Marking guest as ignored.")
                    ignore_tag = True
                else:
                    logger.debug(f"Tag: {tag} This is not an ignore tag.")

        logger.debug("Finished: get_ignore.")
        return ignore_tag

    @staticmethod
    def get_node_relationships(tags: List[str], nodes: Dict[str, Any], pools: List[str], ha_rules: List[str], proxlb_config: Dict[str, Any]) -> str:
        """
        Get a node relationship tag for a guest from the Proxmox cluster by the API to pin
        a guest to a node or by defined pools from ProxLB configuration.

        This method retrieves a relationship tag between a guest and a specific
        hypervisor node to pin the guest to a specific node (e.g., for licensing reason).

        Args:
            tags (List): A list holding all defined tags for a given guest.
            nodes (Dict): A dictionary holding all available nodes in the cluster.
            pools (List): A list holding all defined pools for a given guest.
            ha_rules (List): A list holding all defined ha_rules for a given guest.
            proxlb_config (Dict): A dict holding the ProxLB configuration.

        Returns:
            Str: The related hypervisor node name(s).
        """
        logger.debug("Starting: get_node_relationships.")
        node_relationship_tags = []

        # Tag based node relationship
        if len(tags) > 0:
            logger.debug("Validating node pinning by tags.")
            for tag in tags:
                if tag.startswith("plb_pin"):
                    node_relationship_tag = tag.replace("plb_pin_", "")

                    # Validate if the node to pin is present in the cluster
                    if Helper.validate_node_presence(node_relationship_tag, nodes):
                        logger.debug(f"Tag {node_relationship_tag} is valid! Defined node exists in the cluster.")
                        logger.debug(f"Setting node relationship because of tag {tag} to {node_relationship_tag}.")
                        node_relationship_tags.append(node_relationship_tag)
                    else:
                        logger.warning(f"Tag {node_relationship_tag} is invalid! Defined node does not exist in the cluster. Not applying pinning.")

        # Pool based node relationship
        if len(pools) > 0:
            logger.debug("Validating node pinning by pools.")
            for pool in pools:
                if pool in (proxlb_config['balancing'].get('pools') or {}):

                    pool_nodes = proxlb_config['balancing']['pools'][pool].get('pin', None)
                    for node in pool_nodes if pool_nodes is not None else []:

                        # Validate if the node to pin is present in the cluster
                        if Helper.validate_node_presence(node, nodes):
                            logger.debug(f"Pool pinning tag {node} is valid! Defined node exists in the cluster.")
                            logger.debug(f"Setting node relationship because of pool {pool} to {node}.")
                            node_relationship_tags.append(node)
                        else:
                            logger.warning(f"Pool pinning tag {node} is invalid! Defined node does not exist in the cluster. Not applying pinning.")

                else:
                    logger.debug(f"Skipping pinning for pool {pool}. Pool is not defined in ProxLB configuration.")

        # HA rule based node relationship
        if len(ha_rules) > 0:
            logger.debug("Validating node pinning by ha-rules.")
            for ha_rule in ha_rules:
                if len(ha_rule.get("nodes", 0)) > 0:
                    if ha_rule.get("type", None) == "affinity":
                        logger.debug(f"ha-rule {ha_rule['rule']} is of type affinity.")
                        for node in ha_rule["nodes"]:
                            logger.debug(f"Adding {node} as node relationship because of ha-rule {ha_rule['rule']}.")
                            node_relationship_tags.append(node)
                    else:
                        logger.debug(f"ha-rule {ha_rule['rule']} is of type anti-affinity. Skipping node relationship addition.")

        logger.debug("Finished: get_node_relationships.")
        return node_relationship_tags
