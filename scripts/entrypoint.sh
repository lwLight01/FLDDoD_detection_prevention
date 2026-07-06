#!/bin/bash
# Start OpenVSwitch
service openvswitch-switch start
# Execute the passed command
exec "$@"
