# Use the latest Alpine image
FROM alpine:latest

# Labels
LABEL maintainer="gyptazy@gyptazy.com"
LABEL org.label-schema.name="ProxLB"
LABEL org.label-schema.description="ProxLB - An advanced load balancer for Proxmox clusters."
LABEL org.label-schema.vendor="gyptazy"
LABEL org.label-schema.url="https://proxlb.de"
LABEL org.label-schema.vcs-url="https://github.com/gyptazy/ProxLB"

# Install Python3
RUN apk add --no-cache python3 py3-pip

# Create a directory for the app
WORKDIR /app

# Copy the python program from the current directory to /app
COPY proxlb /app/proxlb

# Copy requirements to the container
COPY requirements.txt /app/requirements.txt

# Install dependencies in the virtual environment
RUN pip install --break-system-packages -r /app/requirements.txt

# Set the entry point to use the virtual environment's python
ENTRYPOINT ["/bin/python3", "/app/proxlb/main.py"]
