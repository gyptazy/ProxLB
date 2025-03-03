"""
The Balancing class is responsible for processing workloads on Proxmox clusters.
It processes the previously generated data (held in proxlb_data) and moves guests
and other supported types across Proxmox clusters based on the defined values by an operator.
"""


__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import proxmoxer
import time
from utils.logger import SystemdLogger
from typing import Dict, Any

logger = SystemdLogger()


class Balancing:
    """
    The balancing class is responsible for processing workloads on Proxmox clusters.
    The previously generated data (hold in proxlb_data) will processed and guests and
    other supported types will be moved across Proxmox clusters based on the defined
    values by an operator.

    Methods:
    __init__(self, proxmox_api: any, proxlb_data: Dict[str, Any]):
        Initializes the Balancing class with the provided ProxLB data and initiates the rebalancing
        process for guests.

    exec_rebalancing_vm(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str) -> None:
        Executes the rebalancing of a virtual machine (VM) to a new node within the cluster. Logs the migration
        process and handles exceptions.

    exec_rebalancing_ct(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str) -> None:
        Executes the rebalancing of a container (CT) to a new node within the cluster. Logs the migration
        process and handles exceptions.

    get_rebalancing_job_status(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str, guest_current_node: str, job_id: int, retry_counter: int = 1) -> bool:
        Monitors the status of a rebalancing job on a Proxmox node until it completes or a timeout
        is reached. Returns True if the job completed successfully, False otherwise.
    """

    def __init__(self, proxmox_api: any, proxlb_data: Dict[str, Any]):
        """
        Initializes the Balancing class with the provided ProxLB data.

        Args:
            proxlb_data (dict): The data required for balancing VMs and CTs.
        """
        for guest_name, guest_meta in proxlb_data["guests"].items():

            if guest_meta["node_current"] != guest_meta["node_target"]:
                guest_id = guest_meta["id"]
                guest_node_current = guest_meta["node_current"]
                guest_node_target = guest_meta["node_target"]

                # VM Balancing
                if guest_meta["type"] == "vm":
                    self.exec_rebalancing_vm(proxmox_api, proxlb_data, guest_name)

                # CT Balancing
                elif guest_meta["type"] == "ct":
                    self.exec_rebalancing_ct(proxmox_api, proxlb_data, guest_name)

                # Hopefully never reaching, but should be catched
                else:
                    logger.critical(f"Balancing: Got unexpected guest type: {guest_meta['type']}. Cannot proceed guest: {guest_meta['name']}.")

    def exec_rebalancing_vm(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str) -> None:
        """
        Executes the rebalancing of a virtual machine (VM) to a new node within the cluster.
        This function initiates the migration of a specified VM to a target node as part of the
        load balancing process. It logs the migration process and handles any exceptions that
        may occur during the migration.
        Args:
            proxmox_api (object): The Proxmox API client instance used to interact with the Proxmox cluster.
            proxlb_data (dict): A dictionary containing data related to the ProxLB load balancing configuration.
            guest_name (str): The name of the guest VM to be migrated.
        Raises:
            proxmox_api.core.ResourceException: If an error occurs during the migration process.
        Returns:
            None
        """
        logger.debug("Starting: exec_rebalancing_vm.")
        guest_id = proxlb_data["guests"][guest_name]["id"]
        guest_node_current = proxlb_data["guests"][guest_name]["node_current"]
        guest_node_target = proxlb_data["guests"][guest_name]["node_target"]

        if proxlb_data["meta"]["balancing"].get("live", True):
            online_migration = 1
        else:
            online_migration = 0

        if proxlb_data["meta"]["balancing"].get("with_local_disks", True):
            with_local_disks = 1
        else:
            with_local_disks = 0

        migration_options = {
            'target': {guest_node_target},
            'online': online_migration,
            'with-local-disks': with_local_disks
        }

        try:
            logger.debug(f"Balancing: Starting to migrate guest {guest_name} of type VM.")
            job_id = proxmox_api.nodes(guest_node_current).qemu(guest_id).migrate().post(**migration_options)
            job = self.get_rebalancing_job_status(proxmox_api, proxlb_data, guest_name, guest_node_current, job_id)
        except proxmoxer.core.ResourceException as proxmox_api_error:
            logger.critical(f"Balancing: Failed to migrate guest {guest_name} of type CT due to some Proxmox errors. Please check if resource is locked or similar.")

        logger.debug("Finished: exec_rebalancing_vm.")

    def exec_rebalancing_ct(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str) -> None:
        """
        Executes the rebalancing of a container (CT) to a new node within the cluster.
        This function initiates the migration of a specified CT to a target node as part of the
        load balancing process. It logs the migration process and handles any exceptions that
        may occur during the migration.
        Args:
            proxmox_api (object): The Proxmox API client instance used to interact with the Proxmox cluster.
            proxlb_data (dict): A dictionary containing data related to the ProxLB load balancing configuration.
            guest_name (str): The name of the guest CT to be migrated.
        Raises:
            proxmox_api.core.ResourceException: If an error occurs during the migration process.
        Returns:
            None
        """
        logger.debug("Starting: exec_rebalancing_ct.")
        guest_id = proxlb_data["guests"][guest_name]["id"]
        guest_node_current = proxlb_data["guests"][guest_name]["node_current"]
        guest_node_target = proxlb_data["guests"][guest_name]["node_target"]

        try:
            logger.debug(f"Balancing: Starting to migrate guest {guest_name} of type CT.")
            job_id = proxmox_api.nodes(guest_node_current).lxc(guest_id).migrate().post(target=guest_node_target, restart=1)
            job = self.get_rebalancing_job_status(proxmox_api, proxlb_data, guest_name, guest_node_current, job_id)
        except proxmoxer.core.ResourceException as proxmox_api_error:
            logger.critical(f"Balancing: Failed to migrate guest {guest_name} of type CT due to some Proxmox errors. Please check if resource is locked or similar.")

        logger.debug("Finished: exec_rebalancing_ct.")

    def get_rebalancing_job_status(self, proxmox_api: any, proxlb_data: Dict[str, Any], guest_name: str, guest_current_node: str, job_id: int, retry_counter: int = 1) -> bool:
        """
        Monitors the status of a rebalancing job on a Proxmox node until it completes or a timeout is reached.

        Args:
            proxmox_api (object): The Proxmox API client instance.
            proxlb_data (dict): The ProxLB configuration data.
            guest_name (str): The name of the guest (virtual machine) being rebalanced.
            guest_current_node (str): The current node where the guest is running.
            job_id (str): The ID of the rebalancing job to monitor.
            retry_counter (int, optional): The current retry count. Defaults to 1.

        Returns:
            bool: True if the job completed successfully, False otherwise.
        """
        logger.debug("Starting: get_rebalancing_job_status.")
        # Parallel migrations can take a huge time and create a higher load, if not defined by an
        # operator we will use a sequential mode by default
        if not proxlb_data["meta"]["balancing"].get("parallel", False):
            job = proxmox_api.nodes(guest_current_node).tasks(job_id).status().get()

            # Watch job id until it finalizes
            if job["status"] == "running":
                # Do not hammer the API while
                # watching the job status
                time.sleep(10)
                retry_counter += 1

                # Run recursion until we hit the soft-limit of maximum migration time for a guest
                if retry_counter < proxlb_data["meta"]["balancing"].get("max_job_validation", 1800):
                    logger.debug(f"Balancing: Job ID {job_id} (guest: {guest_name}) for migration is still running... (Run: {retry_counter})")
                    self.get_rebalancing_job_status(proxmox_api, proxlb_data, guest_name, guest_current_node, job_id, retry_counter)
                else:
                    logger.warning(f"Balancing: Job ID {job_id} (guest: {guest_name}) for migration took too long. Please check manually.")
                    logger.debug("Finished: get_rebalancing_job_status.")
                    return False

            # Validate job output for errors when finished
            if job["status"] == "stopped":

                if job["exitstatus"] == "OK":
                    logger.debug(f"Balancing: Job ID {job_id} (guest: {guest_name}) was sucessfully.")
                    logger.debug("Finished: get_rebalancing_job_status.")
                    return True
                else:
                    logger.critical(f"Balancing: Job ID {job_id} (guest: {guest_name}) went into an error! Please check manually.")
                    logger.debug("Finished: get_rebalancing_job_status.")
                    return False
