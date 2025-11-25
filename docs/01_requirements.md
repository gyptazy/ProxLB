# Table of Contents

- [Requirements](#requirements)
- [Where To Run?](#where-to-run)

## Requirements
ProxLB is a sophisticated load balancer designed to enhance the management and distribution of workloads within a Proxmox cluster. By fully utilizing the Proxmox API, ProxLB eliminates the need for additional SSH access, streamlining cluster management while maintaining robust security. This chapter outlines the general requirements necessary to deploy and operate ProxLB effectively.

### Proxmox Cluster Requirements
To use ProxLB, you must have an existing Proxmox cluster consisting of at least two nodes. While traditional load balancers often struggle to manage minimal node configurations, ProxLB is optimized to provide efficient load distribution even in a two-node environment. The more nodes present in the cluster, the better ProxLB can optimize resource usage and manage workloads.

### ProxLB Package Requirements
Next to the previously mentioned requirements, ProxLB also requires you to fit the following ones:
* Python3.x
* proxmoxer
* requests
* urllib3
* pyyaml

### Seamless API Integration
ProxLB relies exclusively on the Proxmox API for all management tasks. This eliminates the need for direct SSH access, ensuring a cleaner and more secure interaction with the cluster. The API integration allows ProxLB to:

- Monitor cluster health and node resource utilization
- Migrate virtual machines (VMs) and containers as needed
- Manage storage utilization and distribution
- Implement load balancing policies

### Authentication and Security Standards
ProxLB fully supports Proxmox’s integrated user management system, providing robust authentication and access control. Key features include:

- **Multi-Factor Authentication (MFA):** Enhances security by requiring multiple verification methods.
- **API Key Support:** ProxLB can utilize API keys for authentication instead of traditional username/password combinations, minimizing exposure to credentials.
- **Role-Based Access Control (RBAC):** Ensures administrators have fine-grained control over user permissions.

### Flexible Storage Support
ProxLB offers versatile storage management options, supporting both local and shared storage types. It efficiently balances storage workloads across the cluster using the following storage systems:

- **Local Storage:** Direct-attached storage on each node.
- **Shared Storage:** Includes options like iSCSI, NVMeOF, and NFS for centralized storage solutions.
- **Ceph:** Integrated support for Ceph distributed storage, providing high availability and fault tolerance.

### Network Infrastructure Requirements
For optimal performance, ProxLB requires a reliable and high-speed network connection between the nodes in the cluster. Ensure that the network infrastructure meets the following criteria:

- **Low Latency:** Essential for real-time load balancing and VM migration.
- **Sufficient Bandwidth:** Adequate to handle storage access, data replication, and migration traffic.
- **Redundant Network Paths:** Recommended for increased fault tolerance and uptime.

### System Resource Allocation
ProxLB itself requires minimal system resources to operate. However, for managing larger clusters or high workloads, ensure the node running ProxLB has adequate resources available:

- **CPU:** A modern multi-core processor.
- **Memory:** At least 2 GB of RAM.
- **Storage:** Minimal disk space for configuration files and logs.


## Where To Run?
ProxLB is lightweight and flexible where it runs on nearly any environment and only needs access to your Proxmox host’s API endpoint (commonly TCP port 8006).

Therefore, you can simply run ProxLB on:
* Bare-metal Systems
* VMs (even inside the Proxmox cluster)
* Docker/Podman Container
* LXC Container
* On a Proxmox node