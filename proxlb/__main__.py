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
import signal

from proxlb_solver import shadow as _solver_shadow
from proxlb_solver.models import MigrationPlan

from proxlb.utils.logger import SystemdLogger
from proxlb.utils.cli_parser import CliParser
from proxlb.utils.config_parser import ConfigParser
from proxlb.utils.proxmox_api import ProxmoxApi
from proxlb.models.nodes import Nodes
from proxlb.models.features import Features
from proxlb.models.guests import Guests
from proxlb.models.groups import Groups
from proxlb.models.calculations import Calculations
from proxlb.models.balancing import Balancing
from proxlb.models.pools import Pools
from proxlb.models.ha_rules import HaRules
from proxlb.models.ha_status import HaStatus
from proxlb.utils.helper import Helper
from proxlb.utils.proxlb_data import ProxLbData


"""
ProxLB main function
"""
# Initialize logging handler
logger = SystemdLogger(level=logging.INFO)

# Initialize handlers
signal.signal(signal.SIGHUP, Helper.handler_sighup)
signal.signal(signal.SIGINT, Helper.handler_sigint)

# Parses arguments passed from the CLI
cli_parser = CliParser()
cli_args = cli_parser.parse_args()
Helper.get_version(cli_args.version)

# Parse ProxLB config file
config_parser = ConfigParser(cli_args.config)
proxlb_config = config_parser.get_config()

# Update log level from config and fallback to INFO if not defined
logger.set_log_level(proxlb_config.service.log_level)

# Validate of an optional service delay
Helper.get_service_delay(proxlb_config)

# Connect to Proxmox API & create API object
proxmox_api = ProxmoxApi(proxlb_config)

# Overwrite password after creating the API object
proxlb_config.proxmox_api.password = "********"
proxlb_config.proxmox_api.token_secret = "********"


def reinstall_sigint() -> None:
    """
    There is a quirk in context of PID 1 execution,
    e.g. as a container entrypoint. The handler is not
    triggered any more, even though it is still registered.
    It only happens with solver invocations.
    """
    signal.signal(
        signal.SIGINT,
        signal.getsignal(signal.SIGINT),
    )


while True:

    # Validate if HA mode is enabled and if this node is the HA manager.
    if proxlb_config.service.enable_ha:
        if not HaStatus.is_node_ha_manager(proxmox_api):
            logger.info("This node is not the HA manager. Waiting for next run.")
            Helper.get_daemon_mode(proxlb_config)
            continue
        else:
            logger.debug("This node is the HA manager. Continuing.")

    # Validate if reload signal was sent during runtime
    # and reload the ProxLB configuration and adjust log level
    if Helper.proxlb_reload:
        logger.info("Reloading ProxLB configuration.")
        proxlb_config = config_parser.get_config()
        logger.set_log_level(proxlb_config.service.log_level)
        Helper.proxlb_reload = False

    # Get all required objects from the Proxmox cluster
    Helper.apply_maintenance_nodes_schedule(proxlb_config)
    nodes = Nodes.get_nodes(proxmox_api, proxlb_config)
    meta = Features.validate_any_non_pve9_node(proxlb_config, nodes)
    pools = Pools.get_pools(proxmox_api)
    ha_rules = HaRules.get_ha_rules(proxmox_api, meta)
    guests = Guests.get_guests(proxmox_api, pools, ha_rules, nodes, proxlb_config)
    groups = Groups.get_groups(guests, nodes)

    # Merge obtained objects from the Proxmox cluster for further usage
    proxlb_data = ProxLbData(
        meta=meta,
        nodes=nodes,
        guests=guests,
        pools=pools,
        ha_rules=ha_rules,
        groups=groups,
    )
    Helper.log_node_metrics(proxlb_data)

    # Validate usable features by PVE versions
    Features.validate_available_features(proxlb_data)

    # Update the initial node resource assignments
    # by the previously created groups.
    Calculations.set_node_assignments(proxlb_data)
    Helper.log_node_metrics(proxlb_data, init=False)
    Calculations.set_node_hot(proxlb_data)
    Calculations.set_guest_hot(proxlb_data)
    target = Calculations.get_most_free_node(proxlb_data, cli_args.best_node)
    if target is None:
        logger.warning("No suitable target node found for balancing. Skipping this run.")
    else:
        Calculations.validate_affinity_map(proxlb_data)
        Calculations.relocate_guests_on_maintenance_nodes(proxlb_data)
        Calculations.get_balanciness(proxlb_data)
        Calculations.relocate_guests(proxlb_data)

        # CP-SAT solver (optional) — shadow (read-only) or active mode.
        _solver_cfg = proxlb_config.solver
        _run_file: str | None = None
        _solver_plan: MigrationPlan | None = None
        if _solver_cfg.enable:
            _run_file, _solver_plan = _solver_shadow.run_shadow(
                proxlb_data, _solver_cfg
            )
            reinstall_sigint()

        Helper.log_node_metrics(proxlb_data, init=False)

        # Perform balancing actions via Proxmox API
        if proxlb_data.meta.balancing.enable:
            if not cli_args.dry_run:
                if (_solver_cfg.enable
                        and _solver_cfg.mode == "active"):
                    if _solver_plan is not None:
                        try:
                            _solver_shadow.execute_solver_plan(
                                proxmox_api, proxlb_data,
                                _solver_plan, _solver_cfg, _run_file
                            )
                        except Exception as exc:
                            if _solver_cfg.fallback_to_greedy:
                                logger.warning(
                                    f"[solver] active execution failed, "
                                    f"falling back to ProxLB plan: {exc}")
                                Balancing.balance(proxmox_api, proxlb_data)
                            else:
                                logger.warning(
                                    f"[solver] active execution failed, "
                                    f"skipping greedy fallback "
                                    f"(fallback_to_greedy=False): {exc}")
                    elif _solver_cfg.fallback_to_greedy:
                        Balancing.balance(proxmox_api, proxlb_data)
                    else:
                        logger.warning(
                            "[solver] active: no feasible solver plan; "
                            "skipping greedy fallback "
                            "(fallback_to_greedy=False)")
                else:
                    Balancing.balance(proxmox_api, proxlb_data)
                reinstall_sigint()

        # Record whether balancing was executed or skipped (dry-run).
        if _run_file is not None:
            try:
                _solver_shadow.finalize_run(_run_file, dry_run=cli_args.dry_run)
            except Exception as exc:
                logger.warning(f"[solver] finalize_run failed: {exc}")
            reinstall_sigint()

    # Validate if the JSON output should be
    # printed to stdout
    Helper.print_json(proxlb_data, cli_args.json)
    # Validate daemon mode
    Helper.get_daemon_mode(proxlb_config)
    logger.debug("Finished: __main__")
