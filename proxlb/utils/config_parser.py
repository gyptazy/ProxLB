"""
The ConfigParser class handles the parsing of configuration file
from a given YAML file from any location.
"""

__author__ = "Florian Paul Azim Hoberg <gyptazy>"
__copyright__ = "Copyright (C) 2025 Florian Paul Azim Hoberg (@gyptazy)"
__license__ = "GPL-3.0"


import os
import sys
try:
    import yaml
    PYYAML_PRESENT = True
except ImportError:
    PYYAML_PRESENT = False
from enum import StrEnum
from typing import Any, Optional, assert_never
from pydantic import BaseModel, Field, PrivateAttr, ValidationError
from pathlib import Path
from proxlb.utils.logger import SystemdLogger


if not PYYAML_PRESENT:
    print("Error: The required library 'pyyaml' is not installed.")
    sys.exit(1)

import yaml  # noqa: F811 # keep for pyright

logger = SystemdLogger()


class TimeFormat(StrEnum):
    Hours = "hours"
    Minutes = "minutes"


class Config(BaseModel):

    class AffinityType(StrEnum):
        PositiveAffinity = "affinity"
        NegativeAffinity = "anti-affinity"

    class GuestType(StrEnum):
        Vm = "vm"
        Ct = "ct"

    class ProxmoxAPI(BaseModel):
        hosts: list[str]
        password: Optional[str] = Field(alias="pass", default=None)
        retries: int = 1
        ssl_verification: bool = True
        timeout: int = 1
        token_id: Optional[str] = None
        token_secret: Optional[str] = None
        username: str = Field(alias="user")
        wait_time: int = 1

    class ProxmoxCluster(BaseModel):
        class MaintenanceNodesSchedule(BaseModel):
            duration: int = Field(default=0, ge=0)
            pre_migration: int = Field(default=0, alias="pre-migration", ge=0)
            schedules: dict[str, list[str]] = Field(default_factory=dict)

        _maintenance_nodes_static: list[str] = PrivateAttr(default_factory=list)

        ignore_nodes: list[str] = []
        maintenance_nodes: list[str] = []
        maintenance_nodes_schedule: MaintenanceNodesSchedule = Field(default_factory=MaintenanceNodesSchedule)
        overprovisioning: bool = False

        def model_post_init(self, __context: Any) -> None:
            self._maintenance_nodes_static = list(dict.fromkeys(self.maintenance_nodes))

        def static_maintenance_nodes(self) -> list[str]:
            return list(self._maintenance_nodes_static)

    class Balancing(BaseModel):
        class Resource(StrEnum):
            Cpu = "cpu"
            Disk = "disk"
            Memory = "memory"

        class Mode(StrEnum):
            Assigned = "assigned"
            Psi = "psi"
            Used = "used"

        class Psi(BaseModel):
            class Pressure(BaseModel):
                pressure_full: float
                pressure_some: float
                pressure_spikes: float
            guests: dict["Config.Balancing.Resource", Pressure]
            nodes: dict["Config.Balancing.Resource", Pressure]

        class Pool(BaseModel):
            pin: Optional[list[str]] = None
            strict: bool = True
            type: Optional["Config.AffinityType"] = None

        balance_larger_guests_first: bool = False
        balance_types: list["Config.GuestType"] = []
        balanciness: int = 10
        cpu_overcommit: float = 2.0
        cpu_threshold: Optional[int] = None
        enable: bool = False
        enforce_affinity: bool = False
        enforce_pinning: bool = False
        live: bool = True
        max_job_validation: int = 1800
        max_node_inflow: Optional[int] = 1
        memory_threshold: Optional[int] = None
        disk_threshold: Optional[int] = None
        method: "Config.Balancing.Resource" = Resource.Memory
        mode: Mode = Mode.Used
        node_resource_reserve: Optional[dict[str, dict["Config.Balancing.Resource", int]]] = None
        parallel: bool = False
        parallel_jobs: int = 5
        pools: Optional[dict[str, Pool]] = None
        psi: Optional[Psi] = None
        with_conntrack_state: bool = True
        with_local_disks: bool = True

        def threshold(self, method: "Config.Balancing.Resource") -> Optional[int]:
            if method == self.Resource.Cpu:
                return self.cpu_threshold
            elif method == self.Resource.Disk:
                return self.disk_threshold
            elif method == self.Resource.Memory:
                return self.memory_threshold
            else:
                assert_never(method)

    class Service(BaseModel):

        class LogLevel(StrEnum):
            CRITICAL = "CRITICAL"
            DEBUG = "DEBUG"
            ERROR = "ERROR"
            INFO = "INFO"
            WARNING = "WARNING"

        class Delay(BaseModel):
            enable: bool = False
            format: TimeFormat = TimeFormat.Hours
            time: int = 1

            @property
            def seconds(self) -> int:
                return self.time * 3600 if self.format == TimeFormat.Hours else self.time * 60

            def __str__(self) -> str:
                return f"{self.time} {self.format}"

        class Schedule(BaseModel):
            format: TimeFormat = TimeFormat.Hours
            interval: int = 12

            @property
            def seconds(self) -> int:
                return self.interval * 3600 if self.format == TimeFormat.Hours else self.interval * 60

            def __str__(self) -> str:
                return f"{self.interval} {self.format}"

        daemon: bool = True
        enable_ha: bool = False
        delay: Delay = Delay()
        log_level: "Config.Service.LogLevel" = LogLevel.INFO
        schedule: Schedule = Schedule()

    class Solver(BaseModel):
        class Mode(StrEnum):
            Active = "active"
            Shadow = "shadow"

        active_step_retries: int = 3
        enable: bool = False
        fallback_to_greedy: bool = True
        log_dir: str = "/var/log/proxlb/solver"
        mode: Mode = Mode.Shadow
        timeout_seconds: float = 30.0
        use_reservations: bool = True

    proxmox_api: ProxmoxAPI
    proxmox_cluster: ProxmoxCluster = ProxmoxCluster()
    balancing: Balancing = Field(default_factory=Balancing)
    service: Service = Field(default_factory=Service)
    solver: Solver = Field(default_factory=Solver)


