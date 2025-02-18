"""
The Tags class retrieves all tags from guests of the type VM or CT running
in a Proxmox cluster and validates for affinity, anti-affinity and ignore
tags set for the guest in the Proxmox API.
"""

import time
from typing import List
from utils.logger import SystemdLogger

logger = SystemdLogger()


class Tags:
    """
    The Tags class retrieves all tags from guests of the type VM or CT running
    in a Proxmox cluster and validates for affinity, anti-affinity and ignore
    tags set for the guest in the Proxmox API.
    """
    def __init__(self):
        """
        Initializes the Tags class.
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
            Bool: Returns a bool that indicates wether to ignore a guest or not.
        """
        logger.debug("Starting: get_ignore.")
        ignore_tag = False

        if len(tags) > 0:
            for tag in tags:
                if tag.startswith("plb_ignore"):
                    ignore_tag = True

        logger.debug("Finished: get_ignore.")
        return ignore_tag
