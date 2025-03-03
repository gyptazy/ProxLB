"""
ProxLB is a load balancing tool for Proxmox Virtual Environment (PVE) clusters.
It connects to the Proxmox API, retrieves information about nodes, guests, and groups,
and performs calculations to determine the optimal distribution of resources across the
cluster. The tool supports daemon mode for continuous operation and can log metrics and
perform balancing actions based on the configuration provided. It also includes a CLI
parser for handling command-line arguments and a custom logger for systemd integration.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import logging
from utils.logger import SystemdLogger
from utils.cli_parser import CliParser
from utils.config_parser import ConfigParser
from utils.proxmox_api import ProxmoxApi
from models.nodes import Nodes
from models.guests import Guests
from models.groups import Groups
from models.calculations import Calculations
from models.balancing import Balancing
from utils.helper import Helper


def main():
    """
    ProxLB main function
    """
    # Initialize logging handler
    logger = SystemdLogger(level=logging.INFO)

    # Parses arguments passed from the CLI
    cli_parser = CliParser()
    cli_args = cli_parser.parse_args()
    Helper.get_version(cli_args.version)

    # Parse ProxLB config file
    config_parser = ConfigParser(cli_args.config)
    proxlb_config = config_parser.get_config()

    # Update log level from config and fallback to INFO if not defined
    logger.set_log_level(proxlb_config.get('service', {}).get('log_level', 'INFO'))

    # Connect to Proxmox API & create API object
    proxmox_api = ProxmoxApi(proxlb_config)

    # Overwrite password after creating the API object
    proxlb_config["proxmox_api"]["pass"] = "********"

    while True:
        # Get all required objects from the Proxmox cluster
        meta = {"meta": proxlb_config}
        nodes = Nodes.get_nodes(proxmox_api, proxlb_config)
        guests = Guests.get_guests(proxmox_api, nodes)
        groups = Groups.get_groups(guests, nodes)

        # Merge obtained objects from the Proxmox cluster for further usage
        proxlb_data = {**meta, **nodes, **guests, **groups}
        Helper.log_node_metrics(proxlb_data)

        # Update the initial node resource assignments
        # by the previously created groups.
        Calculations.set_node_assignments(proxlb_data)
        Calculations.get_most_free_node(proxlb_data, cli_args.best_node)
        Calculations.relocate_guests_on_maintenance_nodes(proxlb_data)
        Calculations.get_balanciness(proxlb_data)
        Calculations.relocate_guests(proxlb_data)
        Helper.log_node_metrics(proxlb_data, init=False)

        # Perform balancing actions via Proxmox API
        if not cli_args.dry_run:
            Balancing(proxmox_api, proxlb_data)

        # Validate daemon mode
        Helper.get_daemon_mode(proxlb_config)

        logger.debug(f"Finished: __main__")


if __name__ == "__main__":
    main()
