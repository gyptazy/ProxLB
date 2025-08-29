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
    def get_affinity_groups(tags: List[str]) -> List[str]:
        """
        Get affinity tags for a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest and evaluates the
        affinity tags which are required during the balancing calculations.

        Args:
            tags (List): A list holding all defined tags for a given guest.

        Returns:
            List: A list including all affinity tags for the given guest.
        """
        logger.debug("Starting: get_affinity_groups.")
        affinity_tags = []

        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_affinity"):
                    affinity_tags.append(tag)

        logger.debug("Finished: get_affinity_groups.")
        return affinity_tags

    @staticmethod
    def get_anti_affinity_groups(tags: List[str]) -> List[str]:
        """
        Get anti-affinity tags for a guest from the Proxmox cluster by the API.

        This method retrieves all tags for a given guest and evaluates the
        anti-affinity tags which are required during the balancing calculations.

        Args:
            tags (List): A list holding all defined tags for a given guest.

        Returns:
            List: A list including all anti-affinity tags for the given guest..
        """
        logger.debug("Starting: get_anti_affinity_groups.")
        anti_affinity_tags = []

        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_anti_affinity"):
                    anti_affinity_tags.append(tag)

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
            for tag in tags:
                if tag.startswith("plb_ignore"):
                    ignore_tag = True

        logger.debug("Finished: get_ignore.")
        return ignore_tag

    @staticmethod
    def get_node_relationships(tags: List[str], nodes: Dict[str, Any]) -> str:
        """
        Get a node relationship tag for a guest from the Proxmox cluster by the API to pin
        a guest to a node.

        This method retrieves a relationship tag between a guest and a specific
        hypervisor node to pin the guest to a specific node (e.g., for licensing reason).

        Args:
            tags (List): A list holding all defined tags for a given guest.
            nodes (Dict): A dictionary holding all available nodes in the cluster.

        Returns:
            Str: The related hypervisor node name.
        """
        logger.debug("Starting: get_node_relationships.")
        node_relationship_tags = []

        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_pin"):
                    node_relationship_tag = tag.replace("plb_pin_", "")

                    # Validate if the node to pin is present in the cluster
                    if Helper.validate_node_presence(node_relationship_tag, nodes):
                        logger.info(f"Tag {node_relationship_tag} is valid! Defined node exists in the cluster.")
                        node_relationship_tags.append(node_relationship_tag)
                    else:
                        logger.warning(f"Tag {node_relationship_tag} is invalid! Defined node does not exist in the cluster. Not applying pinning.")

        logger.debug("Finished: get_node_relationships.")
        return node_relationship_tags
