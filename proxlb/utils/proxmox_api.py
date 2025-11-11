"""
    The proxmox_api class manages connections to the Proxmox API by parsing the required objects
    for the authentication which can be based on username/password or API tokens.

    This class provides methods to initialize the Proxmox API connection, test connectivity to
    Proxmox hosts, and handle authentication using either username/password or API tokens.
    It also includes functionality to distribute load across multiple Proxmox API endpoints
    and manage SSL certificate validation.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import errno
try:
    import proxmoxer
    PROXMOXER_PRESENT = True
except ImportError:
    PROXMOXER_PRESENT = False
import random
import socket
try:
    import requests
    REQUESTS_PRESENT = True
except ImportError:
    REQUESTS_PRESENT = False
import sys
import time
try:
    import urllib3
    URLLIB3_PRESENT = True
except ImportError:
    URLLIB3_PRESENT = False
from typing import Dict, Any
from utils.helper import Helper
from utils.logger import SystemdLogger


if not PROXMOXER_PRESENT:
    print("Error: The required library 'proxmoxer' is not installed.")
    sys.exit(1)

if not URLLIB3_PRESENT:
    print("Error: The required library 'urllib3' is not installed.")
    sys.exit(1)

if not REQUESTS_PRESENT:
    print("Error: The required library 'requests' is not installed.")
    sys.exit(1)


logger = SystemdLogger()


class ProxmoxApi:
    """
    The proxmox_api class manages connections to the Proxmox API by parsing the required objects
    for the authentication which can be based on username/password or API tokens.

    This class provides methods to initialize the Proxmox API connection, test connectivity to
    Proxmox hosts, and handle authentication using either username/password or API tokens.
    It also includes functionality to distribute load across multiple Proxmox API endpoints
    and manage SSL certificate validation.

    Attributes:
        logger (SystemdLogger): Logger instance for logging messages.
        proxmox_api (proxmoxer.ProxmoxAPI): Authenticated ProxmoxAPI object.

    Methods:
        __init__(proxlb_config: Dict[str, Any]) -> None:
            Initializes the ProxmoxApi instance with the provided configuration.
        __getattr__(name):
            Delegates attribute access to the proxmox_api object.
        api_connect_get_hosts(proxmox_api_endpoints: list) -> str:
            Determines a working Proxmox API host from a list of endpoints.
        test_api_proxmox_host(host: str) -> str:
            Tests connectivity to a Proxmox host by resolving its IP address.
        test_api_proxmox_host_ipv4(host: str, port: int = 8006, timeout: int = 1) -> bool:
            Tests reachability of a Proxmox host on its IPv4 address.
        test_api_proxmox_host_ipv6(host: str, port: int = 8006, timeout: int = 1) -> bool:
            Tests reachability of a Proxmox host on its IPv6 address.
        api_connect(proxlb_config: Dict[str, Any]) -> proxmoxer.ProxmoxAPI:
            Establishes a connection to the Proxmox API using the provided configuration.
    """
    def __init__(self, proxlb_config: Dict[str, Any]) -> None:
        """
        Initializes the ProxmoxApi instance with the provided configuration.

        This constructor method sets up the Proxmox API connection by calling the
        api_connect method with the given configuration dictionary. It logs the
        initialization process for debugging purposes.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the Proxmox API configuration.
        """
        logger.debug("Starting: ProxmoxApi initialization.")
        self.proxmox_api = self.api_connect(proxlb_config)
        self.test_api_user_permissions(self.proxmox_api)
        logger.debug("Finished: ProxmoxApi initialization.")

    def __getattr__(self, name):
        """
        Delegate attribute access to proxmox_api to the underlying proxmoxer module.
        """
        return getattr(self.proxmox_api, name)

    def validate_config(self, proxlb_config: Dict[str, Any]) -> None:
        """
        Validates the provided ProxLB configuration dictionary to ensure that it contains
        the necessary credentials for authentication and that the credentials are not
        mutually exclusive.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.
                It must include a "proxmox_api" key with a nested dictionary that contains
                either "user" and "password" keys for username/password authentication or
                "token_id" and "token_secret" keys for API token authentication.

        Raises:
            SystemExit: If both pass/token_secret and API token authentication methods are
                        provided, the function will log a critical error message and terminate
                        the program.

        Logs:
            Logs the start and end of the validation process. Logs a critical error if both
            authentication methods are provided.
        """
        logger.debug("Starting: validate_config.")
        if not proxlb_config.get("proxmox_api", False):
            logger.critical(f"Config error. Please check your proxmox_api chapter in your config file.")
            print(f"Config error. Please check your proxmox_api chapter in your config file.")
            sys.exit(1)

        proxlb_credentials = proxlb_config["proxmox_api"]
        present_auth_pass = "pass" in proxlb_credentials
        present_auth_secret = "token_secret" in proxlb_credentials
        token_id = proxlb_credentials.get("token_id", None)

        if token_id:
            non_allowed_chars = ["@", "!"]
            for char in non_allowed_chars:
                if char in token_id:
                    logger.error(f"Wrong user/token format defined. User and token id must be splitted! Please see: https://github.com/gyptazy/ProxLB/blob/main/docs/03_configuration.md#required-permissions-for-a-user")
                    sys.exit(1)

        if present_auth_pass and present_auth_secret:
            logger.critical(f"Username/password and API token authentication are mutal exclusive. Please use only one!")
            print(f"Username/password and API token authentication are mutal exclusive. Please use only one!")
            sys.exit(1)

        logger.debug("Finished: validate_config.")

    def api_connect_get_hosts(self, proxlb_config, proxmox_api_endpoints: list) -> str:
        """
        Perform a connectivity test to determine a working host for the Proxmox API.

        This method takes a list of Proxmox API endpoints and validates their connectivity.
        It returns a working host from the list. If only one endpoint is provided, it is
        returned immediately. If multiple endpoints are provided, each one is tested for
        connectivity. If a valid host is found, it is returned. If multiple valid hosts
        are found, one is chosen at random to distribute the load across the cluster.

        Args:
            proxlb_config (Dict[str, Any]): A dictionary containing the ProxLB configuration.
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
            logger.critical("The proxmox_api hosts are not defined as a list type.")
            sys.exit(1)
        if not proxmox_api_endpoints:
            logger.critical("No proxmox_api hosts are defined.")
            sys.exit(1)

        validated_api_hosts: list[tuple[str, int]] = []

        for host in proxmox_api_endpoints:
            retries = proxlb_config["proxmox_api"].get("retries", 1)
            wait_time = proxlb_config["proxmox_api"].get("wait_time", 1)

            for attempt in range(retries):
                candidate_host, candidate_port = self.test_api_proxmox_host(host)
                if candidate_host:
                    validated_api_hosts.append((candidate_host, candidate_port))
                    break
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}/{retries} failed for host {host}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)

        if validated_api_hosts:
            chosen_host, chosen_port = random.choice(validated_api_hosts)
            return chosen_host, chosen_port

        logger.critical("No valid Proxmox API hosts found.")
        print("No valid Proxmox API hosts found.")
        logger.debug("Finished: api_connect_get_hosts.")
        sys.exit(1)

    def test_api_proxmox_host(self, host: str) -> tuple[str, int | None, None]:
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

        # Validate for custom port configurations (e.g., by given external
        # loadbalancer systems)
        host, port = Helper.get_host_port_from_string(host)
        if port is None:
            port = 8006

        # Try resolving DNS to IP and log non-resolvable ones
        try:
            infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC)
        except socket.gaierror:
            logger.warning(f"Could not resolve {host}.")
            return (None, None)

        # Check both families that are actually present
        saw_family = set()
        for family, *_rest in infos:
            saw_family.add(family)

        if socket.AF_INET in saw_family:
            logger.debug(f"{host} has IPv4.")
            if self.test_api_proxmox_host_ipv4(host, port):
                return (host, port)

        if socket.AF_INET6 in saw_family:
            logger.debug(f"{host} has IPv6.")
            if self.test_api_proxmox_host_ipv6(host, port):
                return (host, port)

        logger.debug("Finished: test_api_proxmox_host (unreachable).")
        return (None, None)

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
        ok, rc = Helper.tcp_connect_test(socket.AF_INET, host, port, timeout)
        if ok:
            logger.debug(f"Host {host} is reachable on IPv4 for tcp/{port}.")
            logger.debug("Finished: test_api_proxmox_host_ipv4.")
            return True

        if rc == errno.ETIMEDOUT:
            logger.warning(f"Timeout connecting to {host} on IPv4 tcp/{port}.")
        else:
            logger.warning(f"Host {host} is unreachable on IPv4 for tcp/{port} (errno {rc}).")

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
        ok, rc = Helper.tcp_connect_test(socket.AF_INET6, host, port, timeout)
        if ok:
            logger.debug(f"Host {host} is reachable on IPv6 for tcp/{port}.")
            logger.debug("Finished: test_api_proxmox_host_ipv6.")
            return True

        if rc == errno.ETIMEDOUT:
            logger.warning(f"Timeout connecting to {host} on IPv6 tcp/{port}.")
        else:
            logger.warning(f"Host {host} is unreachable on IPv6 for tcp/{port} (errno {rc}).")

        logger.debug("Finished: test_api_proxmox_host_ipv6.")
        return False

    def test_api_user_permissions(self, proxmox_api: any):
        """
        Test the permissions of the current user/token used for the Proxmox API.

        This method gets all assigned permissions for all API paths for the current
        used user/token and validates them against the minimum required permissions.

        Args:
            proxmox_api (any): The Proxmox API client instance.
        """
        logger.debug("Starting: test_api_user_permissions.")
        permissions_required = ["Datastore.Audit", "Sys.Audit", "VM.Audit", "VM.Migrate"]
        permissions_available = []

        # Get the permissions for the current user/token from API
        try:
            permissions = proxmox_api.access.permissions.get()
        except proxmoxer.core.ResourceException as api_error:
            if "no such user" in str(api_error):
                logger.error("Authentication to Proxmox API not possible: User not known - please check your username and config file.")
                sys.exit(1)
            else:
                logger.error(f"Proxmox API error: {api_error}")
                sys.exit(1)

        # Get all available permissions of the current user/token
        for path, permission in permissions.items():
            for permission in permissions[path]:
                permissions_available.append(permission)

        # Validate if all required permissions are included within the available permissions
        for required_permission in permissions_required:
            if required_permission not in permissions_available:
                logger.critical(f"Permission '{required_permission}' is missing. Please adjust the permissions for your user/token. See also: https://github.com/gyptazy/ProxLB/blob/main/docs/03_configuration.md#required-permissions-for-a-user")
                sys.exit(1)

        logger.debug("Finished: test_api_user_permissions.")

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
        # Validate config
        self.validate_config(proxlb_config)

        # Get a valid Proxmox API endpoint
        proxmox_api_endpoint, proxmox_api_port = self.api_connect_get_hosts(proxlb_config, proxlb_config.get("proxmox_api", {}).get("hosts", []))

        # Disable warnings for SSL certificate validation
        if not proxlb_config.get("proxmox_api").get("ssl_verification", True):
            logger.warning(f"SSL certificate validation to host {proxmox_api_endpoint} is deactivated.")
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
            requests.packages.urllib3.disable_warnings()

        # Login into Proxmox API and create API object
        try:

            if proxlb_config.get("proxmox_api").get("token_secret", False):
                proxmox_api = proxmoxer.ProxmoxAPI(
                    proxmox_api_endpoint,
                    port=proxmox_api_port,
                    user=proxlb_config.get("proxmox_api").get("user", True),
                    token_name=proxlb_config.get("proxmox_api").get("token_id", True),
                    token_value=proxlb_config.get("proxmox_api").get("token_secret", True),
                    verify_ssl=proxlb_config.get("proxmox_api").get("ssl_verification", True),
                    timeout=proxlb_config.get("proxmox_api").get("timeout", True))
                logger.debug("Using API token authentication.")
            else:
                proxmox_api = proxmoxer.ProxmoxAPI(
                    proxmox_api_endpoint,
                    port=proxmox_api_port,
                    user=proxlb_config.get("proxmox_api").get("user", True),
                    password=proxlb_config.get("proxmox_api").get("pass", True),
                    verify_ssl=proxlb_config.get("proxmox_api").get("ssl_verification", True),
                    timeout=proxlb_config.get("proxmox_api").get("timeout", True))
                logger.debug("Using username/password authentication.")
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
