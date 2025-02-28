"""
Module providing a function printing python version.
"""

try:
    import proxmoxer
    PROXMOXER_PRESENT = True
except ImportError:
    PROXMOXER_PRESENT = False
import random
import socket
import sys
try:
    import requests
    REQUESTS_PRESENT = True
except ImportError:
    REQUESTS_PRESENT = False
try:
    import urllib3
    URLLIB3_PRESENT = True
except ImportError:
    URLLIB3_PRESENT = False

from typing import Dict, Any
from utils.logger import SystemdLogger

logger = SystemdLogger()


class ProxmoxApi:
    """
    Handles command-line argument parsing for ProxLB.
    """
    def __init__(self, proxlb_config: Dict[str, Any]) -> None:
        """
        Initialize the ProxmoxApi instance.

        This method sets up the ProxmoxApi instance by testing the required module dependencies
        and establishing a connection to the Proxmox API using the provided configuration.

        Args:
            proxlb_config (Dict[str, Any]): Configuration dictionary containing Proxmox API connection details.

        Returns:
            None
        """
        logger.debug("Starting: ProxmoxApi initialization.")
        self.test_module_dependencies = self.test_dependencies()
        self.proxmox_api = self.api_connect(proxlb_config)
        logger.debug("Finished: ProxmoxApi initialization.")

    def __getattr__(self, name):
        """
        Delegate attribute access to proxmox_api.
        """
        return getattr(self.proxmox_api, name)

    def test_dependencies(self) -> None:
        """
        Test for the presence of required libraries.

        This method checks if the necessary libraries 'proxmoxer', 'urllib3', and 'requests'
        are installed. If any of these libraries are missing, it logs a critical error message
        and terminates the program.

        Returns:
            None

        Raises:
            SystemExit: If the provided imports are not available.
        """
        logger.debug("Starting: test_dependencies.")
        if not PROXMOXER_PRESENT:
            logger.critical("The required library 'proxmoxer' is not installed.")
            sys.exit(1)

        if not URLLIB3_PRESENT:
            logger.critical("The required library 'urllib3' is not installed.")
            sys.exit(1)

        if not REQUESTS_PRESENT:
            logger.critical("The required library 'requests' is not installed.")
            sys.exit(1)

        logger.debug("Finished: test_dependencies.")

    def api_connect_get_hosts(self, proxmox_api_endpoints: list) -> str:
        """
        Perform a connectivity test to determine a working host for the Proxmox API.

        This method takes a list of Proxmox API endpoints and validates their connectivity.
        It returns a working host from the list. If only one endpoint is provided, it is
        returned immediately. If multiple endpoints are provided, each one is tested for
        connectivity. If a valid host is found, it is returned. If multiple valid hosts
        are found, one is chosen at random to distribute the load across the cluster.

        Args:
            proxmox_api_endpoints (list): A list of Proxmox API endpoints to test.

        Returns:
            str: A working Proxmox API host.

        Raises:
            SystemExit: If the provided endpoints are not a list, if the list is empty,
                        or if no valid hosts are found.
        """
        logger.debug("Starting: api_connect_get_hosts.")
        # Pre-validate the given API endpoints
        if not isinstance(proxmox_api_endpoints, list):
            logger.critical(f"The proxmox_api hosts are not defined as a list type.")
            sys.exit(1)

        if not proxmox_api_endpoints:
            logger.critical(f"No proxmox_api hosts are defined.")
            sys.exit(1)

        if len(proxmox_api_endpoints) == 0:
            logger.critical(f"No proxmox_api hosts are defined.")
            sys.exit(1)

        # Get a suitable Proxmox API endpoint. Therefore, we check if we only have
        # a single Proxmox API endpoint or multiple ones. If only one, we can return
        # this one immediately. If this one does not work, the urllib will raise an
        # exception during the connection attempt.
        if len(proxmox_api_endpoints) == 1:
            return proxmox_api_endpoints[0]

        # If we have multiple Proxmox API endpoints, we need to check each one by
        # doing a connection attempt for IPv4 and IPv6. If we find a working one,
        # we return that one. This allows us to define multiple endpoints in a cluster.
        validated_api_hosts = []
        for host in proxmox_api_endpoints:
            validated = self.test_api_proxmox_host(host)
            if validated:
                validated_api_hosts.append(validated)

        if len(validated_api_hosts) > 0:
            # Choose a random host to distribute the load across the cluster
            # as a simple load balancing mechanism.
            return random.choice(validated_api_hosts)

        logger.critical("No valid Proxmox API hosts found.")
        print("No valid Proxmox API hosts found.")

        logger.debug("Finished: api_connect_get_hosts.")
        sys.exit(1)

    def test_api_proxmox_host(self, host: str) -> str:
        """
        Tests the connectivity to a Proxmox host by resolving its IP address and
        checking both IPv4 and IPv6 addresses.

        This function attempts to resolve the given hostname to its IP addresses
        (both IPv4 and IPv6). It then tests the connectivity to the Proxmox API
        using the resolved IP addresses. If the host is reachable via either
        IPv4 or IPv6, the function returns the hostname. If the host is not
        reachable, the function returns False.

        Args:
            host (str): The hostname of the Proxmox server to test.

        Returns:
            str: The hostname if the Proxmox server is reachable.
            bool: False if the Proxmox server is not reachable.
        """
        logger.debug("Starting: test_api_proxmox_host.")
        ip = socket.getaddrinfo(host, None, socket.AF_UNSPEC)
        for address_type in ip:
            if address_type[0] == socket.AF_INET:
                logger.debug(f"{host} is type ipv4.")
                if self.test_api_proxmox_host_ipv4(host):
                    return host
            elif address_type[0] == socket.AF_INET6:
                logger.debug(f"{host} is type ipv6.")
                if self.test_api_proxmox_host_ipv6(host):
                    return host
            else:
                return False

        logger.debug("Finished: test_api_proxmox_host.")

    def test_api_proxmox_host_ipv4(self, host: str, port: int = 8006, timeout: int = 1) -> bool:
        """
        Test the reachability of a Proxmox host on its IPv4 management address.

        This method attempts to establish a TCP connection to the specified host and port
        within a given timeout period. It logs the process and results, indicating whether
        the host is reachable or not.

        Args:
            host (str): The IPv4 address or hostname of the Proxmox host to test.
            port (int, optional): The TCP port to connect to on the host. Defaults to 8006.
            timeout (int, optional): The timeout duration in seconds for the connection attempt. Defaults to 1.

        Returns:
            bool: True if the host is reachable on the specified port, False otherwise.
        """
        logger.debug("Starting: test_api_proxmox_host_ipv4.")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        logger.warning(f"Warning: Host {host} ran into a timout when connectoing on IPv4 for tcp/{port}.")
        result = sock.connect_ex((host, port))

        if result == 0:
            sock.close()
            logger.debug(f"Host {host} is reachable on IPv4 for tcp/{port}.")
            return True

        sock.close()
        logger.warning(f"Host {host} is unreachable on IPv4 for tcp/{port}.")

        logger.debug("Finished: test_api_proxmox_host_ipv4.")
        return False

    def test_api_proxmox_host_ipv6(self, host: str, port: int = 8006, timeout: int = 1) -> bool:
        """
        Test the reachability of a Proxmox host on its IPv6 management address.

        This method attempts to establish a TCP connection to the specified host and port
        within a given timeout period. It logs the process and results, indicating whether
        the host is reachable or not.

        Args:
            host (str): The IPv6 address or hostname of the Proxmox host to test.
            port (int, optional): The TCP port to connect to on the host. Defaults to 8006.
            timeout (int, optional): The timeout duration in seconds for the connection attempt. Defaults to 1.

        Returns:
            bool: True if the host is reachable on the specified port, False otherwise.
        """
        logger.debug("Starting: test_api_proxmox_host_ipv6.")
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        logger.warning(f"Host {host} ran into a timout when connectoing on IPv6 for tcp/{port}.")
        result = sock.connect_ex((host, port))

        if result == 0:
            sock.close()
            logger.debug(f"Host {host} is reachable on IPv6 for tcp/{port}.")
            return True

        sock.close()
        logger.warning(f"Host {host} is unreachable on IPv6 for tcp/{port}.")

        logger.debug("Finished: test_api_proxmox_host_ipv4.")
        return False

    def api_connect(self, proxlb_config: Dict[str, Any]) -> proxmoxer.ProxmoxAPI:
        """
        Establishes a connection to the Proxmox API using the provided configuration.

        This function retrieves the Proxmox API endpoint from the configuration, optionally disables SSL certificate
        validation warnings, and attempts to authenticate and create a ProxmoxAPI object. It handles various exceptions
        related to authentication, connection timeouts, SSL errors, and connection refusals, logging appropriate error
        messages and exiting the program if necessary.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the Proxmox API configuration. Expected keys include:
                - "proxmox_api": A dictionary with the following keys:
                    - "hosts" (List[str]): A list of Proxmox API host addresses.
                    - "user" (str): The username for Proxmox API authentication.
                    - "pass" (str): The password for Proxmox API authentication.
                    - "ssl_verification" (bool): Whether to verify SSL certificates (default is True).
                    - "timeout" (int): The timeout duration for API requests.

        Returns:
            proxmoxer.ProxmoxAPI: An authenticated ProxmoxAPI object.

        Raises:
            proxmoxer.backends.https.AuthenticationError: If authentication fails.
            requests.exceptions.ConnectTimeout: If the connection to the Proxmox API times out.
            requests.exceptions.SSLError: If SSL certificate validation fails.
            requests.exceptions.ConnectionError: If the connection to the Proxmox API is refused.
        """
        logger.debug("Starting: api_connect.")
        # Get a valid Proxmox API endpoint
        proxmox_api_endpoint = self.api_connect_get_hosts(proxlb_config.get("proxmox_api", {}).get("hosts", []))

        # Disable warnings for SSL certificate validation
        if not proxlb_config.get("proxmox_api").get("ssl_verification", True):
            logger.warning(f"SSL certificate validation to host {proxmox_api_endpoint} is deactivated.")
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
            requests.packages.urllib3.disable_warnings()

        # Login into Proxmox API and create API object
        try:
            proxmox_api = proxmoxer.ProxmoxAPI(
                proxmox_api_endpoint,
                user=proxlb_config.get("proxmox_api").get("user", True),
                password=proxlb_config.get("proxmox_api").get("pass", True),
                verify_ssl=proxlb_config.get("proxmox_api").get("ssl_verification", True),
                timeout=proxlb_config.get("proxmox_api").get("timeout", True))
        except proxmoxer.backends.https.AuthenticationError as proxmox_api_error:
            logger.critical(f"Authentication failed. Please check the defined credentials: {proxmox_api_error}")
            sys.exit(2)
        except requests.exceptions.ConnectTimeout:
            logger.critical(f"Connection timeout to host {proxmox_api_endpoint}")
            sys.exit(2)
        except requests.exceptions.SSLError as proxmox_api_error:
            logger.critical(f"SSL certificate validation failed: {proxmox_api_error}")
            sys.exit(2)
        except requests.exceptions.ConnectionError:
            logger.critical(f"Connection refused by host {proxmox_api_endpoint}")
            sys.exit(2)

        logger.info(f"API connection to host {proxmox_api_endpoint} succeeded.")

        logger.debug("Finished: api_connect.")
        return proxmox_api
