# Use the official Python 3.12 image
FROM python:3.12

# Labels
LABEL maintainer="gyptazy@gyptazy.ch"
LABEL org.label-schema.schema-version="0.9"
LABEL org.label-schema.description="ProxLB - Rebalance VM workloads across nodes in a Proxmox cluster."
LABEL org.label-schema.url="https://github.com/gyptazy/ProxLB"

# Create a directory for the app
WORKDIR /app

# Copy the python program from the current directory to /app
COPY proxlb /app/proxlb

# Copy requirements to the container
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

# Set the entry point to use the virtual environment's python
ENTRYPOINT ["python3", "/app/proxlb"]
