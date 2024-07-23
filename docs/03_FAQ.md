## FAQ

### Could not import all dependencies
ProxLB requires the Python library `proxmoxer`. This can simply be installed by the most
system repositories. If you encounter this error message you simply need to install it.


```
# systemctl status proxlb
x proxlb.service - Proxmox Rebalancing Service
     Loaded: loaded (/etc/systemd/system/proxlb.service; static)
     Active: failed (Result: exit-code) since Sat 2024-07-06 10:25:16 UTC; 1s ago
   Duration: 239ms
    Process: 7285 ExecStart=/usr/bin/proxlb -c /etc/proxlb/proxlb.conf (code=exited, status=2)
   Main PID: 7285 (code=exited, status=2)
        CPU: 129ms

Jul 06 10:25:16 build01 systemd[1]: Started proxlb.service - ProxLB.
Jul 06 10:25:16 build01 proxlb[7285]:  proxlb: Error: [python-imports]: Could not import all dependencies. Please install "proxmoxer".
```

Debian/Ubuntu: apt-get install python3-proxmoxer
If the package is not provided by your systems repository, you can also install it by running `pip3 install proxmoxer`.

### How does it work?
ProxLB is a load-balancing system designed to optimize the distribution of virtual machines (VMs) and containers (CTs) across a cluster. It works by first gathering resource usage metrics from all nodes in the cluster through the Proxmox API. This includes detailed resource metrics for each VM and CT on every node. ProxLB then evaluates the difference between the maximum and minimum resource usage of the nodes, referred to as "Balanciness." If this difference exceeds a predefined threshold (which is configurable), the system initiates the rebalancing process.

Before starting any migrations, ProxLB validates that rebalancing actions are necessary and beneficial. Depending on the selected balancing mode — such as CPU, memory, or disk — it creates a balancing matrix. This matrix sorts the VMs by their maximum used or assigned resources, identifying the VM with the highest usage. ProxLB then places this VM on the node with the most free resources in the selected balancing type. This process runs recursively until the operator-defined Balanciness is achieved. Balancing can be defined for the used or max. assigned resources of VMs/CTs.

### Logging
ProxLB uses the `SystemdHandler` for logging. You can find all your logs in your systemd unit log or in the `journalctl`. In default, ProxLB only logs critical events. However, for further understanding of the balancing it might be useful to change this to `INFO` or `DEBUG` which can simply be done in the [proxlb.conf](https://github.com/gyptazy/ProxLB/blob/main/proxlb.conf#L14) file by changing the `log_verbosity` parameter.

Available logging values:
| Verbosity | Description |
|------|:------:|
| DEBUG | This option logs everything and is needed for debugging the code. |
| INFO | This option provides insides behind the scenes. What/why has been something done and with which values. |
| WARNING | This option provides only warning messages, which might be a problem in general but not for the application itself. |
| CRITICAL | This option logs all critical events that will avoid running ProxLB. |

### Motivation
As a developer managing a cluster of virtual machines for my projects, I often encountered the challenge of resource imbalance. Nodes within the cluster would become unevenly loaded, with some nodes being overburdened while others remained underutilized. This imbalance led to inefficiencies, performance bottlenecks, and increased operational costs. Frustrated by the lack of an adequate solution to address this issue, I decided to develop the ProxLB (PLB) to ensure better resource distribution across my clusters.

My primary motivation for creating PLB stemmed from my work on my BoxyBSD project, where I consistently faced the difficulty of maintaining balanced nodes while running various VM workloads but also on my personal clusters. The absence of an efficient rebalancing mechanism made it challenging to achieve optimal performance and stability. Recognizing the necessity for a tool that could gather and analyze resource metrics from both the cluster nodes and the running VMs, I embarked on developing ProxLB.

PLB meticulously collects detailed resource usage data from each node in a Proxmox cluster, including CPU load, memory usage, and local disk space utilization. It also gathers comprehensive statistics from all running VMs, providing a granular understanding of the workload distribution. With this data, PLB intelligently redistributes VMs based on memory usage, local disk usage, and CPU usage. This ensures that no single node is overburdened, storage resources are evenly distributed, and the computational load is balanced, enhancing overall cluster performance.

As an advocate of the open-source philosophy, I believe in the power of community and collaboration. By sharing solutions like PLB, I aim to contribute to the collective knowledge and tools available to developers facing similar challenges. Open source fosters innovation, transparency, and mutual support, enabling developers to build on each other's work and create better solutions together.

Developing PLB was driven by a desire to solve a real problem I faced in my projects. However, the spirit behind this effort was to provide a valuable resource to the community. By open-sourcing PLB, I hope to help other developers manage their clusters more efficiently, optimize their resource usage, and reduce operational costs. Sharing this solution aligns with the core principles of open source, where the goal is not only to solve individual problems but also to contribute to the broader ecosystem.

### Packages / Container Images
Ready to use packages can be found at:
* https://cdn.gyptazy.ch/files/amd64/debian/proxlb/
* https://cdn.gyptazy.ch/files/amd64/ubuntu/proxlb/
* https://cdn.gyptazy.ch/files/amd64/redhat/proxlb/
* https://cdn.gyptazy.ch/files/amd64/freebsd/proxlb/

Container Images for Podman, Docker etc., can be found at:
| Version | Image |
|------|:------:|
| latest | cr.gyptazy.ch/proxlb/proxlb:latest |

### Bugs
Bugs can be reported via the GitHub issue tracker [here](https://github.com/gyptazy/ProxLB/issues). You may also report bugs via email or deliver PRs to fix them on your own. Therefore, you might also see the contributing chapter.

### Contributing
Feel free to add further documentation, to adjust already existing one or to contribute with code. Please take care about the style guide and naming conventions. You can find more in our [CONTRIBUTING.md](https://github.com/gyptazy/ProxLB/blob/main/CONTRIBUTING.md) file.

### Support
If you need assistance or have any questions, we offer support through our dedicated [chat room](https://matrix.to/#/#proxlb:gyptazy.ch) in Matrix and on Reddit. Join our community for real-time help, advice, and discussions. Connect with us in our dedicated chat room for immediate support and live interaction with other users and developers. You can also visit our [Reddit community](https://www.reddit.com/r/Proxmox/comments/1e78ap3/introducing_proxlb_rebalance_your_vm_workloads/) to post your queries, share your experiences, and get support from fellow community members and moderators. You may also just open directly an issue [here](https://github.com/gyptazy/ProxLB/issues) on GitHub. We are here to help and ensure you have the best experience possible.

| Support Channel | Link |
|------|:------:|
| Matrix | [#proxlb:gyptazy.ch](https://matrix.to/#/#proxlb:gyptazy.ch) |
| Reddit | [Reddit community](https://www.reddit.com/r/Proxmox/comments/1e78ap3/introducing_proxlb_rebalance_your_vm_workloads/)  |
| GitHub | [ProxLB GitHub](https://github.com/gyptazy/ProxLB/issues) |