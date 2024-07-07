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
