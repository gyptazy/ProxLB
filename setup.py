from setuptools import setup

setup(
    name="proxlb",
    version="1.1.11",
    description="An advanced resource scheduler and load balancer for Proxmox clusters.",
    long_description="An advanced resource scheduler and load balancer for Proxmox clusters that also supports maintenance modes and affinity/anti-affinity rules.",
    author="Florian Paul Azim Hoberg",
    author_email="gyptazy@gyptazy.com",
    maintainer="Florian Paul Azim Hoberg",
    maintainer_email="gyptazy@gyptazy.com",
    url="https://github.com/gyptazy/ProxLB",
    packages=["proxlb", "proxlb.utils", "proxlb.models"],
    install_requires=[
        "requests",
        "urllib3",
        "proxmoxer",
        "pyyaml",
    ],
        data_files=[('/etc/systemd/system', ['service/proxlb.service']), ('/etc/proxlb/', ['config/proxlb_example.yaml'])],
)
