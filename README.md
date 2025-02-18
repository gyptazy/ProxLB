# ProxLB - (Re)Balance VM Workloads in Proxmox Clusters
<img align="left" src="https://cdn.gyptazy.com/images/Prox-LB-logo.jpg"/>
<br>

<p float="center"><img src="https://img.shields.io/github/license/gyptazy/ProxLB"/><img src="https://img.shields.io/github/contributors/gyptazy/ProxLB"/><img src="https://img.shields.io/github/last-commit/gyptazy/ProxLB/main"/><img src="https://img.shields.io/github/issues-raw/gyptazy/ProxLB"/><img src="https://img.shields.io/github/issues-pr/gyptazy/ProxLB"/></p>


## Table of Contents



## Introduction
ProxLB is an advanced load balancing solution specifically designed for Proxmox clusters, addressing the absence of a Dynamic Resource Scheduler (DRS) that is familiar to VMware users. As a third-party solution, ProxLB enhances the management and efficiency of Proxmox clusters by intelligently distributing workloads across available nodes. Workloads can be balanced by different times like the guest's memory, CPU or disk usage or their assignment to avoid overprovisioning and ensuring resources.

One of the key advantages of ProxLB is that it is fully open-source and free, making it accessible for anyone to use, modify, and contribute to. This ensures transparency and fosters community-driven improvements. ProxLB supports filtering and ignoring specific nodes and guests through configuration files and API calls, providing administrators with the flexibility to tailor the load balancing behavior to their specific needs.

A standout feature of ProxLB is its maintenance mode. When enabled, all guest workloads are automatically moved to other nodes within the cluster, ensuring that a node can be safely updated, rebooted, or undergo hardware maintenance without disrupting the overall cluster operation. Additionally, ProxLB supports both affinity and anti-affinity rules, allowing operators to group multiple guests to run together on the same node or ensure that certain guests do not run on the same node, depending on the cluster's node count. This feature is crucial for optimizing performance and maintaining high availability.

ProxLB can also return the best next node for guest placement, which can be integrated into CI/CD pipelines using tools like Ansible or Terraform. This capability streamlines the deployment process and ensures efficient resource utilization. Furthermore, ProxLB leverages the Proxmox API, including the entire ACL (Access Control List) system, for secure and efficient operation. Unlike some solutions, it does not require SSH access, enhancing security and simplifying configuration.

Overall, ProxLB significantly enhances resource management by intelligently distributing workloads, reducing downtime through its maintenance mode, and providing improved flexibility with affinity and anti-affinity rules. Its seamless integration with CI/CD tools and reliance on the Proxmox API make it a robust and secure solution for optimizing Proxmox cluster performance.

### Video of Migration
<img src="https://cdn.gyptazy.com/images/proxlb-rebalancing-demo.gif"/>

## Features
* Rebalance VMs/CTs in the cluster by:
  * Memory
  * Disk (only local storage)
  * CPU
* Get best nodes for further automation
* Supported Guest Types
  * VMs
  * CTs
  * Both
* Maintenance Mode
  * Set node(s) into maintenance
  * Move all workloads to different nodes
* Filter
  * Exclude nodes
  * Exclude virtual machines
* Affinity / Anti-Affinity Rules
* Dry-run support
  * Human readable output in CLI
  * JSON output for further parsing
* Fully based on Proxmox API
  * Fully integrated into the Proxmox ACL
  * No SSH required
* Usage
  * One-Time
  * Daemon
  * Proxmox Web GUI Integration