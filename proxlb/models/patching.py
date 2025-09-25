"""
The Patching class is responsible for orchestrating the patching process of nodes in a Proxmox cluster,
based on the provided ProxLB data and using the Proxmox API. It determines which nodes require
patching, selects nodes for patching according to configuration, and executes patching actions
while ensuring no running guests are present.
"""


__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from utils.logger import SystemdLogger
from typing import Dict, Any

logger = SystemdLogger()


class Patching:
    """
    Patching

    This class is responsible for orchestrating the patching process of nodes in a Proxmox cluster,
    based on the provided ProxLB data and using the Proxmox API. It determines which nodes require
    patching, selects nodes for patching according to configuration, and executes patching actions
    while ensuring no running guests are present.

    Functions:
    -----------
    __init__(self, proxmox_api: any, proxlb_data: Dict[str, Any], calculations_done: bool = False)
        - Initializes the Patching class and triggers either patch preparation or execution based on the calculations_done flag.
        - Inputs:
            - proxmox_api: Proxmox API client instance.
            - proxlb_data: Dictionary containing cluster and node information.
            - calculations_done: Boolean flag to determine operation mode.
        - Outputs: None

    val_nodes_packages(self, proxmox_api: any, proxlb_data: Dict[str, Any]) -> Dict[str, Any]
        - Checks each node for available package updates and updates their patching status.
        - Inputs:
            - proxmox_api: Proxmox API client instance.
            - proxlb_data: Dictionary with node and maintenance information.
        - Outputs:
            - Updated proxlb_data dictionary with patching status for each node.

    get_nodes_to_patch(self, proxlb_data: Dict[str, Any]) -> Dict[str, Any]
        - Selects nodes to patch in the current run based on configuration and node status.
        - Inputs:
            - proxlb_data: Dictionary with ProxLB configuration and node information.
        - Outputs:
            - Updated proxlb_data with selected nodes for patching in this run.

    patch_node(self, proxmox_api: any, proxlb_data: Dict[str, Any])
        - Executes the patching process for selected nodes, ensuring no running guests are present before proceeding.
        - Inputs:
            - proxmox_api: Proxmox API client instance.
            - proxlb_data: Dictionary with metadata and list of nodes to patch.
        - Outputs: None
    """
    def __init__(self, proxmox_api: any, proxlb_data: Dict[str, Any], calculations_done: bool = False):
        """
        Initializes the Patching class with the provided ProxLB data.
        """
        if not calculations_done:
            logger.debug("Starting: Patching preparations.")
            self.val_nodes_packages(proxmox_api, proxlb_data)
            self.get_nodes_to_patch(proxlb_data)
            logger.debug("Finished: Patching preparations.")
        else:
            logger.debug("Starting: Patching executions.")
            self.patch_node(proxmox_api, proxlb_data)
            logger.debug("Finished: Patching executions.")

    def val_nodes_packages(self, proxmox_api: any, proxlb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks each node in the provided ProxLB data for available package updates using the Proxmox API,
        and updates the node's patching status accordingly.

        Args:
            proxmox_api (Any): An instance of the Proxmox API client used to query node package updates.
            proxlb_data (Dict[str, Any]): A dictionary containing node information, including maintenance status.

        Returns:
            Dict[str, Any]: The updated proxlb_data dictionary with patching status set for each node.
        """
        logger.debug("Starting: val_nodes_packages.")

        for node in proxlb_data['nodes'].keys():
            if proxlb_data['nodes'][node]['maintenance'] is False:
                node_pkgs = proxmox_api.nodes(node).apt.update.get()

                if len(node_pkgs) > 0:
                    proxlb_data['nodes'][node]['patching'] = True
                    logger.debug(f"Node {node} has {len(node_pkgs)} packages to update.")
                else:
                    logger.debug(f"Node {node} is up to date and has no packages to update.")

        logger.debug("Finished: val_nodes_packages.")
        return proxlb_data

    def get_nodes_to_patch(self, proxlb_data: Dict[str, Any]):
        """
        Determines which nodes should be patched in the current run based on the ProxLB configuration and node status.

        Args:
            proxlb_data (Dict[str, Any]): A dictionary containing ProxLB configuration, metadata, and node information.
                - proxlb_data["meta"]["patching"]["maximum_nodes"]: Maximum number of nodes to patch in this run (default is 1).
                - proxlb_data["nodes"]: Dictionary of node objects, each with a "patching" status and "name".

        Returns:
            Dict[str, Any]: The updated proxlb_data dictionary with:
                - proxlb_data["meta"]["patching"]: List of node names selected for patching in this run.
                - proxlb_data["nodes"]: Updated node objects with "patching" status set to True for selected nodes.
        """
        logger.debug("Starting: get_node_patching.")

        nodes_patching_execution = []
        nodes_patching_count = proxlb_data["meta"].get("patching", {}).get("maximum_nodes", 1)
        nodes_patching = [node for node in proxlb_data["nodes"].values() if node["patching"]]
        nodes_patching_sorted = sorted(nodes_patching, key=lambda x: x["name"])
        logger.debug(f"{len(nodes_patching)} nodes are pending for patching. Patching up to {nodes_patching_count} nodes in this run.")

        if len(nodes_patching_sorted) > 0:
            nodes = nodes_patching_sorted[:nodes_patching_count]
            for node in nodes:
                nodes_patching_execution.append(node["name"])
                proxlb_data['nodes'][node['name']]['patching'] = True
                logger.info(f"Node {node['name']} is going to be patched.")
                logger.info(f"Node {node['name']} is set to maintenance.")

        proxlb_data["meta"]["patching"] = nodes_patching_execution

        logger.debug("Finished: get_node_patching.")
        return proxlb_data

    def patch_node(self, proxmox_api: any, proxlb_data: Dict[str, Any]):
        """
        Patches Proxmox nodes if no running guests are detected.

        This method iterates over the nodes specified in the `proxlb_data` dictionary under the "meta" -> "patching" key.
        For each node, it checks for running QEMU (VM) and LXC (container) guests using the provided Proxmox API client.
        If any guests are running, patching is skipped for that node and a warning is logged.
        If no guests are running, the method proceeds to patch the node (API calls are commented out) and logs the actions.
        Rebooting the node after patching is also logged (API call commented out).

        Args:
            proxmox_api (Any): An instance of the Proxmox API client used to interact with the cluster.
            proxlb_data (Dict[str, Any]): A dictionary containing metadata, including the list of nodes to patch under "meta" -> "patching".

        Returns:
            None
        """
        logger.debug("Starting: patch_node.")

        for node in proxlb_data["meta"]["patching"]:
            node_guests = []
            guests_vm = proxmox_api.nodes(node).qemu.get()
            guests_ct = proxmox_api.nodes(node).lxc.get()
            guests_vm = [vm for vm in guests_vm if vm["status"] == "running"]
            guests_ct = [ct for ct in guests_ct if ct["status"] == "running"]
            guests_count = len(guests_vm) + len(guests_ct)

            # Do not proceed when we still have someho guests running on the node
            if guests_vm or guests_ct:
                logger.warning(f"Node {node} has {guests_count} running guest(s). Patching will be skipped.")
            else:
                logger.debug(f"Node {node} has no running guests. Proceeding with patching.")
                # Upgrading a node by API requires the patched 'pve-manager' package
                # from gyptazy including the new 'upgrade' endpoint.
                # proxmox_api.nodes(node).apt.upgrade.post()
                logger.debug(f"Node {node} has been patched.")
                logger.debug(f"Node {node} is going to reboot.")
                # proxmox_api.nodes(node).status.reboot.post()

        logger.debug("Finished: patch_node.")
