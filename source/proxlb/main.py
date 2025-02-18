"""
Module providing a function printing python version.
"""

import logging
from utils.logger import SystemdLogger
from utils.cli_parser import CliParser
from utils.config_parser import ConfigParser
from utils.proxmox_api import ProxmoxApi
from models.nodes import Nodes
from models.guests import Guests
from models.calculations import Calculations


def main():
    """
    ProxLB main function
    """
    # Initialize logging handler
    logger = SystemdLogger(level=logging.INFO)

    # Parses arguments passed from the CLI
    cli_parser = CliParser()
    cli_args = cli_parser.parse_args()

    # Parse ProxLB config file
    config_parser = ConfigParser(cli_args.config)
    proxlb_config = config_parser.get_config()

    # Update log level from config and fallback to INFO if not defined
    logger.set_log_level(proxlb_config.get('service', {}).get('log_level', 'INFO'))

    # Connect to Proxmox API & create API object
    proxmox_api = ProxmoxApi(proxlb_config)

    # Overwrite password after creating the API object
    proxlb_config["proxmox_api"]["pass"] = "********"

    # Get all required objects from the Proxmox cluster
    meta = {"meta": proxlb_config}
    nodes = Nodes.get_nodes(proxmox_api)
    nodes = Nodes.set_node_maintenance(nodes, proxlb_config)
    nodes = Nodes.set_node_ignore(nodes, proxlb_config)
    guests = Guests.get_guests(proxmox_api, nodes)

    # Merge obtained objects from the Proxmox cluster for further usage
    proxlb_data = {**nodes, **guests, **meta}

    # Update the initial node resource assignments by all guests
    Calculations.update_node_assignments(proxlb_data)

    # Perform balancing calculations
    for vm, meta in proxlb_data["guests"].items():
        #print(proxlb_data["meta"]["balancing"])
        print(f"cbc14: {proxlb_data["nodes"]["cbc-kvm14"]["memory_used_percent"]} | cbc15: {proxlb_data["nodes"]["cbc-kvm15"]["memory_used_percent"]} | cbc16: {proxlb_data["nodes"]["cbc-kvm16"]["memory_used_percent"]}")
        print(f"guest: {vm} moving: {proxlb_data["guests"][vm]["node_current"]} -> {proxlb_data["guests"][vm]["node_target"]} | {proxlb_data["guests"][vm]["affinity_groups"]} | {proxlb_data["guests"][vm]["anti_affinity_groups"]}")
        Calculations.get_balanciness(proxlb_data)
        Calculations.get_largest_guest(proxlb_data)
        Calculations.get_most_free_node(proxlb_data)
        Calculations.val_affinty_rules(proxlb_data)
        Calculations.update_resources(proxlb_data)


    print("OK")


if __name__ == "__main__":
    main()
