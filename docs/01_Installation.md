# Installation

## Packages
The easiest way to get started is by using the ready-to-use packages that I provide on my CDN and to run it on a Linux Debian based system. This can also be one of the Proxmox nodes itself.

```
wget https://cdn.gyptazy.ch/files/amd64/debian/proxlb/proxlb_0.9.9_amd64.deb
dpkg -i proxlb_0.9.9_amd64.deb
# Adjust your config
vi /etc/proxlb/proxlb.conf
systemctl restart proxlb
systemctl status proxlb
```

## Container (Docker/Podman)
Creating a container image of ProxLB is straightforward using the provided Dockerfile. The Dockerfile simplifies the process by automating the setup and configuration required to get ProxLB running in a container. Simply follow the steps in the Dockerfile to build the image, ensuring all dependencies and configurations are correctly applied. For those looking for an even quicker setup, a ready-to-use ProxLB container image is also available, eliminating the need for manual building and allowing for immediate deployment.

```bash
git clone https://github.com/gyptazy/ProxLB.git
cd ProxLB
build -t proxlb .
```

Afterwards simply adjust the config file to your needs:
```
vi /etc/proxlb/proxlb.conf
```

Finally, start the created container.
```bash
docker run -it --rm -v $(pwd)/proxlb.conf:/etc/proxlb/proxlb.conf proxlb
```