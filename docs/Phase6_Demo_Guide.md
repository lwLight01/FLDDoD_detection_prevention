# Phase 6: SDN Mitigation Demo Guide

This guide contains the exact steps to demonstrate the Software Defined Network (SDN) and Mitigation REST API on your Kali Linux VM.

## 🟢 1. Environment Setup
Open your Kali Linux VM and open **three separate terminal tabs**.

In **Terminal 1**, start the background networking service and activate your Python environment:
```bash
sudo service openvswitch-switch start
source ~/ryu_venv/bin/activate
cd ~/FLDDoD_detection_prevention
```

## 🧠 2. Start the Controller (The Brain)
In **Terminal 1**, launch the Ryu SDN controller:
```bash
PYTHONPATH=src ryu-manager --verbose src/sdn_controller/ryu_app.py --wsapi-port 8080
```
*(Leave this running. This terminal will show the real-time flow extraction logs!)*

## 🌐 3. Start the Network Simulation
In **Terminal 2**, spin up your Mininet virtual infrastructure:
```bash
cd ~/FLDDoD_detection_prevention
sudo python3 src/sdn_controller/mininet_topo.py
```

## ✅ 4. Prove Initial Connectivity
At the `mininet>` prompt in Terminal 2, prove to your teacher that the network is healthy:
```bash
pingall
```
*(You should see `0% dropped` - all hosts can communicate).*

## 💥 5. Launch the DDoS Attack
At the `mininet>` prompt, simulate the hacker (`h4`) launching a massive SYN Flood against the server (`h1`) in the background:
```bash
h4 hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source 10.0.0.1 &
```
*(Point out to your teacher that Terminal 1 is now rapidly extracting these malicious flows!)*

## 🛡️ 6. Trigger the Mitigation API
In **Terminal 3**, act as the ML Engine and send a REST API command to block the attacker:
```bash
curl -X POST http://localhost:8080/api/v1/mitigate \
     -H "Content-Type: application/json" \
     -d '{"src_ip": "10.0.0.4", "action": "drop"}'
```

## 🎯 7. Prove the Mitigation Worked!
Go back to the `mininet>` prompt in **Terminal 2** and run pingall again:
```bash
pingall
```
*(Show your teacher the results! `h1`, `h2`, and `h3` can still communicate, but `h4` will show `X X X` - it has been 100% blocked by the switch!)*

## 🧹 8. Clean Up
When the presentation is over, gracefully shut down the network to prevent errors on your next run:
1. In Terminal 2 (Mininet), type: `quit`
2. Then type: `sudo mn -c`
3. In Terminal 1 (Ryu), press: `Ctrl + C`
