#!/bin/bash
# scripts/traffic_gen.sh
# Simulates benign background traffic using iperf or curl

echo "Starting benign traffic generation..."

# h1 to h2 UDP traffic
iperf -c 10.0.0.2 -u -b 1M -t 60 &

# h3 to h1 TCP traffic
iperf -c 10.0.0.1 -t 60 &

echo "Benign traffic running in background for 60 seconds."
