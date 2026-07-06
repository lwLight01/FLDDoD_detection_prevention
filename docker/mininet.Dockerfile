FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies including mininet, openvswitch, and python3
RUN apt-get update && apt-get install -y \
    mininet \
    openvswitch-switch \
    openvswitch-common \
    python3 \
    python3-pip \
    iproute2 \
    iputils-ping \
    net-tools \
    iperf \
    hping3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ryu controller
RUN pip3 install ryu webob

# Start OpenVSwitch service before running any mininet topology
# OVS needs to be running in the container for Mininet to create switches.
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app
COPY src/sdn_controller /app/sdn_controller
COPY scripts /app/scripts

# Run our custom entrypoint which starts OVS then executes CMD
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
