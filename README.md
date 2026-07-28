# ProxLB - (Re)Balance VM Workloads in Proxmox Clusters
<img align="left" src="https://cdn.gyptazy.com/img/ProxLB.jpg"/>
<br>

<p float="center"><img src="https://img.shields.io/github/license/gyptazy/ProxLB"/><img src="https://img.shields.io/github/contributors/gyptazy/ProxLB"/><img src="https://img.shields.io/github/last-commit/gyptazy/ProxLB/main"/><img src="https://img.shields.io/github/issues-raw/gyptazy/ProxLB"/><img src="https://img.shields.io/github/issues-pr/gyptazy/ProxLB"/></p>

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [How does it work?](#how-does-it-work)
4. [ProxLB vs Proxmox Dynamic Load Balancing](#ProxLB-vs-Proxmox-Dynamic-Load-Balancing)
5. [Documentation](#documentation)
6. [Installation](#installation)
   1. [Requirements / Dependencies](#requirements--dependencies)
   2. [Debian Package](#debian-package)
   4. [Container / Docker](#container--docker)
   5. [Source](#source)
   6. [CP-SAT Solver (Optional)](#cp-sat-solver-optional)
7. [Usage / Configuration](#usage--configuration)
   1. [Proxmox HA Integration](#proxmox-ha-integration)
   2. [Options](#options)
8. [Affinity & Anti-Affinity Rules](#affinity--anti-affinity-rules)
   1. [Affinity Rules](#affinity-rules)
   2. [Anti-Affinity Rules](#anti-affinity-rules)
   3. [Ignore VMs](#ignore-vms)
   4. [Pin VMs to Hypervisor Nodes](#pin-vms-to-hypervisor-nodes)
9. [Maintenance](#maintenance)
10. [Misc](#misc)
   1. [Bugs](#bugs)
   2. [Contributing](#contributing)
   3. [Support](#support)
11. [Enterprise-Support](#enterprise-support)
12. [Prox-Tools Collection](#prox-tools-collection)
13. [Author(s)](#authors)


## Introduction
ProxLB is an advanced load balancing solution (initially written by [@gyptazy](https://gyptazy.com/proxlb/)) specifically designed for Proxmox clusters, addressing the absence of an intelligent and more advanced resource scheduler. As a third-party solution, ProxLB enhances the management and efficiency of Proxmox clusters by intelligently distributing workloads across available nodes. Workloads can be balanced by different times like the guest's memory, CPU or disk usage or their assignment to avoid overprovisioning and ensuring resources.

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

## ProxLB vs Proxmox Dynamic Load Balancing
With the introduction of Dynamic Load Balancing (DLB) in Proxmox VE 9.2, Proxmox now includes a native solution for automatically balancing HA workloads across cluster nodes. This naturally raises the question of how ProxLB compares to the built-in scheduler and whether an external balancing solution is still necessary.

While both solutions aim to optimize resource utilization and automate VM placement, they follow different design philosophies. Proxmox DLB focuses on native integration, simplicity, and HA-aware balancing directly within the Proxmox cluster stack, whereas ProxLB provides a more flexible and customizable orchestration layer with advanced placement logic, affinity handling, and policy-based scheduling for any kind of workloads and is **not** limited to only HA workloads.

The following comparison highlights the key differences, strengths, and use cases of both approaches.

| Feature | ProxLB | PVE Native DLB |
|---|---|---|
| Integration level | External third-party scheduler | Built directly into Proxmox HA/CRS |
| Works for guests with HA stack | Yes | Yes|
| Works for guests without HA stack | Yes | No |
| Real-time balancing | Yes | Yes |
| VM migration automation | Yes | Yes |
| Affinity / anti-affinity rules | Advanced | More basic / HA-rule focused |
| Node pinning | Yes, incl. groups | Yes |
| ProxPatch Support | Yes | No |
| Custom scheduling logic | Extensive | Limited to Proxmox parameters |
| Metrics considered | CPU, RAM, disk, overprovisioning, assignment logic | Primarily node + guest runtime utilization |
| GUI integration | Partial / custom | Fully native |
| Maintenance burden | You manage updates/config | Supported by Proxmox |
| Stability / support | Community project | Officially supported |
| Enterprise readiness | Powerful but external | Much better for standardized environments |
| Complexity | Higher | Lower |
| Best suited for | Advanced custom orchestration | Native enterprise balancing |
| Dependency footprint | Additional daemon/service | Built-in functionality |
| Upgrade handling | Manual compatibility validation | Included in Proxmox upgrades |
| Scheduling aggressiveness | Highly customizable | Conservative by design |
| Corosync related | No (good) | Yes (bad) |

> [!TIP]
> Still using PVE 8? The only solution is ProxLB! If you encounter issues due to more Corosync traffic, you might also want to switch to ProxLB (for large-scaled environemnts).

## Documentation
This `README.md` doesn't contain all information and only highlights the most important facts. Extended information, such like API permissions, creating dedicated user, best-practices in running ProxLB and much more can be found in the [docs/](https://github.com/gyptazy/ProxLB/tree/main/docs) directory. Please consult the documentation before creating issues.

## Installation
ProxLB can be installed as a Debian package or by a container image. With the provided Helm charts it can also easily be deployed into Kubernetes stacks.

*Note: The Debian repository and container image registry are currently operated by @gyptazy and will be migrated to a new location in the future.*


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
# Add GPG key
curl -fsSL https://packages.credativ.com/public/proxtools/public.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/proxtools-archive-keyring.gpg

# Add repository
echo "deb [signed-by=/etc/apt/keyrings/proxtools-archive-keyring.gpg] \
https://packages.credativ.com/public/proxtools stable main" \
| sudo tee /etc/apt/sources.list.d/proxlb.list

# Update & install
sudo apt-get update
sudo apt-get -y install proxlb

# Copy example config
sudo cp /etc/proxlb/proxlb_example.yaml /etc/proxlb/proxlb.yaml

# Adjust the config to your needs
sudo vi /etc/proxlb/proxlb.yaml

# Start service
sudo systemctl start proxlb

# Adjust the config to your needs
sudo vi /etc/proxlb/proxlb.yaml
sudo systemctl start proxlb
```

Afterwards, ProxLB is running in the background and balances your cluster by your defined balancing method (default: memory).

#### Details
ProxLB provides two different repositories:
* https://packages.credativ.com/public/proxtools stable main
* https://packages.credativ.com/public/proxtools snapshots main

The repository is signed and the GPG key can be found at:
* https://packages.credativ.com/public/proxtools/archive-keyring.gpg

You can also simply import it by running:

```
# KeyID:  34C5B9642CD591E5D090A03B062A8A3A410B831D
# UID:    Proxtools Repository Signer <info@credativ.de>
# SHA256: 4cb4a74b25f775616709eb0596eeeac61d8d28717f4872fef2d68fb558434ed3  public.key

wget -O /etc/apt/keyrings/proxtools-archive-keyring.gpg https://packages.credativ.com/public/proxtools/public.key
```

### Container Images / Docker
Using the ProxLB container images is straight forward and only requires you to mount the config file.

Available images can be found at the GitHub [packages page](https://github.com/credativ/ProxLB/pkgs/container/proxlb) or [Docker Hub](https://hub.docker.com/r/credativ/proxlb).

```bash
# Pull the image from GHCR
docker pull ghcr.io/credativ/proxlb:latest
# or Docker Hub
docker pull credativ/proxlb:latest
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
    image: ghcr.io/credativ/proxlb:latest
    container_name: proxlb
    restart: unless-stopped
    volumes:
      - ./proxlb.yaml:/etc/proxlb/proxlb.yaml:ro
```

*Note: ProxLB container images are officially only available at ghcr.io/credativ/proxlb or docker.io/credativ/proxlb*

### Source
ProxLB can also easily be used from the provided sources - for traditional systems but also as a Docker/Podman container image.

#### Traditional System
Setting up and running ProxLB from the sources is simple and requires just a few commands. Ensure Python 3 and the Python dependencies are installed on your system, then run ProxLB using the following command:
```bash
git clone https://github.com/credativ/ProxLB.git
cd ProxLB
```

Afterwards simply adjust the config file to your needs:
```bash
vi config/proxlb.yaml
```

Start ProxLB by Python3 on the system:
```bash
python3 -m proxlb -c config/proxlb.yaml
```

#### Container Image
Creating a container image of ProxLB is straightforward using the provided Dockerfile. The Dockerfile simplifies the process by automating the setup and configuration required to get ProxLB running in an Alpine container. Simply follow the steps in the Dockerfile to build the image, ensuring all dependencies and configurations are correctly applied. For those looking for an even quicker setup, a ready-to-use ProxLB container image is also available, eliminating the need for manual building and allowing for immediate deployment.

```bash
git clone https://github.com/credativ/ProxLB.git
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

### CP-SAT Solver (Optional)
ProxLB optionally integrates a CP-SAT-based placement solver (Google OR-Tools) that replaces the built-in greedy balancer with a mathematically optimal assignment engine. It runs in two modes:

* **Shadow mode** *(default)* — solver computes an optimal plan alongside ProxLB for comparison; no migrations are changed.
* **Active mode** — solver drives all migrations with automatic per-step verification and re-solve on failure.

Both modes produce a structured JSONL log and an HTML report showing the solver plan, node load before/after, and (in active mode) the execution result of every migration.

Add a `solver:` block to your `proxlb.yaml`:

```yaml
solver:
  enable: True
  mode: shadow            # 'shadow' (observe only) or 'active' (solver drives migrations)
  log_dir: /var/log/proxlb/solver
  timeout_seconds: 30
  use_reservations: True
  active_step_retries: 3
  fallback_to_greedy: True
```

See [docs/04_solver.md](docs/04_solver.md) for the full configuration reference, a description of the feedback loop in active mode, and instructions for generating HTML reports.

## Usage / Configuration
Running ProxLB is straightforward and versatile, as it only requires `Python3` and the `proxmoxer` library. This means ProxLB can be executed directly on a Proxmox node or on dedicated systems such as Debian, RedHat, or even FreeBSD, provided that the Proxmox API is accessible from the client running ProxLB. ProxLB can also run inside a Container - Docker or LXC - and is simply up to you.

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
|  | maintenance_nodes_schedule |  |  | `Dict` | A weekly schedule that temporarily adds nodes to `maintenance_nodes` during runtime. |
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
|  | cpu_threshold |  | 75 | `Int` | The maximum threshold (in percent) that needs to be hit to perform balancing actions. (Optional) |
|  | method |  | memory | `Str` | The balancing method that should be used.  [values: `memory` (default), `cpu`, `disk`]|
|  | mode |  | used | `Str` | The balancing mode that should be used. [values: `used` (default), `assigned`, `psi` (pressure)] |
|  | balance_larger_guests_first |  | False | `Bool` | Option to prefer larger/smaller guests first |
|  | node_resource_reserve |  | { default: { memory: 4 }, { node01: { memory: 6 }} } | `Dict` | A dict of pool names and their type for creating affinity/anti-affinity rules |
|  | psi |  | { nodes: { memory: { pressure_full: 0.20, pressure_some: 0.20, pressure_spikes: 1.00 }}} | `Dict` | A dict of PSI based thresholds for nodes and guests |
|  | pools |  | pools: { dev: { type: affinity }, de-nbg01-db: { type: anti-affinity }} | `Dict` | A dict of pool names and their type for creating affinity/anti-affinity rules |
| `service` |  |  |  |  |  |
|  | daemon |  | True | `Bool` | If daemon mode should be activated. |
|  | enable_ha |  | False | `Bool` | Enables HA mode of ProxLB. |
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
  maintenance_nodes_schedule:
    duration: 3
    pre-migration: 10
    schedules:
      virt77.example.com:
        - 'Monday, 8:00'
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
  #cpu_threshold: 75
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
  enable_ha: False
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

Maintenance mode can also be scheduled. Scheduled nodes are added during each runtime cycle and removed automatically when the active window ends. `duration` is counted in hours from the configured start time, while `pre-migration` starts maintenance mode that many minutes earlier.
```yaml
proxmox_cluster:
  maintenance_nodes_schedule:
    duration: 3
    pre-migration: 10
    schedules:
      virt77.example.com:
        - 'Monday, 8:00'
```

## Misc
### Bugs
Bugs can be reported via the GitHub issue tracker [here](https://github.com/gyptazy/ProxLB/issues). You may also report bugs via email or deliver PRs to fix them on your own. Therefore, you might also see the contributing chapter.

### Contributing
Feel free to add further documentation, to adjust already existing one or to contribute with code. Please take care about the style guide and naming conventions. You can find more in our [CONTRIBUTING.md](https://github.com/gyptazy/ProxLB/blob/main/CONTRIBUTING.md) file.

### Enterprise-Support
Running critical infrastructure in an enterprise environment often comes with requirements that go far beyond functionality alone. Enterprises typically expect predictable service levels, defined escalation paths, and guaranteed response times. In many cases, organizations also demand 24x7 support availability to ensure that their systems remain stable and resilient, even under unexpected circumstances.

[credativ.de GmbH](https://www.credativ.de/en/portfolio/support/proxmox-virtualization/) is also happy to provide enterprise support for ProxLB, including 24x7 support.

## Prox-Tools Collection
The [Prox-Tools collection](https://gyptazy.com/projects/) is a set of (mostly) open-source solutions crafted by our employee [@gyptazy](https://gyptazy.com/) with a clear mission: to close functional gaps in Proxmox VE environments that are especially relevant for enterprise use cases. While Proxmox VE already provides a powerful and flexible virtualization platform, real world production deployments often require additional tooling around scheduling, compatibility, automation, networking, and operational safety. Prox-Tools addresses exactly these needs.
All tools in this collection are designed with the same principles in mind: practical relevance, minimal complexity, transparent behavior, and full openness. They are built to integrate seamlessly into existing Proxmox VE clusters, without vendor lock-in, and with a strong focus on reliability and operational clarity. The current tools are listed below:
* [ProxLB](https://gyptazy.com/proxlb/): An advanced open-source load balancing and resource scheduling solution for Proxmox clusters.
* [ProxCLMC](https://gyptazy.com/proxclmc/): A CPU compatibility validator across Proxmox VE nodes for safe live migrations.
* [ProxSnap](https://gyptazy.com/proxsnap/): Snapshot management and cleanup tool for Proxmox VE clusters.
* [ProxWall](https://gyptazy.com/proxwall/): Micro-segmentation and advanced firewalling and networking for Proxmox VE clusters. It is designed to give enterprises fine-grained control over east-west and north-south traffic.
* [ProxWire](https://cdn.gyptazy.com/talks/ProxWire_Connecting_Proxmox_Clusters_Around_the_World_Without_Corosync.pdf): A forward-looking concept aimed at securely connecting Proxmox VE nodes across larger geographic distances.

## Author(s)
 * Florian Paul Azim Hoberg [@gyptazy](https://gyptazy.com/proxlb/)
