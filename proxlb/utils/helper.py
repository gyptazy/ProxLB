"""
The Helper class provides some basic helper functions to not mess up the code in other
classes.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import ipaddress
import json
import urllib.error
import urllib.request
import uuid
import socket
import sys
import time
import typing
import utils.version
from utils.logger import SystemdLogger
from typing import Dict, Any

logger = SystemdLogger()


class Helper:
    """
    The Helper class provides some basic helper functions to not mess up the code in other
    classes.

    Methods:
        __init__():
            Initializes the general Helper class.

        get_uuid_string() -> str:
            Generates a random uuid and returns it as a string.

        log_node_metrics(proxlb_data: Dict[str, Any], init: bool = True) -> None:
            Logs the memory, CPU, and disk usage metrics of nodes in the provided proxlb_data dictionary.

        get_version(print_version: bool = False) -> None:
            Returns the current version of ProxLB and optionally prints it to stdout.

        get_daemon_mode(proxlb_config: Dict[str, Any]) -> None:
            Checks if the daemon mode is active and handles the scheduling accordingly.
    """
    def __init__(self):
        """
        Initializes the general Helper class.
        """

    @staticmethod
    def get_uuid_string() -> str:
        """
        Generates a random uuid and returns it as a string.

        Args:
            None

        Returns:
            Str: Returns a random uuid as a string.
        """
        logger.debug("Starting: get_uuid_string.")
        generated_uuid = uuid.uuid4()
        logger.debug("Finished: get_uuid_string.")
        return str(generated_uuid)

    @staticmethod
    def log_node_metrics(proxlb_data: Dict[str, Any], init: bool = True) -> None:
        """
        Logs the memory, CPU, and disk usage metrics of nodes in the provided proxlb_data dictionary.

        This method processes the usage metrics of nodes and logs them. It also updates the
        'statistics' field in the 'meta' section of the proxlb_data dictionary with the
        memory, CPU, and disk usage metrics before and after a certain operation.

            proxlb_data (Dict[str, Any]): A dictionary containing node metrics and metadata.
            init (bool): A flag indicating whether to initialize the 'before' statistics
                        (True) or update the 'after' statistics (False). Default is True.
        """
        logger.debug("Starting: log_node_metrics.")
        nodes_usage_memory = " | ".join([f"{key}: {value['memory_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
        nodes_usage_cpu = "  | ".join([f"{key}: {value['cpu_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])
        nodes_usage_disk = " | ".join([f"{key}: {value['disk_used_percent']:.2f}%" for key, value in proxlb_data["nodes"].items()])

        if init:
            proxlb_data["meta"]["statistics"] = {"before": {"memory": nodes_usage_memory, "cpu": nodes_usage_cpu, "disk": nodes_usage_disk}, "after": {"memory": "", "cpu": "", "disk": ""}}
        else:
            proxlb_data["meta"]["statistics"]["after"] = {"memory": nodes_usage_memory, "cpu": nodes_usage_cpu, "disk": nodes_usage_disk}

        logger.debug(f"Nodes usage memory: {nodes_usage_memory}")
        logger.debug(f"Nodes usage cpu:    {nodes_usage_cpu}")
        logger.debug(f"Nodes usage disk:   {nodes_usage_disk}")
        logger.debug("Finished: log_node_metrics.")

    @staticmethod
    def get_version(print_version: bool = False) -> None:
        """
        Returns the current version of ProxLB and optionally prints it to stdout.

        Parameters:
            print_version (bool): If True, prints the version information to stdout and exits the program.

        Returns:
            None
        """
        if print_version:
            print(f"{utils.version.__app_name__} version: {utils.version.__version__}\n(C) 2025 by {utils.version.__author__}\n{utils.version.__url__}")
            sys.exit(0)

    @staticmethod
    def get_daemon_mode(proxlb_config: Dict[str, Any]) -> None:
        """
        Checks if the daemon mode is active and handles the scheduling accordingly.

        Parameters:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

        Returns:
            None
        """
        logger.debug("Starting: get_daemon_mode.")
        if proxlb_config.get("service", {}).get("daemon", True):

            # Validate schedule format which changed in v1.1.1
            if type(proxlb_config["service"].get("schedule", None)) != dict:
                logger.error("Invalid format for schedule. Please use 'hours' or 'minutes'.")
                sys.exit(1)

            # Convert hours to seconds
            if proxlb_config["service"]["schedule"].get("format", "hours") == "hours":
                sleep_seconds = proxlb_config.get("service", {}).get("schedule", {}).get("interval", 12) * 3600
            # Convert minutes to seconds
            elif proxlb_config["service"]["schedule"].get("format", "hours") == "minutes":
                sleep_seconds = proxlb_config.get("service", {}).get("schedule", {}).get("interval", 720) * 60
            else:
                logger.error("Invalid format for schedule. Please use 'hours' or 'minutes'.")
                sys.exit(1)

            logger.info(f"Daemon mode active: Next run in: {proxlb_config.get('service', {}).get('schedule', {}).get('interval', 12)} {proxlb_config['service']['schedule'].get('format', 'hours')}.")
            time.sleep(sleep_seconds)

        else:
            logger.debug("Successfully executed ProxLB. Daemon mode not active - stopping.")
            print("Daemon mode not active - stopping.")
            sys.exit(0)

        logger.debug("Finished: get_daemon_mode.")

    @staticmethod
    def print_json(proxlb_config: Dict[str, Any], print_json: bool = False) -> None:
        """
        Prints the calculated balancing matrix as a JSON output to stdout.

        Parameters:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.

        Returns:
            None
        """
        logger.debug("Starting: print_json.")
        if print_json:
            # Create a filtered list by stripping the 'meta' key from the proxlb_config dictionary
            # to make sure that no credentials are leaked.
            filtered_data = {k: v for k, v in proxlb_config.items() if k != "meta"}
            print(json.dumps(filtered_data, indent=4))

        logger.debug("Finished: print_json.")

    @staticmethod
    def create_wol_magic_packet(mac_address: str) -> bytes:
        """
        Create a magic packet from a given MAC adddress for wake-on-lan.

        A magic packet is a packet that can be used with the for wake on lan
        protocol to wake up a computer. The packet is constructed from the
        mac address given as a parameter.

        Parameters:
            mac_address: The mac address that should be parsed into a magic packet.

        Orig-Author: Remco Haszing @remcohaszing (https://github.com/remcohaszing/pywakeonlan)

        """
        logger.debug("Starting: create_wol_magic_packet.")
        if len(mac_address) == 17:
            sep = mac_address[2]
            mac_address = mac_address.replace(sep, '')
        elif len(mac_address) == 14:
            sep = mac_address[4]
            mac_address = mac_address.replace(sep, '')
        if len(mac_address) != 12:
            raise ValueError('Incorrect MAC address format')
        logger.debug("Finished: create_wol_magic_packet.")
        return bytes.fromhex('F' * 12 + mac_address * 16)

    @staticmethod
    def send_wol_packet(self, mac_address: str, interface: str, address_family: typing.Optional[socket.AddressFamily] = None) -> None:
        """
        Sends a magic packet to a given MAC address on a given interface for wake-on-lan.

        Parameters:
            mac_address: The mac address that should be used for wake-on-lan.
            interface: The network interface that should be used for wake-on-lan.

        Returns:
            None

        Orig-Author: Remco Haszing @remcohaszing (https://github.com/remcohaszing/pywakeonlan)
        """
        logger.debug("Starting: send_wol_packet.")
        packets = [self.create_wol_magic_packet(mac) for mac in macs]

        with socket.socket(address_family, socket.SOCK_DGRAM) as sock:
            if interface is not None:
                sock.bind((interface, 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.connect(("255.255.255.255", 9))
            for packet in packets:
                sock.send(packet)

        logger.debug("Finished: send_wol_packet.")

    @staticmethod
    def get_local_hostname() -> str:
        """
        Retruns the local hostname of the executing system.

        Parameters:
            None

        Returns:
            str: The local hostname of the executing system.
        """
        logger.debug("Starting: get_local_hostname.")
        hostname = socket.gethostname()
        logger.debug("Systems local hostname is: {hostname}")
        logger.debug("Finished: get_local_hostname.")
        return hostname

    @staticmethod
    def http_client_get(uri: str) -> str:
        """
        Receives the content of a GET request from a given URI.

        Parameters:
            uri (str): The URI to get the content from.

        Returns:
            str: The response content.
        """
        logger.debug("Starting: http_client_get.")
        http_charset = "utf-8"
        http_headers = {
            "User-Agent": "ProxLB client/1.0"
        }
        http_request = urllib.request.Request(uri, headers=http_headers, method="GET")

        try:
            logger.debug("Get http client information from {uri}/{path}.")
            with urllib.request.urlopen(http_request) as response:
                http_client_content = response.read().decode(http_charset)
                return http_client_content
        except urllib.error.HTTPError as e:
            print(f"HTTP error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL error: {e.reason}")
        logger.debug("Finished: http_client_get.")

    @staticmethod
    def http_client_post(uri: str, data: Dict[str, Any]) -> str:
        """
        Sends a POST request with JSON data to the given URI.

        Parameters:
            uri (str): The URI to send the POST request to.
            data (dict): The data to send in the request body.

        Returns:
            str: The response content.
        """
        logger.debug("Starting: http_client_post.")
        http_charset = "utf-8"
        http_json_data = json.dumps(data).encode(http_charset)
        http_headers = {
            "User-Agent": "ProxLB client/1.0",
            "Content-Type": "application/json"
        }
        http_request = urllib.request.Request(uri, data=http_json_data, headers=http_headers, method="POST")

        try:
            logger.debug(f"Sending HTTP client information to {uri}.")
            with urllib.request.urlopen(http_request) as response:
                http_client_content = response.read().decode(http_charset)
                return http_client_content
        except urllib.error.HTTPError as e:
            print(f"HTTP error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL error: {e.reason}")
        logger.debug("Finished: http_client_post.")
