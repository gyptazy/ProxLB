"""
The Guests class retrieves all running guests on the Proxmox cluster across all available nodes.
It handles both VM and CT guest types, collecting their resource metrics.
"""

from typing import Dict, Any
from utils.logger import SystemdLogger
from models.tags import Tags

logger = SystemdLogger()


class Guests:
    """
    The Guests class retrieves all running guests on the Proxmox cluster across all available nodes.
    It handles both VM and CT guest types, collecting their resource metrics.
    """
    def __init__(self):
        """
        Initializes the Guests class with the provided ProxLB data.
        """

    @staticmethod
    def get_guests(proxmox_api: any, nodes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metrics of all guests in a Proxmox cluster.

        This method retrieves metrics for all running guests (both VMs and CTs) across all nodes in the Proxmox cluster.
        It iterates over each node and collects resource metrics for each running guest, including CPU, memory, and disk usage.
        Additionally, it retrieves tags and affinity/anti-affinity groups for each guest.

        Args:
            proxmox_api (any): The Proxmox API client instance.
            nodes (Dict[str, Any]): A dictionary containing information about the nodes in the Proxmox cluster.

        Returns:
            Dict[str, Any]: A dictionary containing metrics and information for all running guests.
        """
        logger.debug("Starting: get_guests.")
        guests = {"guests": {}}

        # Guest objects are always only in the scope of a node.
        # Therefore, we need to iterate over all nodes to get all guests.
        for node in nodes['nodes'].keys():

            # VM objects: Iterate over all VMs on the current node by the qemu API object.
            # Unlike the nodes we need to keep them even when being ignored to create proper
            # resource metrics for rebalancing to ensure that we do not overprovisiong the node.
            for guest in proxmox_api.nodes(node).qemu.get():
                if guest['status'] == 'running':
                    guests['guests'][guest['name']] = {}
                    guests['guests'][guest['name']]['name'] = guest['name']
                    guests['guests'][guest['name']]['cpu_total'] = guest['cpus']
                    guests['guests'][guest['name']]['cpu_used'] = guest['cpu']
                    guests['guests'][guest['name']]['memory_total'] = guest['maxmem']
                    guests['guests'][guest['name']]['memory_used'] = guest['mem']
                    guests['guests'][guest['name']]['disk_total'] = guest['maxdisk']
                    guests['guests'][guest['name']]['disk_used'] = guest['disk']
                    guests['guests'][guest['name']]['id'] = guest['vmid']
                    guests['guests'][guest['name']]['node_current'] = node
                    guests['guests'][guest['name']]['node_target'] = node
                    guests['guests'][guest['name']]['processed'] = False
                    guests['guests'][guest['name']]['tags'] = Tags.get_tags_from_guests(proxmox_api, node, guest['vmid'], 'vm')
                    guests['guests'][guest['name']]['affinity_groups'] = Tags.get_affinity_groups(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['anti_affinity_groups'] = Tags.get_anti_affinity_groups(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['ignore'] = Tags.get_ignore(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['type'] = 'vm'
                else:
                    logger.debug(f'Metric for VM {guest["name"]} ignored because VM is not running.')

            # CT objects: Iterate over all VMs on the current node by the lxc API object.
            # Unlike the nodes we need to keep them even when being ignored to create proper
            # resource metrics for rebalancing to ensure that we do not overprovisiong the node.
            for guest in proxmox_api.nodes(node).lxc.get():
                if guest['status'] == 'running':
                    guests['guests'][guest['name']] = {}
                    guests['guests'][guest['name']]['name'] = guest['name']
                    guests['guests'][guest['name']]['cpu_total'] = guest['cpus']
                    guests['guests'][guest['name']]['cpu_used'] = guest['cpu']
                    guests['guests'][guest['name']]['memory_total'] = guest['maxmem']
                    guests['guests'][guest['name']]['memory_used'] = guest['mem']
                    guests['guests'][guest['name']]['disk_total'] = guest['maxdisk']
                    guests['guests'][guest['name']]['disk_used'] = guest['disk']
                    guests['guests'][guest['name']]['id'] = guest['vmid']
                    guests['guests'][guest['name']]['node_current'] = node
                    guests['guests'][guest['name']]['node_target'] = node
                    guests['guests'][guest['name']]['processed'] = False
                    guests['guests'][guest['name']]['tags'] = Tags.get_tags_from_guests(proxmox_api, node, guest['vmid'], 'ct')
                    guests['guests'][guest['name']]['affinity_groups'] = Tags.get_affinity_groups(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['anti_affinity_groups'] = Tags.get_anti_affinity_groups(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['ignore'] = Tags.get_ignore(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['type'] = 'ct'
                else:
                    logger.debug(f'Metric for CT {guest["name"]} ignored because CT is not running.')

        logger.debug("Finished: get_guests.")
        return guests
