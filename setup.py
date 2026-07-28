from setuptools import setup

setup(
    name="proxlb",
    version="2.2.0",
    description="An advanced resource scheduler and load balancer for Proxmox clusters.",
    long_description="An advanced resource scheduler and load balancer for Proxmox clusters that also supports maintenance modes and affinity/anti-affinity rules.",
    author="Florian Paul Azim Hoberg",
    author_email="gyptazy@gyptazy.com",
    maintainer="credativ GmbH",
    maintainer_email="support@credativ.de",
    url="https://github.com/credativ/ProxLB",
    packages=["proxlb", "proxlb.utils", "proxlb.models"],
    install_requires=[
        "packaging",
        "proxlb-solver>=0.1.2",
        "proxmoxer",
        "pydantic",
        "pyyaml",
        "requests",
        "urllib3",
    ],
    data_files=[('/etc/systemd/system', ['service/proxlb.service']), ('/etc/proxlb/', ['config/proxlb_example.yaml'])],
)
