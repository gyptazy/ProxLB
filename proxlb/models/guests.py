"""
The Guests class retrieves all running guests on the Proxmox cluster across all available nodes.
It handles both VM and CT guest types, collecting their resource metrics.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


from typing import Dict, Any
from utils.logger import SystemdLogger
from models.pools import Pools
from models.ha_rules import HaRules
from models.tags import Tags
import time

logger = SystemdLogger()


class Guests:
    """
    The Guests class retrieves all running guests on the Proxmox cluster across all available nodes.
    It handles both VM and CT guest types, collecting their resource metrics.

    Methods:
        __init__:
            Initializes the Guests class.

        get_guests(proxmox_api: any, nodes: Dict[str, Any]) -> Dict[str, Any]:
            Retrieves metrics for all running guests (both VMs and CTs) across all nodes in the Proxmox cluster.
            It collects resource metrics such as CPU, memory, and disk usage, as well as tags and affinity/anti-affinity groups.
    """
    def __init__(self):
        """
        Initializes the Guests class with the provided ProxLB data.
        """

    @staticmethod
    def get_guests(proxmox_api: any, pools: Dict[str, Any], ha_rules: Dict[str, Any], nodes: Dict[str, Any], meta: Dict[str, Any], proxlb_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metrics of all guests in a Proxmox cluster.

        This method retrieves metrics for all running guests (both VMs and CTs) across all nodes in the Proxmox cluster.
        It iterates over each node and collects resource metrics for each running guest, including CPU, memory, and disk usage.
        Additionally, it retrieves tags and affinity/anti-affinity groups for each guest.

        Args:
            proxmox_api (any): The Proxmox API client instance.
            pools (Dict[str, Any]): A dictionary containing information about the pools in the Proxmox cluster.
            ha_rules (Dict[str, Any]): A dictionary containing information about the HA rules in the
            nodes (Dict[str, Any]): A dictionary containing information about the nodes in the Proxmox cluster.
            meta (Dict[str, Any]): A dictionary containing metadata information.
            proxmox_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

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
                    guests['guests'][guest['name']]['cpu_total'] = int(guest['cpus'])
                    guests['guests'][guest['name']]['cpu_used'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', None)
                    guests['guests'][guest['name']]['cpu_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'some')
                    guests['guests'][guest['name']]['cpu_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'full')
                    guests['guests'][guest['name']]['cpu_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'some', spikes=True)
                    guests['guests'][guest['name']]['cpu_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'full', spikes=True)
                    guests['guests'][guest['name']]['cpu_pressure_hot'] = False
                    guests['guests'][guest['name']]['memory_total'] = guest['maxmem']
                    guests['guests'][guest['name']]['memory_used'] = guest['mem']
                    guests['guests'][guest['name']]['memory_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'some')
                    guests['guests'][guest['name']]['memory_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'full')
                    guests['guests'][guest['name']]['memory_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'some', spikes=True)
                    guests['guests'][guest['name']]['memory_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'full', spikes=True)
                    guests['guests'][guest['name']]['memory_pressure_hot'] = False
                    guests['guests'][guest['name']]['disk_total'] = guest['maxdisk']
                    guests['guests'][guest['name']]['disk_used'] = guest['disk']
                    guests['guests'][guest['name']]['disk_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'some')
                    guests['guests'][guest['name']]['disk_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'full')
                    guests['guests'][guest['name']]['disk_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'some', spikes=True)
                    guests['guests'][guest['name']]['disk_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'full', spikes=True)
                    guests['guests'][guest['name']]['disk_pressure_hot'] = False
                    guests['guests'][guest['name']]['id'] = guest['vmid']
                    guests['guests'][guest['name']]['node_current'] = node
                    guests['guests'][guest['name']]['node_target'] = node
                    guests['guests'][guest['name']]['processed'] = False
                    guests['guests'][guest['name']]['pressure_hot'] = False
                    guests['guests'][guest['name']]['tags'] = Tags.get_tags_from_guests(proxmox_api, node, guest['vmid'], 'vm')
                    guests['guests'][guest['name']]['pools'] = Pools.get_pools_for_guest(guest['name'], pools)
                    guests['guests'][guest['name']]['ha_rules'] = HaRules.get_ha_rules_for_guest(guest['name'], ha_rules, guest['vmid'])
                    guests['guests'][guest['name']]['affinity_groups'] = Tags.get_affinity_groups(guests['guests'][guest['name']]['tags'], guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['anti_affinity_groups'] = Tags.get_anti_affinity_groups(guests['guests'][guest['name']]['tags'], guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['ignore'] = Tags.get_ignore(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['node_relationships'] = Tags.get_node_relationships(guests['guests'][guest['name']]['tags'], nodes, guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['node_relationships_strict'] = Pools.get_pool_node_affinity_strictness(proxlb_config, guests['guests'][guest['name']]['pools'])
                    guests['guests'][guest['name']]['type'] = 'vm'

                    logger.debug(f"Resources of Guest {guest['name']} (type VM) added: {guests['guests'][guest['name']]}")
                else:
                    logger.debug(f'Metric for VM {guest["name"]} ignored because VM is not running.')

            # CT objects: Iterate over all VMs on the current node by the lxc API object.
            # Unlike the nodes we need to keep them even when being ignored to create proper
            # resource metrics for rebalancing to ensure that we do not overprovisiong the node.
            for guest in proxmox_api.nodes(node).lxc.get():
                if guest['status'] == 'running':
                    guests['guests'][guest['name']] = {}
                    guests['guests'][guest['name']]['name'] = guest['name']
                    guests['guests'][guest['name']]['cpu_total'] = int(guest['cpus'])
                    guests['guests'][guest['name']]['cpu_used'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', None)
                    guests['guests'][guest['name']]['cpu_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'some')
                    guests['guests'][guest['name']]['cpu_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'full')
                    guests['guests'][guest['name']]['cpu_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'some', spikes=True)
                    guests['guests'][guest['name']]['cpu_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'cpu', 'full', spikes=True)
                    guests['guests'][guest['name']]['cpu_pressure_hot'] = False
                    guests['guests'][guest['name']]['memory_total'] = guest['maxmem']
                    guests['guests'][guest['name']]['memory_used'] = guest['mem']
                    guests['guests'][guest['name']]['memory_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'some')
                    guests['guests'][guest['name']]['memory_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'full')
                    guests['guests'][guest['name']]['memory_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'some', spikes=True)
                    guests['guests'][guest['name']]['memory_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'memory', 'full', spikes=True)
                    guests['guests'][guest['name']]['memory_pressure_hot'] = False
                    guests['guests'][guest['name']]['disk_total'] = guest['maxdisk']
                    guests['guests'][guest['name']]['disk_used'] = guest['disk']
                    guests['guests'][guest['name']]['disk_pressure_some_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'some')
                    guests['guests'][guest['name']]['disk_pressure_full_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'full')
                    guests['guests'][guest['name']]['disk_pressure_some_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'some', spikes=True)
                    guests['guests'][guest['name']]['disk_pressure_full_spikes_percent'] = Guests.get_guest_rrd_data(proxmox_api, node, guest['vmid'], guest['name'], 'disk', 'full', spikes=True)
                    guests['guests'][guest['name']]['disk_pressure_hot'] = False
                    guests['guests'][guest['name']]['id'] = guest['vmid']
                    guests['guests'][guest['name']]['node_current'] = node
                    guests['guests'][guest['name']]['node_target'] = node
                    guests['guests'][guest['name']]['processed'] = False
                    guests['guests'][guest['name']]['pressure_hot'] = False
                    guests['guests'][guest['name']]['tags'] = Tags.get_tags_from_guests(proxmox_api, node, guest['vmid'], 'ct')
                    guests['guests'][guest['name']]['pools'] = Pools.get_pools_for_guest(guest['name'], pools)
                    guests['guests'][guest['name']]['ha_rules'] = HaRules.get_ha_rules_for_guest(guest['name'], ha_rules, guest['vmid'])
                    guests['guests'][guest['name']]['affinity_groups'] = Tags.get_affinity_groups(guests['guests'][guest['name']]['tags'], guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['anti_affinity_groups'] = Tags.get_anti_affinity_groups(guests['guests'][guest['name']]['tags'], guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['ignore'] = Tags.get_ignore(guests['guests'][guest['name']]['tags'])
                    guests['guests'][guest['name']]['node_relationships'] = Tags.get_node_relationships(guests['guests'][guest['name']]['tags'], nodes, guests['guests'][guest['name']]['pools'], guests['guests'][guest['name']]['ha_rules'], proxlb_config)
                    guests['guests'][guest['name']]['node_relationships_strict'] = Pools.get_pool_node_affinity_strictness(proxlb_config, guests['guests'][guest['name']]['pools'])
                    guests['guests'][guest['name']]['type'] = 'ct'

                    logger.debug(f"Resources of Guest {guest['name']} (type CT) added: {guests['guests'][guest['name']]}")
                else:
                    logger.debug(f'Metric for CT {guest["name"]} ignored because CT is not running.')

        logger.debug("Finished: get_guests.")
        return guests

    @staticmethod
    def get_guest_rrd_data(proxmox_api, node_name: str, vm_id: int, vm_name: str, object_name: str, object_type: str, spikes=False) -> float:
        """
        Retrieves the rrd data metrics for a specific resource (CPU, memory, disk) of a guest VM or CT.

        Args:
            proxmox_api (Any): The Proxmox API client instance.
            node_name (str): The name of the node hosting the guest.
            vm_id (int): The ID of the guest VM or CT.
            vm_name (str): The name of the guest VM or CT.
            object_name (str): The resource type to query (e.g., 'cpu', 'memory', 'disk').
            object_type (str, optional): The pressure type ('some', 'full') or None for average usage.
            spikes (bool, optional): Whether to consider spikes in the calculation. Defaults to False.

        Returns:
            float: The calculated average usage value for the specified resource.
        """
        logger.debug("Starting: get_guest_rrd_data.")
        time.sleep(0.1)

        try:
            if spikes:
                logger.debug(f"Getting spike RRD data for {object_name} from guest: {vm_name}.")
                guest_data_rrd = proxmox_api.nodes(node_name).qemu(vm_id).rrddata.get(timeframe="hour", cf="MAX")
            else:
                logger.debug(f"Getting average RRD data for {object_name} from guest: {vm_name}.")
                guest_data_rrd = proxmox_api.nodes(node_name).qemu(vm_id).rrddata.get(timeframe="hour", cf="AVERAGE")
        except Exception:
            logger.error(f"Failed to retrieve RRD data for guest: {vm_name} (ID: {vm_id}) on node: {node_name}. Using 0.0 as value.")
            logger.debug("Finished: get_guest_rrd_data.")
            return float(0.0)

        if object_type:

            lookup_key = f"pressure{object_name}{object_type}"
            if spikes:
                # RRD data is collected every minute, so we look at the last 6 entries
                # and take the maximum value to represent the spike
                logger.debug(f"Getting RRD data (spike: {spikes}) of pressure for {object_name} {object_type} from guest: {vm_name}.")
                rrd_data_value = [row.get(lookup_key) for row in guest_data_rrd if row.get(lookup_key) is not None]
                rrd_data_value = max(rrd_data_value[-6:], default=0.0)
            else:
                # Calculate the average value from the RRD data entries
                logger.debug(f"Getting RRD data (spike: {spikes}) of pressure for {object_name} {object_type} from guest: {vm_name}.")
                rrd_data_value = sum(entry.get(lookup_key, 0.0) for entry in guest_data_rrd) / len(guest_data_rrd)

        else:
            logger.debug(f"Getting RRD data of cpu usage from guest: {vm_name}.")
            rrd_data_value = sum(entry.get("cpu", 0.0) for entry in guest_data_rrd) / len(guest_data_rrd)

        logger.debug(f"RRD data (spike: {spikes}) for {object_name} from guest: {vm_name}: {rrd_data_value}")
        logger.debug("Finished: get_guest_rrd_data.")
        return rrd_data_value