class ConfigParser:
    """
    The ConfigParser class handles the parsing of a configuration file.

    Methods:
    __init__(config_path: str)

    test_config_path(config_path: Path) -> None
        Checks if the configuration file is present at the given config path.

    get_config() -> Dict[str, Any]
        Parses and returns the configuration data from the YAML file.
    """
    def __init__(self, config_path: Path):
        """
        Initializes the configuration file parser and validates the config file.
        """
        logger.debug("Starting: ConfigParser.")
        self.config_path = self.test_config_path(config_path)
        logger.debug("Finished: ConfigParser.")

    def test_config_path(self, config_path: Path) -> Path:
        """
        Checks if configuration file is present at given config path.
        """
        logger.debug("Starting: test_config_path.")

        if os.path.exists(config_path):
            logger.debug(f"The file {config_path} exists.")
        else:
            print(f"The config file {config_path} does not exist.")
            logger.critical(f"The config file {config_path} does not exist.")
            sys.exit(1)

        logger.debug("Finished: test_config_path.")
        return config_path

    def get_config(self) -> Config:
        """
        Parses and returns CLI arguments.
        """
        logger.debug("Starting: get_config.")
        logger.info(f"Using config path: {self.config_path}")

        try:
            with self.config_path.open(encoding="utf-8") as config_file:
                return Config(**yaml.load(config_file, Loader=yaml.FullLoader))
        except yaml.YAMLError as exception_error:
            msg = f"Error loading YAML file: {exception_error}"
            print(msg)
            logger.critical(msg)
            sys.exit(1)
        except (TypeError, ValidationError) as exception_error:
            msg = f"Error parsing {self.config_path}: {exception_error}"
            print(msg)
            logger.critical(msg)
            sys.exit(1)
