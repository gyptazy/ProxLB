# Use the official Debian 12 base image
FROM debian:12

# Labels
LABEL maintainer="gyptazy@gyptazy.ch"
LABEL org.label-schema.schema-version="0.9"
LABEL org.label-schema.description="ProxLB - Rebalance VM workloads across nodes in a Proxmox cluster."
LABEL org.label-schema.url="https://github.com/gyptazy/ProxLB"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install python3 and python3-venv
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for the app
WORKDIR /app

# Copy the python program from the current directory to /app
COPY proxlb /app/proxlb

# Create a virtual environment
RUN python3 -m venv venv

# Copy requirements to the container
COPY requirements.txt /app/requirements.txt

# Install dependencies in the virtual environment
RUN . venv/bin/activate && pip install -r /app/requirements.txt

# Set the entry point to use the virtual environment's python
ENTRYPOINT ["/app/venv/bin/python3", "/app/proxlb"]
