"""
The HaRules class retrieves all HA rules defined on a Proxmox cluster
including their affinity settings and member resources.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import Dict, Any
from utils.logger import SystemdLogger

logger = SystemdLogger()


class HaRules:
    """
    The HaRules class retrieves all HA rules defined on a Proxmox cluster
    including their (anti)a-ffinity settings and member resources and translates
    them into a ProxLB usable format.

    Methods:
        __init__:
            Initializes the HaRules class.

        get_ha_rules(proxmox_api: any) -> Dict[str, Any]:
            Retrieve HA rule definitions from the Proxmox cluster.
            Returns a dict with a top-level "ha_rules" mapping each rule id to
            {"rule": <rule_id>, "type": <affinity_type>, "members": [<resource_ids>...]}.
            Converts affinity settings to descriptive format (affinity or anti-affinity).
    """
    def __init__(self):
        """
        Initializes the HA Rules class with the provided ProxLB data.
        """

    @staticmethod
    def get_ha_rules(proxmox_api: any, meta: dict) -> Dict[str, Any]:
        """
        Retrieve all HA rules from a Proxmox cluster.

        Queries the Proxmox API for HA rule definitions and returns a dictionary
        containing each rule's id, affinity type, and member resources (VM/CT IDs).
        This function processes rule affinity settings and converts them to a more
        descriptive format (affinity or anti-affinity).

        Args:
            proxmox_api (any):      Proxmox API client instance.
            meta (dict):            The metadata dictionary containing cluster information.

        Returns:
            Dict[str, Any]:         Dictionary with a top-level "ha_rules" key mapping rule id
                                    to {"rule": <rule_id>, "type": <affinity_type>, "members": [<resource_ids>...]}.
        """
        logger.debug("Starting: get_ha_rules.")
        ha_rules = {"ha_rules": {}}

        # If any node is non PVE 9, skip fetching HA rules as they are unsupported
        if meta["meta"]["cluster_non_pve9"]:
            logger.debug("Skipping HA rule retrieval as non Proxmox VE 9 systems detected.")
            return ha_rules
        else:
            logger.debug("Cluster running Proxmox VE 9 or newer, proceeding with HA rule retrieval.")

        for rule in proxmox_api.cluster.ha.rules.get():

            # Skip disabled rules (disable key exists AND is truthy)
            if rule.get("disable", 0):
                logger.debug(f"Skipping ha-rule: {rule['rule']} of type {rule['type']} affecting guests: {rule['resources']}. Rule is disabled.")
                continue

            # Create a resource list by splitting on commas and stripping whitespace containing
            # the VM and CT IDs that are part of this HA rule
            resources_list_guests = [int(r.split(":")[1]) for r in rule["resources"].split(",") if r.strip()]

            # Convert the affinity field to a more descriptive type
            if rule.get("affinity", None) == "negative":
                affinity_type = "anti-affinity"
            else:
                affinity_type = "affinity"

            # Create affected nodes list
            resources_list_nodes = []
            if rule.get("nodes", None):
                resources_list_nodes = [n for n in rule["nodes"].split(",") if n]

            # Create the ha_rule element
            ha_rules['ha_rules'][rule['rule']] = {}
            ha_rules['ha_rules'][rule['rule']]['rule'] = rule['rule']
            ha_rules['ha_rules'][rule['rule']]['type'] = affinity_type
            ha_rules['ha_rules'][rule['rule']]['nodes'] = resources_list_nodes
            ha_rules['ha_rules'][rule['rule']]['members'] = resources_list_guests

            logger.debug(f"Got ha-rule: {rule['rule']} as type {affinity_type} affecting guests: {rule['resources']}")

        logger.debug("Finished: ha_rules.")
        return ha_rules

    @staticmethod
    def get_ha_rules_for_guest(guest_name: str, ha_rules: Dict[str, Any], vm_id: int) -> Dict[str, Any]:
        """
        Return the list of HA rules that include the given guest.

        Args:
            guest_name (str):               Name of the VM or CT to look up.
            ha_rules (Dict[str, Any]):      HA rules structure as returned by get_ha_rules(),
                                            expected to contain a top-level "ha_rules" mapping each rule id to
                                            {"rule": <rule_id>, "type": <affinity_type>, "members": [<resource_ids>...]}.
            vm_id (int):                    VM or CT ID of the guest.

        Returns:
            list:                           IDs of HA rules the guest is a member of (empty list if none).
        """
        logger.debug("Starting: get_ha_rules_for_guest.")
        guest_ha_rules = []

        for rule in ha_rules["ha_rules"].values():
            if vm_id in rule.get("members", []):
                logger.debug(f"Guest: {guest_name} (VMID: {vm_id}) is member of HA Rule: {rule['rule']}.")
                guest_ha_rules.append(rule)
            else:
                logger.debug(f"Guest: {guest_name} (VMID: {vm_id}) is NOT member of HA Rule: {rule['rule']}.")

        logger.debug("Finished: get_ha_rules_for_guest.")
        return guest_ha_rules
