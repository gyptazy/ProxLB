# Use the latest Alpine image
FROM alpine:latest

# Labels
LABEL maintainer="gyptazy@gyptazy.com"
LABEL org.label-schema.name="ProxLB"
LABEL org.label-schema.description="ProxLB - An advanced load balancer for Proxmox clusters."
LABEL org.label-schema.vendor="gyptazy"
LABEL org.label-schema.url="https://proxlb.de"
LABEL org.label-schema.vcs-url="https://github.com/gyptazy/ProxLB"

# --- Step 1 (root): system deps, user, dirs ---
RUN apk add --no-cache python3 py3-pip \
  && addgroup -S plb \
  && adduser -S -G plb -h /home/plb plb \
  && mkdir -p /app/conf /opt/venv \
  && chown -R plb:plb /app /home/plb /opt/venv

WORKDIR /app

# Copy only requirements first for better layer caching
COPY --chown=plb:plb requirements.txt /app/requirements.txt

# --- Step 2 (appuser): venv + deps + code ---
USER plb

# Create venv owned by appuser and put it on PATH
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install Python dependencies into the venv (no PEP 668 issues)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (owned by appuser)
COPY --chown=plb:plb proxlb /app/proxlb

# Optional: placeholder config so a bind-mount can override cleanly
RUN touch /app/conf/proxlb.yaml

# Run as non-root using venv Python
ENTRYPOINT ["/opt/venv/bin/python", "/app/proxlb/main.py"]
