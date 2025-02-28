from setuptools import setup, find_packages

setup(
    name='proxlb',
    version='1.1.0',
    description='A DRS alike loadbalancer for Proxmox clusters.',
    author='Florian Paul Azim Hoberg',
    author_email='gyptazy@gyptazy.com',
    url='https://github.com/gyptazy/ProxLB',
    packages=find_packages(),
    install_requires=[
        'python3-proxmoxer',
        'python3-urllib3',
        'python3-requests',
        'python3-yaml',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GPL v3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
