## Table of Contents

1. [GUI Integration](#gui-integration)
    - [How to install pve-proxmoxlb-service-ui package](https://github.com/gyptazy/ProxLB/issues/44)
2. [Proxmox HA Integration](#proxmox-ha-integration)
    - [Host groups: Honour HA groups](https://github.com/gyptazy/ProxLB/issues/65)

### GUI Integration
<img align="left" src="https://cdn.gyptazy.com/images/proxlb-GUI-integration.jpg"/> ProxLB can also be accessed through the Proxmox Web UI by installing the optional `pve-proxmoxlb-service-ui` package, which depends on the proxlb package. For full Web UI integration, this package must be installed on all nodes within the cluster. Once installed, a new menu item - `Rebalancing`, appears in the cluster level under the HA section. Once installed, it offers two key functionalities:
* Rebalancing VM workloads
* Migrate VM workloads away from a defined node (e.g. maintenance preparation)

**Note:** This package is currently discontinued and will be readded at a later time. See also: [#44: How to install pve-proxmoxlb-service-ui package](https://github.com/gyptazy/ProxLB/issues/44).

### Proxmox HA Integration
Proxmox HA (High Availability) groups are designed to ensure that virtual machines (VMs) remain running within a Proxmox cluster. HA groups define specific rules for where VMs should be started or migrated in case of node failures, ensuring minimal downtime and automatic recovery.

However, when used in conjunction with ProxLB, the built-in load balancer for Proxmox, conflicts can arise. ProxLB operates with its own logic for workload distribution, taking into account affinity and anti-affinity rules. While it effectively balances guest workloads, it may re-shift and redistribute VMs in a way that does not align with HA group constraints, potentially leading to unsuitable placements.

Due to these conflicts, it is currently not recommended to use both HA groups and ProxLB simultaneously. The interaction between the two mechanisms can lead to unexpected behavior, where VMs might not adhere to HA group rules after being moved by ProxLB.

A solution to improve compatibility between HA groups and ProxLB is under evaluation, aiming to ensure that both features can work together without disrupting VM placement strategies.

See also: [#65: Host groups: Honour HA groups](https://github.com/gyptazy/ProxLB/issues/65).