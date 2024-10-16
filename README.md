# ProxLB - (Re)Balance VM Workloads in Proxmox Clusters
<img align="left" src="https://cdn.gyptazy.com/images/Prox-LB-logo.jpg"/>
<br>

<p float="center"><img src="https://img.shields.io/github/license/gyptazy/ProxLB"/><img src="https://img.shields.io/github/contributors/gyptazy/ProxLB"/><img src="https://img.shields.io/github/last-commit/gyptazy/ProxLB/main"/><img src="https://img.shields.io/github/issues-raw/gyptazy/ProxLB"/><img src="https://img.shields.io/github/issues-pr/gyptazy/ProxLB"/></p>


## Table of Contents
- [ProxLB - (Re)Balance VM Workloads in Proxmox Clusters](#proxlb---rebalance-vm-workloads-in-proxmox-clusters)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [Video of Migration](#video-of-migration)
  - [Features](#features)
  - [How does it work?](#how-does-it-work)
  - [Usage](#usage)
    - [Dependencies](#dependencies)
    - [Options](#options)
      - [Notes](#notes)
    - [Parameters](#parameters)
    - [Balancing](#balancing)
      - [General](#general)
      - [By Used Memory of VMs/CTs](#by-used-memory-of-vmscts)
      - [By Assigned Memory of VMs/CTs](#by-assigned-memory-of-vmscts)
      - [Storage Balancing](#storage-balancing)
    - [Affinity Rules / Grouping Relationships](#affinity-rules--grouping-relationships)
      - [Affinity (Stay Together)](#affinity-stay-together)
      - [Anti-Affinity (Keep Apart)](#anti-affinity-keep-apart)
      - [Ignore VMs (Tag Style)](#ignore-vms-tag-style)
    - [Systemd](#systemd)
    - [Manual](#manual)
    - [Proxmox GUI Integration](#proxmox-gui-integration)
    - [Quick Start](#quick-start)
    - [Container Quick Start (Docker/Podman)](#container-quick-start-dockerpodman)
    - [Logging](#logging)
  - [Motivation](#motivation)
  - [References](#references)
  - [Downloads](#downloads)
    - [Packages](#packages)
    - [Repository](#repository)
      - [Stable Releases](#stable-releases)
      - [Beta/Testing Releases](#betatesting-releases)
    - [Container Images (Docker/Podman)](#container-images-dockerpodman)
  - [Misc](#misc)
    - [Bugs](#bugs)
    - [Contributing](#contributing)
    - [Documentation](#documentation)
    - [Support](#support)
    - [Author(s)](#authors)

## Introduction
`ProxLB` (PLB) is an advanced tool designed to enhance the efficiency and performance of Proxmox clusters by optimizing the distribution of virtual machines (VMs) or Containers (CTs) across the cluster nodes by using the Proxmox API. ProxLB meticulously gathers and analyzes a comprehensive set of resource metrics from both the cluster nodes and the running VMs. These metrics include CPU usage, memory consumption, and disk utilization, specifically focusing on local disk resources.

PLB collects resource usage data from each node in the Proxmox cluster, including CPU, (local) disk and memory utilization. Additionally, it gathers resource usage statistics from all running VMs, ensuring a granular understanding of the cluster's workload distribution.

Intelligent rebalancing is a key feature of ProxLB where it re-balances VMs based on their memory, disk or CPU usage, ensuring that no node is overburdened while others remain underutilized. The rebalancing capabilities of PLB significantly enhance cluster performance and reliability. By ensuring that resources are evenly distributed, PLB helps prevent any single node from becoming a performance bottleneck, improving the reliability and stability of the cluster. Efficient rebalancing leads to better utilization of available resources, potentially reducing the need for additional hardware investments and lowering operational costs.

Automated rebalancing reduces the need for manual actions, allowing operators to focus on other critical tasks, thereby increasing operational efficiency.

### Video of Migration
<img src="https://cdn.gyptazy.com/images/proxlb-rebalancing-demo.gif"/>

## Features
* Rebalance VMs/CTs in the cluster by:
  * Memory
  * Disk (only local storage)
  * CPU
* Rebalance Storage in the cluster
  * Rebalance VMs/CTs disks to other storage pools
  * Rebalance by used storage
* Get best Node for new VM/CT placement in cluster
* Performing
  * Periodically
  * One-shot solution
* Types
  * Rebalance only VMs
  * Rebalance only CTs
  * Rebalance all (VMs and CTs)
  * Rebalance VM/CT disks (Storage)
* Filter
  * Exclude nodes
  * Exclude virtual machines
* Grouping
  * Include groups (VMs that are rebalanced to nodes together)
  * Exclude groups (VMs that must run on different nodes)
  * Ignore groups (VMs that should be untouched)
* Dry-run support
  * Human readable output in CLI
  * JSON output for further parsing
* Migrate VM workloads away (e.g. maintenance preparation)
* Fully based on Proxmox API
* Usage
  * One-Shot (one-shot)
  * Periodically (daemon)
  * Proxmox Web GUI Integration (optional)

## How does it work?
ProxLB is a load-balancing system designed to optimize the distribution of virtual machines (VMs) and containers (CTs) across a cluster. It works by first gathering resource usage metrics from all nodes in the cluster through the Proxmox API. This includes detailed resource metrics for each VM and CT on every node. ProxLB then evaluates the difference between the maximum and minimum resource usage of the nodes, referred to as "Balanciness." If this difference exceeds a predefined threshold (which is configurable), the system initiates the rebalancing process.

Before starting any migrations, ProxLB validates that rebalancing actions are necessary and beneficial. Depending on the selected balancing mode — such as CPU, memory, or disk — it creates a balancing matrix. This matrix sorts the VMs by their maximum used or assigned resources, identifying the VM with the highest usage. ProxLB then places this VM on the node with the most free resources in the selected balancing type. This process runs recursively until the operator-defined Balanciness is achieved. Balancing can be defined for the used or max. assigned resources of VMs/CTs.

## Usage
Running PLB is easy and it runs almost everywhere since it just depends on `Python3` and the `proxmoxer` library. Therefore, it can directly run on a Proxmox node, dedicated systems like Debian, RedHat, or even FreeBSD, as long as the API is reachable by the client running PLB.

### Dependencies
* Python3
* proxmoxer (Python module)

### Options
The following options can be set in the `proxlb.conf` file:

| Section | Option | Example | Description |
|------|:------:|:------:|:------:|
| `proxmox` | api_host | hypervisor01.gyptazy.com | Host or IP address (or comma separated list) of the remote Proxmox API. |
| | api_user | root@pam | Username for the API. |
| | api_pass | FooBar | Password for the API. |
| | verify_ssl | 1 | Validate SSL certificates (1) or ignore (0). (default: 1, type: bool) |
| | timeout | 10 | Timeout for the Proxmox API in sec. (default: 10) |
| `vm_balancing` | enable | 1 | Enables VM/CT balancing. |
| | method | memory | Defines the balancing method (default: memory) where you can use `memory`, `disk` or `cpu`. |
| | mode | used | Rebalance by `used` resources (efficiency) or `assigned` (avoid overprovisioning) resources. (default: used)|
| | mode_option | byte | Rebalance by node's resources in `bytes` or `percent`. (default: bytes) |
| | type | vm | Rebalance only `vm` (virtual machines), `ct` (containers) or `all` (virtual machines & containers). (default: vm)|
| | balanciness | 10 | Value of the percentage of lowest and highest resource consumption on nodes may differ before rebalancing. (default: 10) |
| | parallel_migrations | 1 | Defines if migrations should be done parallely or sequentially. (default: 1, type: bool) |
| | maintenance_nodes | dummynode03,dummynode04 | Defines a comma separated list of nodes to set them into maintenance mode and move VMs/CTs to other nodes. |
| | ignore_nodes | dummynode01,dummynode02,test* | Defines a comma separated list of nodes to exclude. |
| | ignore_vms | testvm01,testvm02 | Defines a comma separated list of VMs to exclude. (`*` as suffix wildcard or tags are also supported) |
| `storage_balancing` | enable | 0 | Enables storage balancing. |
| | balanciness | 10 | Value of the percentage of lowest and highest storage consumption may differ before rebalancing. (default: 10) |
| | parallel_migrations | 1 | Defines if migrations should be done parallely or sequentially. (default: 1, type: bool) |
| `update_service` | enable | 0 | Enables the automated update service (rolling updates). (default: 0, type: bool) |
| `api` | enable | 0 | Enables the ProxLB API. |
| `service`| daemon | 1 | Run as a daemon (1) or one-shot (0). (default: 1, type: bool) |
| | schedule | 24 | Hours to rebalance in hours. (default: 24) |
| | master_only | 0 | Defines is this should only be performed (1) on the cluster master node or not (0). (default: 0, type: bool) |
| | log_verbosity | INFO | Defines the log level (default: CRITICAL) where you can use `INFO` or `CRITICAL` |
| | config_version | 3 | Defines the current config version schema for ProxLB |

An example of the configuration file looks like:
```
[proxmox]
api_host: hypervisor01.gyptazy.com
api_user: root@pam
api_pass: FooBar
verify_ssl: 1
timeout: 10
[vm_balancing]
enable: 1
method: memory
mode: used
type: vm
# Balanciness defines how much difference may be
# between the lowest & highest resource consumption
# of nodes before rebalancing will be done.
# Examples:
# Rebalancing:     node01: 41% memory consumption :: node02: 52% consumption
# No rebalancing:  node01: 43% memory consumption :: node02: 50% consumption
balanciness: 10
# Enable parallel migrations. If set to 0 it will wait for completed migrations
# before starting next migration.
parallel_migrations: 1
maintenance_nodes: dummynode03,dummynode04
ignore_nodes: dummynode01,dummynode02
ignore_vms: testvm01,testvm02
[storage_balancing]
enable: 0
[update_service]
enable: 0
[api]
enable: 0
[service]
# The master_only option might be useful if running ProxLB on all nodes in a cluster
# but only a single one should do the balancing. The master node is obtained from the Proxmox
# HA status.
master_only: 0
daemon: 1
config_version: 3
```

#### Notes
* If running ProxLB on more than one Proxmox node you can set `api_host` to a comma-separated list of each node's IP address or hostname. (Example: `api_host: node01.gyptazy.com,node02.gyptazy.com,node03.gyptazy.com`)
* The `verify_ssl` parameter can switch between the mode to verify trusted remote certificates. Keep in mind, that even local ones are **not** trusted by default and need to be imported to the truststore.
* Even when using only the `vm_balancing` mode, ensure to have the other sections listed in your config:
```
[storage_balancing]
enable: 0
[update_service]
enable: 0
[api]
enable: 0
```

### Parameters
The following options and parameters are currently supported:

| Option | Long Option | Description | Default |
|------|:------:|------:|------:|
| -c | --config | Path to a config file. | /etc/proxlb/proxlb.conf (default) |
| -d | --dry-run | Performs a dry-run without doing any actions. | Unset |
| -j | --json | Returns a JSON of the VM movement. | Unset |
| -b | --best-node | Returns the best next node for a VM/CT placement (useful for further usage with Terraform/Ansible). | Unset |
| -m | --maintenance | Sets node(s) to maintenance mode & moves workloads away. | Unset |
| -v | --version | Returns the ProxLB version on stdout. | Unset |

### Balancing
#### General
In general, virtual machines (VMs), containers (CTs) can be rebalanced and moved around nodes or shared storage (storage balancing) in the cluster. Often, this also works without downtime without any further downtimes. However, this does **not** work with containers. LXC based containers will be shutdown, copied and started on the new node. Also to note, live migrations can work fluently without any issues but there are still several things to be considered. This is out of scope for ProxLB and applies in general to Proxmox and your cluster setup. You can find more details about this here: https://pve.proxmox.com/wiki/Migrate_to_Proxmox_VE.

#### By Used Memory of VMs/CTs
By continuously monitoring the current resource usage of VMs, ProxLB intelligently reallocates workloads to prevent any single node from becoming overloaded. This approach ensures that resources are balanced efficiently, providing consistent and optimal performance across the entire cluster at all times. To activate this balancing mode, simply activate the following option in your ProxLB configuration:
```
mode: used
```

Afterwards, restart the service (if running in daemon mode) to activate this rebalancing mode.

#### By Assigned Memory of VMs/CTs
By ensuring that resources are always available for each VM, ProxLB prevents over-provisioning and maintains a balanced load across all nodes. This guarantees that users have consistent access to the resources they need. However, if the total assigned resources exceed the combined capacity of the cluster, ProxLB will issue a warning, indicating potential over-provisioning despite its best efforts to balance the load.  To activate this balancing mode, simply activate the following option in your ProxLB configuration:
```
mode: assigned
```

Afterwards, restart the service (if running in daemon mode) to activate this rebalancing mode.

#### Storage Balancing
Starting with ProxLB 1.0.3, ProxLB also supports the balancing of underlying shared storage. In this case, all attached disks (`rootfs` in a context of a CT) of a VM or CT are being fetched and evaluated. If a VM has multiple disks attached, the disks can also be distributed over different storages. As a result, only shared storage is supported. Non shared storage would require to move the whole VM including all attached disks to the parent's node local storage.

Limitations:
* Only shared storage
* Only supported for the following VM disk types:
    * ide (only disks, not CD)
    * nvme
    * scsi
    * virtio
    * sata
    * rootfs (Container)

*Note: Storage balancing is currently in beta and should be used carefully.*

### Affinity Rules / Grouping Relationships
#### Affinity (Stay Together)
<img align="left" src="https://cdn.gyptazy.com/images/plb-rebalancing-include-balance-group.jpg"/> Access the Proxmox Web UI by opening your web browser and navigating to your Proxmox VE web interface, then log in with your credentials. Navigate to the VM you want to tag by selecting it from the left-hand navigation panel. Click on the "Options" tab to view the VM's options, then select "Edit" or "Add" (depending on whether you are editing an existing tag or adding a new one). In the tag field, enter plb_include_ followed by your unique identifier, for example, plb_include_group1. Save the changes to apply the tag to the VM. Repeat these steps for each VM that should be included in the group.

#### Anti-Affinity (Keep Apart)
<img align="left" src="https://cdn.gyptazy.com/images/plb-rebalancing-exclude-balance-group.jpg"/> Access the Proxmox Web UI by opening your web browser and navigating to your Proxmox VE web interface, then log in with your credentials. Navigate to the VM you want to tag by selecting it from the left-hand navigation panel. Click on the "Options" tab to view the VM's options, then select "Edit" or "Add" (depending on whether you are editing an existing tag or adding a new one). In the tag field, enter plb_exclude_ followed by your unique identifier, for example, plb_exclude_critical. Save the changes to apply the tag to the VM. Repeat these steps for each VM that should be excluded from being on the same node.

#### Ignore VMs (Tag Style)
<img align="left" src="https://cdn.gyptazy.com/images/plb-rebalancing-ignore-vm.jpg"/>  In Proxmox, you can ensure that certain VMs are ignored during the rebalancing process by setting a specific tag within the Proxmox Web UI, rather than solely relying on configurations in the ProxLB config file. This can be achieved by adding the tag 'plb_ignore_vm' to the VM. Once this tag is applied, the VM will be excluded from any further rebalancing operations, simplifying the management process.

### Systemd
When installing a Linux distribution (such as .deb or .rpm) file, this will be shipped with a systemd unit file. The default configuration file will be sourced from `/etc/proxlb/proxlb.conf`.

| Unit Name | Options |
|------|:------:|
| proxlb | start, stop, status, restart |

### Manual
A manual installation is possible and also supports BSD based systems. Proxmox Rebalancing Service relies on mainly two important files:
* proxlb (Python Executable)
* proxlb.conf (Config file)

The executable must be able to read the config file, if no dedicated config file is given by the `-c` argument, PLB tries to read it from `/etc/proxlb/proxlb.conf`.

### Proxmox GUI Integration
<img align="left" src="https://cdn.gyptazy.com/images/proxlb-GUI-integration.jpg"/> PLB can also be directly be used from the Proxmox Web UI by installing the optional package `pve-proxmoxlb-service-ui` package which has a dependency on the `proxlb` package. For the Web UI integration, it requires to be installed (in addition) on the nodes on the cluster. Afterwards, a new menu item is present in the HA chapter called `Rebalancing`. This chapter provides two possibilities:
* Rebalancing VM workloads
* Migrate VM workloads away from a defined node (e.g. maintenance preparation)

### Quick Start
The easiest way to get started is by using the ready-to-use packages that I provide on my CDN and to run it on a Linux Debian based system. This can also be one of the Proxmox nodes itself.

```
wget https://cdn.gyptazy.com/files/os/debian/proxlb/proxlb_1.0.4_amd64.deb
dpkg -i proxlb_1.0.4_amd64.deb
# Adjust your config
vi /etc/proxlb/proxlb.conf
systemctl restart proxlb
systemctl status proxlb
```

### Container Quick Start (Docker/Podman)
Creating a container image of ProxLB is straightforward using the provided Dockerfile. The Dockerfile simplifies the process by automating the setup and configuration required to get ProxLB running in a container. Simply follow the steps in the Dockerfile to build the image, ensuring all dependencies and configurations are correctly applied. For those looking for an even quicker setup, a ready-to-use ProxLB container image is also available, eliminating the need for manual building and allowing for immediate deployment.

```bash
git clone https://github.com/gyptazy/ProxLB.git
cd ProxLB
docker build -t proxlb .
```

Afterwards simply adjust the config file to your needs:
```
vi /etc/proxlb/proxlb.conf
```

Finally, start the created container.
```bash
docker run -it --rm -v $(pwd)/proxlb.conf:/etc/proxlb/proxlb.conf proxlb
```

### Logging
ProxLB uses the `SystemdHandler` for logging. You can find all your logs in your systemd unit log or in the `journalctl`. In default, ProxLB only logs critical events. However, for further understanding of the balancing it might be useful to change this to `INFO` or `DEBUG` which can simply be done in the [proxlb.conf](https://github.com/gyptazy/ProxLB/blob/main/proxlb.conf#L14) file by changing the `log_verbosity` parameter.

Available logging values:
| Verbosity | Description |
|------|:------:|
| DEBUG | This option logs everything and is needed for debugging the code. |
| INFO | This option provides insides behind the scenes. What/why has been something done and with which values. |
| WARNING | This option provides only warning messages, which might be a problem in general but not for the application itself. |
| CRITICAL | This option logs all critical events that will avoid running ProxLB. |

## Motivation
As a developer managing a cluster of virtual machines for my projects, I often encountered the challenge of resource imbalance. Nodes within the cluster would become unevenly loaded, with some nodes being overburdened while others remained underutilized. This imbalance led to inefficiencies, performance bottlenecks, and increased operational costs. Frustrated by the lack of an adequate solution to address this issue, I decided to develop the ProxLB (PLB) to ensure better resource distribution across my clusters.

My primary motivation for creating PLB stemmed from my work on my BoxyBSD project, where I consistently faced the difficulty of maintaining balanced nodes while running various VM workloads but also on my personal clusters. The absence of an efficient rebalancing mechanism made it challenging to achieve optimal performance and stability. Recognizing the necessity for a tool that could gather and analyze resource metrics from both the cluster nodes and the running VMs, I embarked on developing ProxLB.

PLB meticulously collects detailed resource usage data from each node in a Proxmox cluster, including CPU load, memory usage, and local disk space utilization. It also gathers comprehensive statistics from all running VMs, providing a granular understanding of the workload distribution. With this data, PLB intelligently redistributes VMs based on memory usage, local disk usage, and CPU usage. This ensures that no single node is overburdened, storage resources are evenly distributed, and the computational load is balanced, enhancing overall cluster performance.

As an advocate of the open-source philosophy, I believe in the power of community and collaboration. By sharing solutions like PLB, I aim to contribute to the collective knowledge and tools available to developers facing similar challenges. Open source fosters innovation, transparency, and mutual support, enabling developers to build on each other's work and create better solutions together.

Developing PLB was driven by a desire to solve a real problem I faced in my projects. However, the spirit behind this effort was to provide a valuable resource to the community. By open-sourcing PLB, I hope to help other developers manage their clusters more efficiently, optimize their resource usage, and reduce operational costs. Sharing this solution aligns with the core principles of open source, where the goal is not only to solve individual problems but also to contribute to the broader ecosystem.

## References
Here you can find some overviews of references for and about the ProxLB (PLB):

| Description | Link |
|------|:------:|
| General introduction into ProxLB | https://gyptazy.com/blog/proxlb-rebalancing-vm-workloads-across-nodes-in-proxmox-clusters/ |
| Howto install and use ProxLB on Debian to rebalance vm workloads in a Proxmox cluster | https://gyptazy.com/howtos/howto-install-and-use-proxlb-to-rebalance-vm-workloads-across-nodes-in-proxmox-clusters/ |

## Downloads
ProxLB can be obtained in man different ways, depending on which use case you prefer. You can use simply copy the code from GitHub, use created packages for Debian or RedHat based systems, use a Repository to keep ProxLB always up to date or simply use a Container image for Docker/Podman.

### Packages
Ready to use packages can be found at:
* https://cdn.gyptazy.com/files/os/debian/proxlb/
* https://cdn.gyptazy.com/files/os/ubuntu/proxlb/
* https://cdn.gyptazy.com/files/os/redhat/proxlb/

### Repository
Debian based systems can also use the repository by adding the following line to their apt sources:

#### Stable Releases
```
deb https://repo.gyptazy.com/stable /
```

#### Beta/Testing Releases
```
deb https://repo.gyptazy.com/testing /
```

The Repository's GPG key can be found at: `https://repo.gyptazy.com/repository.gpg`

You can also simply import it by running:

```
# KeyID:  17169F23F9F71A14AD49EDADDB51D3EB01824F4C
# UID:    gyptazy Solutions Repository <contact@gyptazy.com>
# SHA256: 52c267e6f4ec799d40cdbdb29fa518533ac7942dab557fa4c217a76f90d6b0f3  repository.gpg

wget -O /etc/apt/trusted.gpg.d/proxlb.asc https://repo.gyptazy.com/repository.gpg
```

*Note: The defined repositories `repo.gyptazy.com` and `repo.proxlb.de` are the same!*

### Container Images (Docker/Podman)
Container Images for Podman, Docker etc., can be found at:
| Version | Image |
|------|:------:|
| latest | cr.gyptazy.com/proxlb/proxlb:latest |
| v1.0.4 | cr.gyptazy.com/proxlb/proxlb:v1.0.4 |
| v1.0.3 | cr.gyptazy.com/proxlb/proxlb:v1.0.3 |
| v1.0.2 | cr.gyptazy.com/proxlb/proxlb:v1.0.2 |
| v1.0.0 | cr.gyptazy.com/proxlb/proxlb:v1.0.0 |
| v0.9.9 | cr.gyptazy.com/proxlb/proxlb:v0.9.9 |

## Misc
### Bugs
Bugs can be reported via the GitHub issue tracker [here](https://github.com/gyptazy/ProxLB/issues). You may also report bugs via email or deliver PRs to fix them on your own. Therefore, you might also see the contributing chapter.

### Contributing
Feel free to add further documentation, to adjust already existing one or to contribute with code. Please take care about the style guide and naming conventions. You can find more in our [CONTRIBUTING.md](https://github.com/gyptazy/ProxLB/blob/main/CONTRIBUTING.md) file.

### Documentation
You can also find additional and more detailed documentation within the [docs/](https://github.com/gyptazy/ProxLB/tree/main/docs) directory.

### Support
If you need assistance or have any questions, we offer support through our dedicated [chat room](https://matrix.to/#/#proxlb:gyptazy.com) in Matrix and on Reddit. Join our community for real-time help, advice, and discussions. Connect with us in our dedicated chat room for immediate support and live interaction with other users and developers. You can also visit our [GitHub Community](https://github.com/gyptazy/ProxLB/discussions/) to post your queries, share your experiences, and get support from fellow community members and moderators. You may also just open directly an issue [here](https://github.com/gyptazy/ProxLB/issues) on GitHub. We are here to help and ensure you have the best experience possible.

| Support Channel | Link |
|------|:------:|
| Matrix | [#proxlb:gyptazy.com](https://matrix.to/#/#proxlb:gyptazy.com) |
| GitHub Community | [GitHub Community](https://github.com/gyptazy/ProxLB/discussions/)
| GitHub | [ProxLB GitHub](https://github.com/gyptazy/ProxLB/issues) |

### Author(s)
 * Florian Paul Azim Hoberg @gyptazy (https://gyptazy.com)
