# ProxLB - (Re)Balance VM Workloads in Proxmox Clusters
<img align="left" src="https://cdn.gyptazy.com/img/ProxLB.jpg"/>
<br>

<p float="center"><img src="https://img.shields.io/github/license/gyptazy/ProxLB"/><img src="https://img.shields.io/github/contributors/gyptazy/ProxLB"/><img src="https://img.shields.io/github/last-commit/gyptazy/ProxLB/main"/><img src="https://img.shields.io/github/issues-raw/gyptazy/ProxLB"/><img src="https://img.shields.io/github/issues-pr/gyptazy/ProxLB"/></p>

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [How does it work?](#how-does-it-work)
4. [Documentation](#documentation)
5. [Installation](#installation)
   1. [Requirements / Dependencies](#requirements--dependencies)
   2. [Debian Package](#debian-package)
   4. [Container / Docker](#container--docker)
   5. [Source](#source)
6. [Usage / Configuration](#usage--configuration)
   1. [GUI Integration](#gui-integration)
   2. [Proxmox HA Integration](#proxmox-ha-integration)
   3. [Options](#options)
7. [Affinity & Anti-Affinity Rules](#affinity--anti-affinity-rules)
   1. [Affinity Rules](#affinity-rules)
   2. [Anti-Affinity Rules](#anti-affinity-rules)
   3. [Ignore VMs](#ignore-vms)
   4. [Pin VMs to Hypervisor Nodes](#pin-vms-to-hypervisor-nodes)
8. [Maintenance](#maintenance)
9. [Misc](#misc)
   1. [Bugs](#bugs)
   2. [Contributing](#contributing)
   3. [Support](#support)
   4. [Enterprise-Support](#enterprise-support)
10. [Author(s)](#authors)


## Introduction
ProxLB is an advanced load balancing solution specifically designed for Proxmox clusters, addressing the absence of an intelligent and more advanced resource scheduler. As a third-party solution, ProxLB enhances the management and efficiency of Proxmox clusters by intelligently distributing workloads across available nodes. Workloads can be balanced by different times like the guest's memory, CPU or disk usage or their assignment to avoid overprovisioning and ensuring resources.

One of the key advantages of ProxLB is that it is fully open-source and free, making it accessible for anyone to use, modify, and contribute to. This ensures transparency and fosters community-driven improvements. ProxLB supports filtering and ignoring specific nodes and guests through configuration files and API calls, providing administrators with the flexibility to tailor the load balancing behavior to their specific needs.

A standout feature of ProxLB is its maintenance mode. When enabled, all guest workloads are automatically moved to other nodes within the cluster, ensuring that a node can be safely updated, rebooted, or undergo hardware maintenance without disrupting the overall cluster operation. Additionally, ProxLB supports both affinity and anti-affinity rules, allowing operators to group multiple guests to run together on the same node or ensure that certain guests do not run on the same node, depending on the cluster's node count. This feature is crucial for optimizing performance and maintaining high availability.

ProxLB can also return the best next node for guest placement, which can be integrated into CI/CD pipelines using tools like Ansible or Terraform. This capability streamlines the deployment process and ensures efficient resource utilization. Furthermore, ProxLB leverages the Proxmox API, including the entire ACL (Access Control List) system, for secure and efficient operation. Unlike some solutions, it does not require SSH access, enhancing security and simplifying configuration.

Overall, ProxLB significantly enhances resource management by intelligently distributing workloads, reducing downtime through its maintenance mode, and providing improved flexibility with affinity and anti-affinity rules. Its seamless integration with CI/CD tools and reliance on the Proxmox API make it a robust and secure solution for optimizing Proxmox cluster performance.

### Video of Migration
<img src="https://cdn.gyptazy.com/img/proxlb-rebalancing-demo.gif"/>

## Features
ProxLB's key features are by enabling automatic rebalancing of VMs and CTs across a Proxmox cluster based on memory, CPU, and local disk usage while identifying optimal nodes for automation. It supports maintenance mode, affinity rules, and seamless Proxmox API integration with ACL support, offering flexible usage as a one-time operation, a daemon, or through the Proxmox Web GUI.

**Features**
* Rebalance VMs/CTs in the cluster by:
  * Memory
  * Disk (only local storage)
  * CPU
* Rebalance by different modes:
  * Used resources
  * Assigned resources
  * PSI (Pressure) of resources
* Get best nodes for further automation
* Supported Guest Types
  * VMs
  * CTs
* Maintenance Mode
  * Set node(s) into maintenance
  * Move all workloads to different nodes
* Affinity / Anti-Affinity Rules
* Fully based on Proxmox API
  * Fully integrated into the Proxmox ACL
  * No SSH required
* Usage
  * One-Time
  * Daemon
  * Proxmox Web GUI Integration

## How does it work?
ProxLB is a load-balancing system designed to optimize the distribution of virtual machines (VMs) and containers (CTs) across a cluster. It works by first gathering resource usage metrics from all nodes in the cluster through the Proxmox API. This includes detailed resource metrics for each VM and CT on every node. ProxLB then evaluates the difference between the maximum and minimum resource usage of the nodes, referred to as "Balanciness." If this difference exceeds a predefined threshold (which is configurable), the system initiates the rebalancing process.

Before starting any migrations, ProxLB validates that rebalancing actions are necessary and beneficial. Depending on the selected balancing mode — such as CPU, memory, or disk — it creates a balancing matrix. This matrix sorts the VMs by their maximum used or assigned resources, identifying the VM with the highest usage. ProxLB then places this VM on the node with the most free resources in the selected balancing type. This process runs recursively until the operator-defined Balanciness is achieved. Balancing can be defined for the used or max. assigned resources of VMs/CTs.

## Documentation
This `README.md` doesn't contain all information and only highlights the most important facts. Extended information, such like API permissions, creating dedicated user, best-practices in running ProxLB and much more can be found in the [docs/](https://github.com/gyptazy/ProxLB/tree/main/docs) directory. Please consult the documentation before creating issues.

## Installation

### Requirements / Dependencies
* Proxmox
    * Proxmox 7.x
    * Proxmox 8.x
    * Proxmox 9.x
* Python3.x
* proxmoxer
* requests
* urllib3
* pyyaml

The dependencies can simply be installed with `pip` by running the following command:
```
pip install -r requirements.txt
```

*Note: Distribution packages, such like the provided `.deb` package will automatically resolve and install all required dependencies by using already packaged version from the distribution's repository. By using the Docker (container) image or Debian packages, you do not need to take any care of the requirements listed here.*

### Debian Package
ProxLB is a powerful and flexible load balancer designed to work across various architectures, including `amd64`, `arm64`, `rv64` and many other ones that support Python. It runs independently of the underlying hardware, making it a versatile choice for different environments. This chapter covers the step-by-step process to install ProxLB on Debian-based systems, including Debian clones like Ubuntu.

#### Quick-Start
You can simply use this snippet to install the repository and to install ProxLB on your system.

```bash
echo "deb https://repo.gyptazy.com/stable /" > /etc/apt/sources.list.d/proxlb.list
wget -O /etc/apt/trusted.gpg.d/proxlb.asc https://repo.gyptazy.com/repository.gpg
apt-get update && apt-get -y install proxlb
cp /etc/proxlb/proxlb_example.yaml /etc/proxlb/proxlb.yaml
# Adjust the config to your needs
vi /etc/proxlb/proxlb.yaml
systemctl start proxlb
```

Afterwards, ProxLB is running in the background and balances your cluster by your defined balancing method (default: memory).

**Note**: If you want to use ProxLB with the proxmox-offline-mirror or any other APT mirror tool that does not support the flat repository architecture, please see the [docs](https://github.com/gyptazy/ProxLB/blob/main/docs/02_installation.md#Repo-Mirror-and-Proxmox-Offline-Mirror-Support) how you can add this by using ProxLB's fully repo.

#### Details
ProxLB provides two different repositories:
* https://repo.gyptazy.com/stable (only stable release)
* https://repo.gyptazy.com/testing (bleeding edge - not recommended)

The repository is signed and the GPG key can be found at:
* https://repo.gyptazy.com/repository.gpg

You can also simply import it by running:

```
# KeyID:  17169F23F9F71A14AD49EDADDB51D3EB01824F4C
# UID:    gyptazy Solutions Repository <contact@gyptazy.com>
# SHA256: 52c267e6f4ec799d40cdbdb29fa518533ac7942dab557fa4c217a76f90d6b0f3  repository.gpg

wget -O /etc/apt/trusted.gpg.d/proxlb.asc https://repo.gyptazy.com/repository.gpg
```

*Note: The defined repositories `repo.gyptazy.com` and `repo.proxlb.de` are the same!*

#### Debian Packages (.deb files)
If you do not want to use the repository you can also find the debian packages as a .deb file on gyptazy's CDN at:
* https://cdn.gyptazy.com/debian/proxlb/

Afterwards, you can simply install the package by running:
```bash
dpkg -i proxlb_*.deb
cp /etc/proxlb/proxlb_example.yaml /etc/proxlb/proxlb.yaml
# Adjust the config to your needs
vi /etc/proxlb/proxlb.yaml
systemctl start proxlb
```

### Container Images / Docker
Using the ProxLB container images is straight forward and only requires you to mount the config file.

```bash
# Pull the image
docker pull cr.gyptazy.com/proxlb/proxlb:latest
# Download the config
wget -O proxlb.yaml https://raw.githubusercontent.com/gyptazy/ProxLB/refs/heads/main/config/proxlb_example.yaml
# Adjust the config to your needs
vi proxlb.yaml
# Start the ProxLB container image with the ProxLB config
docker run -it --rm -v $(pwd)/proxlb.yaml:/etc/proxlb/proxlb.yaml proxlb
```

### Docker Compose

```bash
services:
  proxlb:
    image: cr.gyptazy.com/proxlb/proxlb:latest
    container_name: proxlb
    restart: unless-stopped
    volumes:
      - ./proxlb.yaml:/etc/proxlb/proxlb.yaml:ro
```

*Note: ProxLB container images are officially only available at cr.proxlb.de and cr.gyptazy.com.*

#### Overview of Images
| Version | Image |
|------|:------:|
| latest | cr.gyptazy.com/proxlb/proxlb:latest |
| v1.1.11 | cr.gyptazy.com/proxlb/proxlb:v1.1.11 |
| v1.1.10 | cr.gyptazy.com/proxlb/proxlb:v1.1.10 |
| v1.1.9.1 | cr.gyptazy.com/proxlb/proxlb:v1.1.9.1 |
| v1.1.9 | cr.gyptazy.com/proxlb/proxlb:v1.1.9 |
| v1.1.8 | cr.gyptazy.com/proxlb/proxlb:v1.1.8 |
| v1.1.7 | cr.gyptazy.com/proxlb/proxlb:v1.1.7 |
| v1.1.6.1 | cr.gyptazy.com/proxlb/proxlb:v1.1.6.1 |
| v1.1.6 | cr.gyptazy.com/proxlb/proxlb:v1.1.6 |
| v1.1.5 | cr.gyptazy.com/proxlb/proxlb:v1.1.5 |
| v1.1.4 | cr.gyptazy.com/proxlb/proxlb:v1.1.4 |
| v1.1.3 | cr.gyptazy.com/proxlb/proxlb:v1.1.3 |
| v1.1.2 | cr.gyptazy.com/proxlb/proxlb:v1.1.2 |
| v1.1.1 | cr.gyptazy.com/proxlb/proxlb:v1.1.1 |
| v1.1.0 | cr.gyptazy.com/proxlb/proxlb:v1.1.0 |
| v1.0.6 | cr.gyptazy.com/proxlb/proxlb:v1.0.6 |
| v1.0.5 | cr.gyptazy.com/proxlb/proxlb:v1.0.5 |
| v1.0.4 | cr.gyptazy.com/proxlb/proxlb:v1.0.4 |
| v1.0.3 | cr.gyptazy.com/proxlb/proxlb:v1.0.3 |
| v1.0.2 | cr.gyptazy.com/proxlb/proxlb:v1.0.2 |
| v1.0.0 | cr.gyptazy.com/proxlb/proxlb:v1.0.0 |
| v0.9.9 | cr.gyptazy.com/proxlb/proxlb:v0.9.9 |

### Source
ProxLB can also easily be used from the provided sources - for traditional systems but also as a Docker/Podman container image.

#### Traditional System
Setting up and running ProxLB from the sources is simple and requires just a few commands. Ensure Python 3 and the Python dependencies are installed on your system, then run ProxLB using the following command:
```bash
git clone https://github.com/gyptazy/ProxLB.git
cd ProxLB
```

Afterwards simply adjust the config file to your needs:
```bash
vi config/proxlb.yaml
```

Start ProxLB by Python3 on the system:
```bash
python3 proxlb/main.py -c config/proxlb.yaml
```

#### Container Image
Creating a container image of ProxLB is straightforward using the provided Dockerfile. The Dockerfile simplifies the process by automating the setup and configuration required to get ProxLB running in an Alpine container. Simply follow the steps in the Dockerfile to build the image, ensuring all dependencies and configurations are correctly applied. For those looking for an even quicker setup, a ready-to-use ProxLB container image is also available, eliminating the need for manual building and allowing for immediate deployment.

```bash
git clone https://github.com/gyptazy/ProxLB.git
cd ProxLB
docker build -t proxlb .
```

Afterwards simply adjust the config file to your needs:
```bash
vi config/proxlb.yaml
```

Finally, start the created container.
```bash
docker run -it --rm -v $(pwd)/proxlb.yaml:/etc/proxlb/proxlb.yaml proxlb
```

## Usage / Configuration
Running ProxLB is straightforward and versatile, as it only requires `Python3` and the `proxmoxer` library. This means ProxLB can be executed directly on a Proxmox node or on dedicated systems such as Debian, RedHat, or even FreeBSD, provided that the Proxmox API is accessible from the client running ProxLB. ProxLB can also run inside a Container - Docker or LXC - and is simply up to you.

### GUI Integration
<img align="left" src="https://cdn.gyptazy.com/img/rebalance-ui.jpg"/> ProxLB can also be accessed through the Proxmox Web UI by installing the optional `pve-proxmoxlb-service-ui` package, which depends on the proxlb package. For full Web UI integration, this package must be installed on all nodes within the cluster. Once installed, a new menu item - `Rebalancing`, appears in the cluster level under the HA section. Once installed, it offers two key functionalities:
* Rebalancing VM workloads
* Migrate VM workloads away from a defined node (e.g. maintenance preparation)

**Note:** This package is currently discontinued and will be readded at a later time. See also: [#44: How to install pve-proxmoxlb-service-ui package](https://github.com/gyptazy/ProxLB/issues/44).

### Proxmox HA Integration
Proxmox HA (High Availability) groups are designed to ensure that virtual machines (VMs) remain running within a Proxmox cluster. HA groups define specific rules for where VMs should be started or migrated in case of node failures, ensuring minimal downtime and automatic recovery.

However, when used in conjunction with ProxLB, the built-in load balancer for Proxmox, conflicts can arise. ProxLB operates with its own logic for workload distribution, taking into account affinity and anti-affinity rules. While it effectively balances guest workloads, it may re-shift and redistribute VMs in a way that does not align with HA group constraints, potentially leading to unsuitable placements.

Due to these conflicts, it is currently not recommended to use both HA groups and ProxLB simultaneously. The interaction between the two mechanisms can lead to unexpected behavior, where VMs might not adhere to HA group rules after being moved by ProxLB.

A solution to improve compatibility between HA groups and ProxLB is under evaluation, aiming to ensure that both features can work together without disrupting VM placement strategies.

See also: [#65: Host groups: Honour HA groups](https://github.com/gyptazy/ProxLB/issues/65).

### Options
The following options can be set in the configuration file `proxlb.yaml`:

| Section | Option | Sub Option | Example | Type | Description |
|---------|:------:|:----------:|:-------:|:----:|:-----------:|
| `proxmox_api` |  |  |  |  |  |
|  | hosts |  | ['virt01.example.com', '10.10.10.10', 'fe01:bad:code::cafe', 'virt01.example.com:443', '[fc00::1]', '[fc00::1]:443', 'fc00::1:8006'] | `List` | List of Proxmox nodes. Can be IPv4, IPv6 or mixed. You can specify custom ports. In case of IPv6 without brackets the port is considered after the last colon |
|  | user |  | root@pam | `Str` | Username for the API. |
|  | pass |  | FooBar | `Str` | Password for the API. (Recommended: Use API token authorization!) |
|  | token_id |  | proxlb | `Str` | Token ID of the user for the API. |
|  | token_secret |  | 430e308f-1337-1337-beef-1337beefcafe | `Str` | Secret of the token ID for the API. |
|  | ssl_verification |  | True | `Bool` | Validate SSL certificates (1) or ignore (0). [values: `1` (default), `0`] |
|  | timeout |  | 10 | `Int` | Timeout for the Proxmox API in sec. |
|  | retries |  | 1 | `Int` | How often a connection attempt to the defined API host should be performed. |
|  | wait_time |  | 1 | `Int` | How many seconds should be waited before performing another connection attempt to the API host. |
| `proxmox_cluster` |  |  |  |  |  |
|  | maintenance_nodes |  | ['virt66.example.com'] | `List` | A list of Proxmox nodes that are defined to be in a maintenance. (must be the same node names as used within the cluster) |
|  | ignore_nodes |  | [] | `List` | A list of Proxmox nodes that are defined to be ignored. |
|  | overprovisioning |  | False | `Bool` | Avoids balancing when nodes would become overprovisioned. |
| `balancing` |  |  |  |  |  |
|  | enable |  | True | `Bool` | Enables the guest balancing.|
|  | enforce_affinity |  | False | `Bool` | Enforcing affinity/anti-affinity rules but balancing might become worse. |
|  | enforce_pinning |  | False | `Bool` | Enforcing pinning rules but balancing might become worse. |
|  | parallel |  | False | `Bool` | If guests should be moved in parallel or sequentially.|
|  | parallel_jobs |  | 5 | `Int` | The amount if parallel jobs when migrating guests. (default: `5`)|
|  | live |  | True | `Bool` | If guests should be moved live or shutdown.|
|  | with_local_disks |  | True | `Bool` | If balancing of guests should include local disks.|
|  | with_conntrack_state |  | True | `Bool` | If balancing of guests should including the conntrack state.|
|  | balance_types |  | ['vm', 'ct'] | `List` | Defined the types of guests that should be honored. [values: `vm`, `ct`]|
|  | max_job_validation |  | 1800 | `Int` | How long a job validation may take in seconds. (default: 1800) |
|  | balanciness |  | 10 | `Int` | The maximum delta of resource usage between node with highest and lowest usage. |
|  | memory_threshold |  | 75 | `Int` | The maximum threshold (in percent) that needs to be hit to perform balancing actions. (Optional) |
|  | method |  | memory | `Str` | The balancing method that should be used.  [values: `memory` (default), `cpu`, `disk`]|
|  | mode |  | used | `Str` | The balancing mode that should be used. [values: `used` (default), `assigned`, `psi` (pressure)] |
|  | balance_larger_guests_first |  | False | `Bool` | Option to prefer larger/smaller guests first |
|  | node_resource_reserve |  | { default: { memory: 4 }, { node01: { memory: 6 }} } | `Dict` | A dict of pool names and their type for creating affinity/anti-affinity rules |
|  | psi |  | { nodes: { memory: { pressure_full: 0.20, pressure_some: 0.20, pressure_spikes: 1.00 }}} | `Dict` | A dict of PSI based thresholds for nodes and guests |
|  | pools |  | pools: { dev: { type: affinity }, de-nbg01-db: { type: anti-affinity }} | `Dict` | A dict of pool names and their type for creating affinity/anti-affinity rules |
| `service` |  |  |  |  |  |
|  | daemon |  | True | `Bool` | If daemon mode should be activated. |
|  | `schedule` |  |  | `Dict` | Schedule config block for rebalancing. |
|  |  | interval | 12 | `Int` | How often rebalancing should occur in daemon mode.|
|  |  | format | hours | `Str` | Sets the time format. [values: `hours` (default), `minutes`]|
|  | `delay` |  |  | `Dict` | Schedule config block for an optional delay until the service starts. |
|  |  | enable | False | `Bool` | If a delay time should be validated.|
|  |  | time | 1 | `Int` | Delay time until the service starts after the initial execution.|
|  |  | format | hours | `Str` | Sets the time format. [values: `hours` (default), `minutes`]|
|  | log_level |  | INFO | `Str` | Defines the default log level that should be logged. [values: `INFO` (default), `WARNING`, `CRITICAL`, `DEBUG`] |


An example of the configuration file looks like:
```
proxmox_api:
  hosts: ['virt01.example.com', '10.10.10.10', 'fe01:bad:code::cafe']
  user: root@pam
  pass: crazyPassw0rd!
  # API Token method
  # token_id: proxlb
  # token_secret: 430e308f-1337-1337-beef-1337beefcafe
  ssl_verification: True
  timeout: 10
  # API Connection retries
  # retries: 1
  # wait_time: 1

proxmox_cluster:
  maintenance_nodes: ['virt66.example.com']
  ignore_nodes: []
  overprovisioning: True

balancing:
  enable: True
  enforce_affinity: False
  enforce_pinning: False
  parallel: False
  live: True
  with_local_disks: True
  with_conntrack_state: True
  balance_types: ['vm', 'ct']
  max_job_validation: 1800
  memory_threshold: 75
  balanciness: 5
  method: memory
  mode: used
  balance_larger_guests_first: False
  node_resource_reserve:
    defaults:
      memory: 4
    node01:
      memory: 6
# # PSI thresholds only apply when using mode 'psi'
# # PSI based balancing is currently in beta and req. PVE >= 9
# psi:
#   nodes:
#     memory:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
#     cpu:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
#     disk:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
#   guests:
#     memory:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
#     cpu:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
#     disk:
#       pressure_full: 0.20
#       pressure_some: 0.20
#       pressure_spikes: 1.00
  pools:
    dev:
      type: affinity
    de-nbg01-db
      type: anti-affinity
      pin:
        - virt66
        - virt77
      strict: False

service:
  daemon: True
  schedule:
    interval: 12
    format: hours
  delay:
    enable: False
    time: 1
    format: hours
  log_level: INFO
```

### Parameters
The following options and parameters are currently supported:

| Option | Long Option | Description | Default |
|------|:------:|------:|------:|
| -c | --config | Path to a config file. | /etc/proxlb/proxlb.yaml (default) |
| -d | --dry-run | Performs a dry-run without doing any actions. | False |
| -j | --json | Returns a JSON of the VM movement. | False |
| -b | --best-node | Returns the best next node for a VM/CT placement (useful for further usage with Terraform/Ansible). | False |
| -v | --version | Returns the ProxLB version on stdout. | False |

## Affinity & Anti-Affinity Rules
ProxLB provides an advanced mechanism to define affinity and anti-affinity rules, enabling precise control over virtual machine (VM) placement. These rules help manage resource distribution, improve high availability configurations, and optimize performance within a Proxmox Virtual Environment (PVE) cluster. By leveraging Proxmox’s integrated access management, ProxLB ensures that users can only define and manage rules for guests they have permission to access.

ProxLB implements affinity and anti-affinity rules through a tag-based system within the Proxmox web interface. Each guest (virtual machine or container) can be assigned specific tags, which then dictate its placement behavior. This method maintains a streamlined and secure approach to managing VM relationships while preserving Proxmox’s inherent permission model.

### Affinity Rules
<img align="left" src="https://cdn.gyptazy.com/img/proxlb-affinity-rules.jpg"/> Affinity rules are used to group certain VMs together, ensuring that they run on the same host whenever possible. This can be beneficial for workloads requiring low-latency communication, such as clustered databases or application servers that frequently exchange data. In general, there're two ways to manage affinity rules:

#### Affinity Rules by Tags
To define an affinity rule which keeps all guests assigned to this tag together on a node, users assign a tag with the prefix `plb_affinity_$TAG`:

#### Example for Screenshot
```
plb_affinity_talos
```
As a result, ProxLB will attempt to place all VMs with the `plb_affinity_web` tag on the same host (see also the attached screenshot with the same node).

#### Affinity Rules by Pools
Antoher approach is by using pools in Proxmox. This way, it can easily also combined with other resources like backup jobs. However, in this approach you need to modify the ProxLB config file to your needs. Within the `balancing` section you can create a dict of pools, including the pool name and the affinity type. Please see the example for further details:

**Example Config**
```
balancing:
  [...]
  pools:                              # Optional: Define affinity/anti-affinity rules per pool
    dev:                              # Pool name: dev
      type: affinity                  # Type: affinity (keeping VMs together)
      pin:                            # Pin VMs to Nodes
        - virt77                        # Pinning to 'virt77' which is maybe an older system for dev labs
```

### Anti-Affinity Rules by Tags
<img align="left" src="https://cdn.gyptazy.com/img/proxlb-anti-affinity-rules.jpg"/> Conversely, anti-affinity rules ensure that designated VMs do not run on the same physical host. This is particularly useful for high-availability setups, where redundancy is crucial. Ensuring that critical services are distributed across multiple hosts reduces the risk of a single point of failure. In general, there're two ways to manage anti-affinity rules:

To define an anti-affinity rule that ensures to not move systems within this group to the same node, users assign a tag with the prefix:

#### Example for Screenshot
```
plb_anti_affinity_ntp
```

As a result, ProxLB will try to place the VMs with the `plb_anti_affinity_ntp` tag on different hosts (see also the attached screenshot with the different nodes).

#### Anti-Affinity Rules by Pools
Antoher approach is by using pools in Proxmox. This way, it can easily also combined with other resources like backup jobs. However, in this approach you need to modify the ProxLB config file to your needs. Within the `balancing` section you can create a dict of pools, including the pool name and the affinity type. Please see the example for further details:

**Example Config**
```
balancing:
  [...]
  pools:                              # Optional: Define affinity/anti-affinity rules per pool
    de-nbg01-db:                      # Pool name: de-nbg01-db
      type: anti-affinity                  # Type: anti-affinity (spreading VMs apart)
```


**Note:** While this ensures that ProxLB tries distribute these VMs across different physical hosts within the Proxmox cluster this may not always work. If you have more guests attached to the group than nodes in the cluster, we still need to run them anywhere. If this case occurs, the next one with the most free resources will be selected.

### Ignore VMs
<img align="left" src="https://cdn.gyptazy.com/img/proxlb-ignore-vm-movement.jpg"/> Guests, such as VMs or CTs, can also be completely ignored. This means, they won't be affected by any migration (even when (anti-)affinity rules are enforced). To ensure a proper resource evaluation, these guests are still collected and evaluated but simply skipped for balancing actions. Another thing is the implementation. While ProxLB might have a very restricted configuration file including the file permissions, this file is only read- and writeable by the Proxmox administrators. However, we might have user and groups who want to define on their own that their systems shouldn't be moved. Therefore, these users can simpy set a specific tag to the guest object - just like the (anti)affinity rules.

To define a guest to be ignored from the balancing, users assign a tag with the prefix `plb_ignore_$TAG`:

#### Example for Screenshot
```
plb_ignore_dev
```

As a result, ProxLB will not migrate this guest with the `plb_ignore_dev` tag to any other node.

**Note:** Ignored guests are really ignored. Even by enforcing affinity rules this guest will be ignored.

### Pin VMs to Specific Hypervisor Nodes
<img align="left" src="https://cdn.gyptazy.com/img/proxlb-tag-node-pinning.jpg"/> Guests, such as VMs or CTs, can also be pinned to specific (and multiple) nodes in the cluster. This might be usefull when running applications with some special licensing requirements that are only fulfilled on certain nodes. It might also be interesting, when some physical hardware is attached to a node, that is not available in general within the cluster.

#### Pinning VMs to (a) specific Hypervisor Node(s) by Tag
To pin a guest to a specific cluster node, users assign a tag with the prefix `plb_pin_$nodename` to the desired guest:

#### Example for Screenshot
```
plb_pin_node03
```

As a result, ProxLB will pin the guest `dev-vm01` to the node `virt03`.


#### Pinning VMs to (a) specific Hypervisor Node(s) by Pools
Beside the tag approach, you can also pin a resource group to a specific hypervisor or groups of hypervisors by defining a `pin` key of type list.

**Example Config**
```
balancing:
  [...]
  pools:                              # Optional: Define affinity/anti-affinity rules per pool
    dev:                              # Pool name: dev
      type: affinity                  # Type: affinity (keeping VMs together)
      pin:                            # Pin VMs to Nodes
        - virt77                        # Pinning to 'virt77' which is maybe an older system for dev labs
```


You can also repeat this step multiple times for different node names to create a potential group of allowed hosts where a the guest may be served on. In this case, ProxLB takes the node with the lowest used resources according to the defined balancing values from this group.

**Note:** The given node names from the tag are validated. This means, ProxLB validated if the given node name is really part of the cluster. In case of a wrongly defined or unavailable node name it continous to use the regular processes to make sure the guest keeps running.

## Maintenance
The `maintenance_nodes` option allows operators to designate one or more Proxmox nodes for maintenance mode. When a node is set to maintenance, no new guest workloads will be assigned to it, and all existing workloads will be migrated to other available nodes within the cluster. This process ensures that (anti)-affinity rules and resource availability are respected, preventing disruptions while maintaining optimal performance across the infrastructure.

### Adding / Removing Nodes from Maintenance
Within the section `proxmox_cluster` you can define the key `maintenance_nodes` as a list object. Simply add/remove one or more nodes with their equal name in the cluster and restart the daemon.
```
proxmox_cluster:
  maintenance_nodes: ['virt66.example.com']
```
Afterwards, all guest objects will be moved to other nodes in the cluster by ensuring the best balancing.

## Misc
### Bugs
Bugs can be reported via the GitHub issue tracker [here](https://github.com/gyptazy/ProxLB/issues). You may also report bugs via email or deliver PRs to fix them on your own. Therefore, you might also see the contributing chapter.

### Contributing
Feel free to add further documentation, to adjust already existing one or to contribute with code. Please take care about the style guide and naming conventions. You can find more in our [CONTRIBUTING.md](https://github.com/gyptazy/ProxLB/blob/main/CONTRIBUTING.md) file.

### Support
If you need assistance or have any questions, we offer support through our dedicated [chat room](https://matrix.to/#/#proxlb:gyptazy.com) in Matrix or [Discord](https://discord.gg/JemGu7WbfQ). Join our community for real-time help, advice, and discussions. The Matrix and Discord room are bridged to ensure that the communication is not splitted - so simply feel free to join which fits most to you!

Connect with us in our dedicated chat room for immediate support and live interaction with other users and developers. You can also visit our [GitHub Community](https://github.com/gyptazy/ProxLB/discussions/) to post your queries, share your experiences, and get support from fellow community members and moderators. You may also just open directly an issue [here](https://github.com/gyptazy/ProxLB/issues) on GitHub.

| Support Channel | Link |
|------|:------:|
| Matrix | [#proxlb:gyptazy.com](https://matrix.to/#/#proxlb:gyptazy.com) |
| Discord | [Discord](https://discord.gg/JemGu7WbfQ) |
| GitHub Community | [GitHub Community](https://github.com/gyptazy/ProxLB/discussions/)
| GitHub | [ProxLB GitHub](https://github.com/gyptazy/ProxLB/issues) |

**Note:** Please always keep in mind that this is a one-man show project without any further help. This includes coding, testing, packaging and all the infrastructure around it to keep this project up and running.

### Enterprise-Support
Running critical infrastructure in an enterprise environment often comes with requirements that go far beyond functionality alone. Enterprises typically expect predictable service levels, defined escalation paths, and guaranteed response times. In many cases, organizations also demand 24x7 support availability to ensure that their systems remain stable and resilient, even under unexpected circumstances.

As the creator and maintainer of ProxLB, I operate as a one-man project. While I am continuously working to improve the software, I cannot provide the type of enterprise-grade support that large organizations may require. To address this need, several companies have stepped in to offer professional services around ProxLB in Proxmox VE clusters.

Below is a list of organizations currently known to provide enterprise-level support for ProxLB. If your business relies on ProxLB in production and you require more than community-based support, these providers may be a good fit for your needs:

| Company| Country | Web |
|------|:------:|:------:|
| credativ | DE | [credativ.de](https://www.credativ.de/en/portfolio/support/proxmox-virtualization/) |

*Note: If you provide support for ProxLB, feel free to create PR with your addition.*

### Author(s)
 * Florian Paul Azim Hoberg @gyptazy (https://gyptazy.com)
