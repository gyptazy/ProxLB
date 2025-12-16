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
from itertools import islice
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
            proxmox_api (object): The Proxmox API client instance used to interact with the Proxmox cluster.
            proxlb_data (dict): A dictionary containing data related to the ProxLB load balancing configuration.
        """
        def chunk_dict(data, size):
            """
            Splits a dictionary into chunks of a specified size.
            Args:
                data (dict): The dictionary to be split into chunks.
                size (int): The size of each chunk.
            Yields:
                dict: A chunk of the original dictionary with the specified size.
            """
            logger.debug("Starting: chunk_dict.")
            it = iter(data.items())
            for chunk in range(0, len(data), size):
                yield dict(islice(it, size))

        # Validate if balancing should be performed in parallel or sequentially.
        # If parallel balancing is enabled, set the number of parallel jobs.
        parallel_jobs = proxlb_data["meta"]["balancing"].get("parallel_jobs", 5)
        if not proxlb_data["meta"]["balancing"].get("parallel", False):
            parallel_jobs = 1
            logger.debug("Balancing: Parallel balancing is disabled. Running sequentially.")
        else:
            logger.debug(f"Balancing: Parallel balancing is enabled. Running with {parallel_jobs} parallel jobs.")

        for chunk in chunk_dict(proxlb_data["guests"], parallel_jobs):
            jobs_to_wait = []

            for guest_name, guest_meta in chunk.items():

                # Check if the guest's target is not the same as the current node
                if guest_meta["node_current"] != guest_meta["node_target"]:

                    # Check if the guest is not ignored and perform the balancing
                    # operation based on the guest type
                    if not guest_meta["ignore"]:
                        job_id = None

                        # VM Balancing
                        if guest_meta["type"] == "vm":
                            if 'vm' in proxlb_data["meta"]["balancing"].get("balance_types", []):
                                logger.debug(f"Balancing: Balancing for guest {guest_name} of type VM started.")
                                job_id = self.exec_rebalancing_vm(proxmox_api, proxlb_data, guest_name)
                            else:
                                logger.debug(
                                    f"Balancing: Balancing for guest {guest_name} will not be performed. "
                                    "Guest is of type VM which is not included in allowed balancing types.")

                        # CT Balancing
                        elif guest_meta["type"] == "ct":
                            if 'ct' in proxlb_data["meta"]["balancing"].get("balance_types", []):
                                logger.debug(f"Balancing: Balancing for guest {guest_name} of type CT started.")
                                job_id = self.exec_rebalancing_ct(proxmox_api, proxlb_data, guest_name)
                            else:
                                logger.debug(
                                    f"Balancing: Balancing for guest {guest_name} will not be performed. "
                                    "Guest is of type CT which is not included in allowed balancing types.")

                        # Just in case we get a new type of guest in the future
                        else:
                            logger.critical(f"Balancing: Got unexpected guest type: {guest_meta['type']}. Cannot proceed guest: {guest_meta['name']}.")

                        if job_id:
                            jobs_to_wait.append((guest_name, guest_meta["node_current"], job_id))

                    else:
                        logger.debug(f"Balancing: Guest {guest_name} is ignored and will not be rebalanced.")
                else:
                    logger.debug(f"Balancing: Guest {guest_name} is already on the target node {guest_meta['node_target']} and will not be rebalanced.")

            # Wait for all jobs in the current chunk to complete
            for guest_name, node, job_id in jobs_to_wait:
                if job_id:
                    self.get_rebalancing_job_status(proxmox_api, proxlb_data, guest_name, node, job_id)

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
        job_id = None

        if proxlb_data["meta"]["balancing"].get("live", True):
            online_migration = 1
        else:
            online_migration = 0

        if proxlb_data["meta"]["balancing"].get("with_local_disks", True):
            with_local_disks = 1
        else:
            with_local_disks = 0

        migration_options = {
            'target': guest_node_target,
            'online': online_migration,
            'with-local-disks': with_local_disks,
        }

        # Conntrack state aware migrations are not supported in older
        # PVE versions, so we should not add it by default.
        if proxlb_data["meta"]["balancing"].get("with_conntrack_state", True):
            migration_options['with-conntrack-state'] = 1

        try:
            logger.info(f"Balancing: Starting to migrate VM guest {guest_name} from {guest_node_current} to {guest_node_target}.")
            job_id = proxmox_api.nodes(guest_node_current).qemu(guest_id).migrate().post(**migration_options)
        except proxmoxer.core.ResourceException as proxmox_api_error:
            logger.critical(f"Balancing: Failed to migrate guest {guest_name} of type VM due to some Proxmox errors. Please check if resource is locked or similar.")
            logger.debug(f"Balancing: Failed to migrate guest {guest_name} of type VM due to some Proxmox errors: {proxmox_api_error}")

        logger.debug("Finished: exec_rebalancing_vm.")
        return job_id

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
        job_id = None

        try:
            logger.info(f"Balancing: Starting to migrate CT guest {guest_name} from {guest_node_current} to {guest_node_target}.")
            job_id = proxmox_api.nodes(guest_node_current).lxc(guest_id).migrate().post(target=guest_node_target, restart=1)
        except proxmoxer.core.ResourceException as proxmox_api_error:
            logger.critical(f"Balancing: Failed to migrate guest {guest_name} of type CT due to some Proxmox errors. Please check if resource is locked or similar.")
            logger.debug(f"Balancing: Failed to migrate guest {guest_name} of type CT due to some Proxmox errors: {proxmox_api_error}")

        logger.debug("Finished: exec_rebalancing_ct.")
        return job_id

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
        job = proxmox_api.nodes(guest_current_node).tasks(job_id).status().get()

        # Fetch actual migration job status if this got spawned by a HA job
        if job["type"] == "hamigrate":
            logger.debug(f"Balancing: Job ID {job_id} (guest: {guest_name}) is a HA migration job. Fetching underlying migration job...")
            time.sleep(1)
            vm_id = int(job["id"])
            qm_migrate_jobs = proxmox_api.nodes(guest_current_node).tasks.get(typefilter="qmigrate", vmid=vm_id, start=0, source="active", limit=1)

            if len(qm_migrate_jobs) > 0:
                job = qm_migrate_jobs[0]
                job_id = job["upid"]
                logger.debug(f'Overwriting job polling for: ID {job_id} (guest: {guest_name}) by {job}')
        else:
            logger.debug(f"Balancing: Job ID {job_id} (guest: {guest_name}) is a standard migration job. Proceeding with status check.")

        # Watch job id until it finalizes
        # Note: Unsaved jobs are delivered in uppercase from Proxmox API
        if job.get("status", "").lower() == "running":
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
                logger.debug(f"Balancing: Job ID {job_id} (guest: {guest_name}) was successfully.")
                logger.debug("Finished: get_rebalancing_job_status.")
                return True
            else:
                logger.critical(f"Balancing: Job ID {job_id} (guest: {guest_name}) went into an error! Please check manually.")
                logger.debug("Finished: get_rebalancing_job_status.")
                return False
