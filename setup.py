from setuptools import setup

setup(
    name="proxlb",
    version="1.1.0",
    description="A DRS alike loadbalancer for Proxmox clusters.",
    long_description="An advanced DRS alike loadbalancer for Proxmox clusters that also supports maintenance modes and affinity/anti-affinity rules.",
    author="Florian Paul Azim Hoberg (gyptazy)",
    author_email="gyptazy@gyptazy.com",
    packages=["proxlb", "proxlb.utils", "proxlb.models"],
    install_requires=[
        "requests",
        "urllib3",
        "proxmoxer",
        "yaml",
    ],
)
