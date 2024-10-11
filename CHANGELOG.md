# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.4] - 2024-10-11

### Added

- Add feature to make API timeout configureable. [#91]
- Add maintenance mode to evacuate a node and move workloads for other nodes in the cluster. [#58]
- Add version output cli arg. [#89]

### Changed

- Run storage balancing only on supported shared storages. [#79]
- Run storage balancing only when needed to save time. [#79]

### Fixed

- Fix CPU balancing where calculations are done in float instead of int. (by @glitchvern) [#75]
- Fix documentation for the underlying infrastructure. [#81]


## [1.0.3] - 2024-09-12

### Added

- Add storage balancing function. [#51]
- Add a convert function to cast all bool alike options from configparser to bools. [#53]
- Add a config parser options for future features. [#53]
- Add a config versio schema that must be supported by ProxLB. [#53]
- Add doc how to add dedicated user for authentication. (by @Dulux-Oz)
- Add feature to allow the API hosts being provided as a comma separated list. [#60]
- Add cli arg `-b` to return the next best node for next VM/CT placement. [#8]

### Changed

- Improve the underlying code base for future implementations. [#53]
- Provide a more reasonable output when HA services are not active in a Proxmox cluster. [#68]

### Fixed

- Fixed `master_only` function by inverting the condition.
- Improved the overall validation and error handling. [#64]
- Fix bug in the `proxlb.conf` in the vm_balancing section.
- Fix anti-affinity rules not evaluating a new and different node. [#67]
- Fix documentation for the master_only parameter placed in the wrong config section. [#74]
- Fix handling of unset `ignore_nodes` and `ignore_vms` resulted in an attribute error. [#71]


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

- Add option_mode to rebalance by node's free resources in percent (instead of bytes). [#29]
- Add LXC/Container integration. [#27]
- Add exclude grouping feature to rebalance VMs from being located together to new nodes. [#4]
- Add dry-run support to see what kind of rebalancing would be done. [#6]
- Add Docker/Podman support. [#10 by @daanbosch]
- Add feature to prevent VMs from being relocated by defining a wildcard pattern. [#7]
- Add feature to prevent VMs from being relocated by defining the 'plb_ignore_vm' tag. [#7]
- Add include grouping feature to rebalance VMs bundled to new nodes. [#3]
- Add option to rebalance by assigned VM resources to avoid overprovisioning. [#16]
- Add feature to make log verbosity configurable [#17].

### Changed

- Adjusted general logging and log more details.


## [0.9.9] - 2024-07-06

### Added

- Initial public development release of ProxLB.


## [0.9.0] - 2024-02-01

### Added

- Development release of ProxLB.
