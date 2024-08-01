# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.0] - 2024-08-01

### Added

- Add feature to prevent VMs from being relocated by defining a wildcard pattern. [#7]
- Add feature to make log verbosity configurable [#17].
- Add option_mode to rebalance by node's free resources in percent (instead of bytes). [#29]
- Add option to rebalance by assigned VM resources to avoid over provisioning. [#16]
- Add Docker/Podman support. [#10 by @daanbosch]
- Add exclude grouping feature to rebalance VMs from being located together to new nodes. [#4]
- Add feature to prevent VMs from being relocated by defining the 'plb_ignore_vm' tag. [#7]
- Add dry-run support to see what kind of rebalancing would be done. [#6]
- Add LXC/Container integration. [#27]
- Add include grouping feature to rebalance VMs bundled to new nodes. [#3]

### Changed

- Adjusted general logging and log more details.


## [0.9.9] - 2024-07-06

### Added

- Initial public development release of ProxLB.


## [0.9.0] - 2024-02-01

### Added

- Development release of ProxLB.