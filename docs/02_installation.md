# Table of Contents

- [Installation](#installation)
  - [Requirements / Dependencies](#requirements--dependencies)
  - [Debian Package](#debian-package)
    - [Quick-Start](#quick-start)
    - [Details](#details)
    - [Debian Packages (.deb files)](#debian-packages-deb-files)
    - [Repo Mirror and Proxmox Offline Mirror Support](#repo-mirror-and-proxmox-offline-mirror-support)
  - [RedHat Package](#redhat-package)
  - [Container Images / Docker](#container-images--docker)
    - [Overview of Images](#overview-of-images)
  - [Source](#source)
    - [Traditional System](#traditional-system)
    - [Container Image](#container-image)
- [Upgrading](#upgrading)
  - [Upgrading from < 1.1.0](#upgrading-from--110)
  - [Upgrading from >= 1.1.0](#upgrading-from--110)


## Installation
### Requirements / Dependencies
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
* https://cdn.gyptazy.com/files/os/debian/proxlb/

Afterwards, you can simply install the package by running:
```bash
dpkg -i proxlb_*.deb
cp /etc/proxlb/proxlb_example.yaml /etc/proxlb/proxlb.yaml
# Adjust the config to your needs
vi /etc/proxlb/proxlb.yaml
systemctl start proxlb
```

#### Repo Mirror and Proxmox Offline Mirror Support
ProxLB uses the supported flat mirror style for the Debian repository. Unfortunately, not all offline-mirror applications support it. One of the known ones is the official *proxmox-offline-mirror* which is unable to handle flat repositories (see also: [#385](https://github.com/gyptazy/ProxLB/issues/385)).

Therefore, we currently operate and support both ways to avoid everyone force switching to the new repository. As a result, you can simply use this repository:
```
deb https://repo.gyptazy.com/proxlb stable main
```

**Example Config for proxmox-offline-mirror:**

An example config for the proxmox-offline-mirror would look like:
```
mirror: proxlb
    architectures amd64
    base-dir /var/lib/proxmox-offline-mirror/mirrors/
    key-path /etc/apt/trusted.gpg.d/proxlb.asc
    repository deb https://repo.gyptazy.com/proxlb stable main
    sync true
    verify true
```

### RedHat Package
There's currently no official support for RedHat based systems. However, there's a dummy .rpm package for such systems in the pipeline which can be found here:
* https://github.com/gyptazy/ProxLB/actions/workflows/20-pipeline-build-rpm-package.yml


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

*Note: ProxLB container images are officially only available at cr.proxlb.de and cr.gyptazy.com.* 

#### Overview of Images
| Version | Image |
|------|:------:|
| latest | cr.gyptazy.com/proxlb/proxlb:latest |
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

## Upgrading
### Upgrading from < 1.1.0
Upgrading ProxLB is not supported due to a fundamental redesign introduced in version 1.1.x. With this update, ProxLB transitioned from a monolithic application to a pure Python-style project, embracing a more modular and flexible architecture. This shift aimed to improve maintainability and extensibility while keeping up with modern development practices. Additionally, ProxLB moved away from traditional ini-style configuration files and adopted YAML for configuration management. This change simplifies configuration handling, reduces the need for extensive validation, and ensures better type casting, ultimately providing a more streamlined and user-friendly experience.

### Upgrading from >= 1.1.0
Uprading within the current stable versions, starting from 1.1.0, will be possible in all supported ways.