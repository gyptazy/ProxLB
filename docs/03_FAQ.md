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

### VM Grouping
<img align="left" src="https://cdn.gyptazy.ch/images/proxlb-vm-grouping-for-rebalancing.jpg"/> In the Proxmox WEB UI, you can group VMs using the notes field. While Proxmox doesn't natively support tagging or flagging VMs, you can utilize the VM's notes/description field for this purpose. You can still include any other notes and comments in the description field, but to enable grouping, you must add a new line starting with `proxlb-grouping:` followed by the group name.

Example:
```
This is a great VM
proxlb-grouping: db-gyptazy01-workload-group01

foo bar With some more text.
Important is only the proxlb-grouping line with a name and
we can still use this field.
```

The notes field is evaluated for each VM. All VMs with the same group name (e.g., `db-gyptazy01-workload-group01`) will be rebalanced together on the same host.