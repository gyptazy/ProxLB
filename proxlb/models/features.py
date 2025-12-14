"""
ProxLB Features module for validating and adjusting feature flags
based on Proxmox VE node versions and cluster compatibility.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import List
from typing import Dict, Any
from utils.logger import SystemdLogger
from packaging import version

logger = SystemdLogger()


class Features:
    """
    ProxLB Features module for validating and adjusting feature flags
    based on Proxmox VE node versions and cluster compatibility.

    Responsibilities:
        - Validate and adjust feature flags based on Proxmox VE node versions.

    Methods:
        __init__():
            No-op initializer.

        validate_available_features(proxlb_data: dict) -> None:
            Static method that inspects proxlb_data["nodes"] versions and disables
            incompatible balancing features for Proxmox VE versions < 9.0.0.
            This function mutates proxlb_data in place.

    Notes:
        - Expects proxlb_data to be a dict with "nodes" and "meta" keys.
    """
    def __init__(self):
        """
        Initializes the Features class.
        """

    @staticmethod
    def validate_available_features(proxlb_data: any) -> None:
        """
        Validate and adjust feature flags in the provided proxlb_data according to Proxmox VE versions.

        This function inspects the cluster node versions in proxlb_data and disables features
        that are incompatible with Proxmox VE versions older than 9.0.0. Concretely, if any node
        reports a 'pve_version' lower than "9.0.0":
        - If meta.balancing.with_conntrack_state is truthy, it is set to False and a warning is logged.
        - If meta.balancing.mode equals "psi", meta.balancing.enable is set to False and a warning is logged.

            proxlb_data (dict): Cluster data structure that must contain:
                - "nodes": a mapping (e.g., dict) whose values are mappings containing a 'pve_version' string.
                - "meta": a mapping that may contain a "balancing" mapping with keys:
                    - "with_conntrack_state" (bool, optional)
                    - "mode" (str, optional)
                    - "enable" (bool, optional)

            None: The function mutates proxlb_data in place to disable incompatible features.

        Side effects:
            - Mutates proxlb_data["meta"]["balancing"] when incompatible features are detected.
            - Emits debug and warning log messages.

        Notes:
            - Unexpected or missing keys/types in proxlb_data may raise KeyError or TypeError.
            - Version comparison uses semantic version parsing; callers should provide versions as strings.

        Returns:
            None
        """
        logger.debug("Starting: validate_available_features.")

        any_non_pve9_node = any(version.parse(n['pve_version']) < version.parse("9.0.0") for n in proxlb_data["nodes"].values())
        if any_non_pve9_node:

            with_conntrack_state = proxlb_data["meta"].get("balancing", {}).get("with_conntrack_state", False)
            if with_conntrack_state:
                logger.warning("Non Proxmox VE 9 systems detected: Deactivating migration option 'with-conntrack-state'!")
                proxlb_data["meta"]["balancing"]["with_conntrack_state"] = False

            psi_balancing = proxlb_data["meta"].get("balancing", {}).get("mode", None)
            if psi_balancing == "psi":
                logger.warning("Non Proxmox VE 9 systems detected: Deactivating balancing!")
                proxlb_data["meta"]["balancing"]["enable"] = False

        logger.debug("Finished: validate_available_features.")

    @staticmethod
    def validate_any_non_pve9_node(meta: any, nodes: any) -> dict:
        """
        Validate if any node in the cluster is running Proxmox VE < 9.0.0 and update meta accordingly.

        This function inspects the cluster node versions and sets a flag in meta indicating whether
        any node is running a Proxmox VE version older than 9.0.0.

        Args:
            meta (dict):    Metadata structure that will be updated with cluster version information.
            nodes (dict):   Cluster nodes mapping whose values contain 'pve_version' strings.

        Returns:
            dict:           The updated meta dictionary with 'cluster_non_pve9' flag set to True or False.

        Side effects:
            - Mutates meta["meta"]["cluster_non_pve9"] based on node versions.
            - Emits debug log messages.

        Notes:
            - Version comparison uses semantic version parsing; defaults to "0.0.0" if pve_version is missing.
        """
        logger.debug("Starting: validate_any_non_pve9_node.")
        any_non_pve9_node = any(version.parse(node.get("pve_version", "0.0.0")) < version.parse("9.0.0") for node in nodes.get("nodes", {}).values())

        if any_non_pve9_node:
            meta["meta"]["cluster_non_pve9"] = True
            logger.debug("Finished: validate_any_non_pve9_node. Result: True")
        else:
            meta["meta"]["cluster_non_pve9"] = False
            logger.debug("Finished: validate_any_non_pve9_node. Result: False")

        return meta
