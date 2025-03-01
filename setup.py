from setuptools import setup

setup(
    name="python3-proxlb",
    version="1.1.0",
    description="My Python Package",
    long_description="My Python Package",
    author="Florian Paul Azim Hoberg (gyptazy)",
    author_email="gyptazy@gyptazy.com",
    packages=["python3-proxlb"],
    install_requires=[
        "requests",
        "urllib3",
        "proxmoxer",
        "yaml",
    ],
)
