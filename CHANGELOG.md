# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.1.6] - 2027-09-04

### Added

- Add validation for provided API user token id to avoid confusions (@gyptazy). [#291]

### Fixed

- Fix stacktrace output when validating permissions on non existing users in Proxmox (@gyptazy). [#291]
- Fix Overprovisioning first node if anti_affinity_group has only one member (@MiBUl-eu). [#295]
- Validate for node presence when pinning guests to avoid crashing (@gyptazy). [#296]
- Fix balancing evaluation of guest types (e.g., VM or CT) (@gyptazy). [#268]

## [1.1.5] - 2025-07-14

### Added

- Allow custom API ports instead of fixed tcp/8006 (@gyptazy). [#260]


## [1.1.4] - 2025-06-27

### Added

- Allow pinning of guests to a group of nodes (@gyptazy). [#245]

### Fixed

- Modified log levels to make output lighter at INFO level (@pmarasse) [#255]
- Fixed an issue where balancing was performed in combination of deactivated balancing and dry-run mode (@gyptazy). [#248]


## [1.1.3] - 2025-06-19

### Added

- Add relaod (SIGHUP) function to ProxLB to reload the configuration (by @gyptazy). [#189]
- Add optional wait time parameter to delay execution until the service takes action (by @gyptazy). [#239]
- Make the amount of parallel migrations configurable (by @gyptazy). [#241]

### Changed

- Use the average CPU consumption of a guest within the last 60 minutes instead of the current CPU usage (by @philslab-ninja & @gyptazy). [#94]

### Fixed

- Align maintenance mode with Proxmox HA maintenance mode (by @gyptazy). [#232]


## [1.1.2] - 2025-05-13

### Added

- Add a configurable retry mechanism when connecting to the Proxmox API (by @gyptazy) [#157]
- Add 1-to-1 relationships between guest and hypervisor node to ping a guest on a node (by @gyptazy) [#218]

### Fixed

- Force type cast cpu count of guests to int for some corner cases where a str got returned (by @gyptazy). [#222]
- Fix systemd unit file to run after network on non PVE nodes (by @robertdahlem) [#137]


## [1.1.1] - 2025-04-20

### Added

- Providing the API upstream error message when migration fails in debug mode (by @gyptazy) [#205]

### Changed

- Change the default behaviour of the daemon mode to active [#176]
- Change the default banalcing mode to used instead of assigned [#180]

### Fixed

- Set cpu_used to the cpu usage, which is a percent, times the total number of cores to get a number where guest cpu_used can be added to nodes cpu_used and be meaningful (by @glitchvern) [#195]
- Fix tag evluation for VMs for being ignored for further balancing [#163]
- Honor the value when balancing should not be performed and stop balancing [#174]
- allow the use of minutes instead of hours and only accept hours or minutes in the format (by @glitchvern) [#187]
- Remove hard coded memory usage from lowest usage node and use method and mode specified in configuration instead (by @glitchvern) [#197]
- Fix the guest type relationship in the logs when a migration job failed (by @gyptazy) [#204]
- Requery a guest if that running guest reports 0 cpu usage (by @glitchvern) [#200]
- Fix Python path for Docker entrypoint (by @crandler) [#170]
- Improve logging verbosity of messages that had a wrong servity [#165]


## [1.1.0] - 2025-04-01

### Fixed

- Refactored code base for ProxLB [#114]
- Switched to `pycodestyle` for linting [#114]
- Package building will be done within GitHub actions pipeline [#114]
- ProxLB now only returns a warning when no guests for further balancing are not present (instead of quitting) [132#]
- All nodes (according to the free resources) will be used now [#130]
- Fixed logging outputs where highest/lowest were mixed-up [#129]
- Stop balancing when movement would get worste (new force param to enfoce for affinity rules) [#128]
- Added requested documentation regarding Proxmox HA groups [#127]
- Rewrite of the whole affinity/anti-affinity rules evaluation and placement [#123]
- Fixed the `ignore` parameter for nodes where the node and guests on the node will be untouched [#102]


## [1.0.6] - 2024-12-24

### Fixed

- Fix maintenance mode when using cli arg and config mode by using the merged list (by @CartCaved). [#119]
- Fix that a scheduler time definition of 1 (int) gets wrongly interpreted as a bool (by @gyptazy). [#115]


## [1.0.5] - 2024-10-30

### Changed

- Change docs to make bool usage in configs more clear (by @gyptazy). [#104]

### Fixed

- Fix node (and its objects) evaluation when not reachable, e.g., maintenance (by @gyptazy). [#107]
- Fix migration from local disks (by @greenlogles). [#113]
- Fix evaluation of maintenance mode where comparing list & string resulted in a crash (by @glitchvern). [#106]
- Fix allowed values (add DEBUG, WARNING) for log verbosity (by @gyptazy). [#98]


## [1.0.4] - 2024-10-11

### Added

- Add maintenance mode to evacuate a node and move workloads for other nodes in the cluster. [#58]
- Add feature to make API timeout configureable. [#91]
- Add version output cli arg. [#89]

### Changed

- Run storage balancing only on supported shared storages. [#79]
- Run storage balancing only when needed to save time. [#79]

### Fixed

- Fix CPU balancing where calculations are done in float instead of int. (by @glitchvern) [#75]
- Fix documentation for the underlying infrastructure. [#81]


## [1.0.3] - 2024-09-12

### Added

- Add cli arg `-b` to return the next best node for next VM/CT placement. [#8]
- Add a convert function to cast all bool alike options from configparser to bools. [#53]
- Add a config parser options for future features. [#53]
- Add a config versio schema that must be supported by ProxLB. [#53]
- Add feature to allow the API hosts being provided as a comma separated list. [#60]
- Add doc how to add dedicated user for authentication. (by @Dulux-Oz)
- Add storage balancing function. [#51]

### Changed

- Provide a more reasonable output when HA services are not active in a Proxmox cluster. [#68]
- Improve the underlying code base for future implementations. [#53]

### Fixed

- Fix anti-affinity rules not evaluating a new and different node. [#67]
- Fixed `master_only` function by inverting the condition.
- Fix documentation for the master_only parameter placed in the wrong config section. [#74]
- Fix bug in the `proxlb.conf` in the vm_balancing section.
- Fix handling of unset `ignore_nodes` and `ignore_vms` resulted in an attribute error. [#71]
- Improved the overall validation and error handling. [#64]


## [1.0.2] - 2024-08-13

### Added

- Add option to run ProxLB only on the Proxmox's master node in the cluster (reg. HA feature). [#40]
- Add option to run migrations in parallel or sequentially. [#41]

### Changed

- Fix daemon timer to use hours instead of minutes. [#45]

### Fixed

- Fix CMake packaging for Debian package to avoid overwriting the config file. [#49]


## [1.0.0] - 2024-08-01

### Added

- Add feature to prevent VMs from being relocated by defining the 'plb_ignore_vm' tag. [#7]
- Add feature to prevent VMs from being relocated by defining a wildcard pattern. [#7]
- Add Docker/Podman support. [#10 by @daanbosch]
- Add option to rebalance by assigned VM resources to avoid overprovisioning. [#16]
- Add feature to make log verbosity configurable [#17].
- Add dry-run support to see what kind of rebalancing would be done. [#6]
- Add LXC/Container integration. [#27]
- Add exclude grouping feature to rebalance VMs from being located together to new nodes. [#4]
- Add include grouping feature to rebalance VMs bundled to new nodes. [#3]
- Add option_mode to rebalance by node's free resources in percent (instead of bytes). [#29]

### Changed

- Adjusted general logging and log more details.


## [0.9.9] - 2024-07-06

### Added

- Initial public development release of ProxLB.


## [0.9.0] - 2024-02-01

### Added

- Development release of ProxLB.
